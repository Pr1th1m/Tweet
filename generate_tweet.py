from datetime import datetime, timezone
import os
import re

from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

from send_email import send_email

load_dotenv()

client = Groq(
    api_key=os.getenv('GROQ_API_KEY')
)

tavilyclient = TavilyClient(
    api_key=os.getenv('TAVILY_API_KEY')
)

X_FREE_CHAR_LIMIT = 280
NEWS_LOOKBACK_DAYS = 1
TOPIC_ORDER = [
    "world news",
    "financial markets",
    "tech revolution in india",
    "india economy & policy",
    "startup & venture capital",
    "ai & emerging technology",
    "cybersecurity",
    "climate & energy",
    "geopolitics & conflicts",
    "business & corporate",
    "festivals & culture",
    "sports business",
]
TOPIC_STATE_FILE = "topic_state.txt"

TOPIC_PROMPTS = {
    "world news": (
        "Fetch only the latest world news from the last 24 hours. "
        "Prioritize high-impact geopolitical, economic, and public-interest updates with concrete facts."
    ),
    "financial markets": (
        "Fetch only the latest financial market updates from the last 24 hours. "
        "Include index/asset moves, policy actions, and major earnings with clear numbers."
    ),
    "tech revolution in india": (
        "Fetch only the latest technology developments in India from the last 24 hours. "
        "Cover startups, AI, policy, telecom, and product launches with facts and numbers."
    ),
    "india economy & policy": (
        "Fetch only the latest India economy and policy updates from the last 24 hours, with statistics and impact."
    ),
    "startup & venture capital": (
        "Fetch only the latest startup and VC developments from the last 24 hours, including funding, launches, and exits."
    ),
    "ai & emerging technology": (
        "Fetch only the latest global AI and emerging tech developments from the last 24 hours, with concrete impact."
    ),
    "cybersecurity": (
        "Fetch only the latest cybersecurity incidents and advisories from the last 24 hours, including affected entities and response."
    ),
    "climate & energy": (
        "Fetch only the latest climate and energy developments from the last 24 hours, with locations and measurable effects."
    ),
    "geopolitics & conflicts": (
        "Fetch only the latest geopolitics and conflict developments from the last 24 hours, with verified facts and implications."
    ),
    "business & corporate": (
        "Fetch only the latest business and corporate developments from the last 24 hours, including deals, leadership, and regulation."
    ),
    "festivals & culture": (
        "Fetch only the latest festivals and culture updates from the last 24 hours in India, with specific events and outcomes."
    ),
    "sports business": (
        "Fetch only the latest sports business developments from the last 24 hours, including rights, sponsorships, and major announcements."
    )
}

TOPIC_HASHTAGS = {
    "world news": ["#WorldNews", "#GlobalAffairs", "#BreakingNews"],
    "financial markets": ["#Markets", "#Stocks", "#Finance"],
    "tech revolution in india": ["#IndiaTech", "#StartupIndia", "#AI"],
    "india economy & policy": ["#IndianEconomy", "#Policy", "#RBI"],
    "startup & venture capital": ["#Startups", "#VentureCapital", "#Funding"],
    "ai & emerging technology": ["#AI", "#EmergingTech", "#Innovation"],
    "cybersecurity": ["#CyberSecurity", "#Infosec", "#DataBreach"],
    "climate & energy": ["#Climate", "#Energy", "#Renewables"],
    "geopolitics & conflicts": ["#Geopolitics", "#GlobalRisk", "#Diplomacy"],
    "business & corporate": ["#Business", "#Corporate", "#Mergers"],
    "festivals & culture": ["#Culture", "#Festivals", "#India"],
    "sports business": ["#SportsBusiness", "#Sponsorship", "#MediaRights"],
}


def web_search_latest(query: str, days: int = NEWS_LOOKBACK_DAYS, max_results: int = 10):
    print('tool calling... latest news mode')


    response = tavilyclient.search(
        query=query,
        topic='news',
        search_depth='advanced',
        max_results=max_results,
        time_range='day',
        days=days,
        include_answer=False,
    )

    items = []
    for result in response.get('results', []):
        title = result.get('title', 'N/A')
        source_url = result.get('url', 'N/A')
        content = result.get('content', '')
        published = (
            result.get('published_date')
            or result.get('date')
            or result.get('published')
            or 'N/A'
        )
        items.append(
            f"Headline: {title}\nPublished: {published}\nSource: {source_url}\nDetails: {content}"
        )

    return '\n\n'.join(items)


def get_round_robin_topic():
    current_index = 0

    if os.path.exists(TOPIC_STATE_FILE):
        try:
            with open(TOPIC_STATE_FILE, 'r', encoding='utf-8') as state_file:
                current_index = int(state_file.read().strip() or '0')
        except (ValueError, OSError):
            current_index = 0

    current_index = current_index % len(TOPIC_ORDER)
    selected_topic = TOPIC_ORDER[current_index]
    next_index = (current_index + 1) % len(TOPIC_ORDER)

    try:
        with open(TOPIC_STATE_FILE, 'w', encoding='utf-8') as state_file:
            state_file.write(str(next_index))
    except OSError as e:
        print(f'Failed to persist round-robin state: {e}')

    return selected_topic


def normalize_tweet(text: str):
    return ' '.join((text or '').replace('\n', ' ').split()).strip()


def trim_to_limit(text: str, limit: int):
    tweet = normalize_tweet(text)
    if len(tweet) <= limit:
        return tweet

    trimmed = tweet[:limit].rstrip()
    last_space = trimmed.rfind(' ')
    if last_space > 180:
        trimmed = trimmed[:last_space].rstrip()

    return trimmed


def add_topic_hashtags(tweet: str, topic: str, limit: int):
    result = normalize_tweet(tweet)
    hashtags = TOPIC_HASHTAGS.get(topic, [])

    for tag in hashtags:
        if tag.lower() in result.lower():
            continue
        candidate = f'{result} {tag}' if result else tag
        if len(candidate) <= limit:
            result = candidate

    return result


def has_stale_year(tweet: str):
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', tweet)]
    current_year = datetime.now(timezone.utc).year
    return any(y < current_year for y in years)


def generate_tweet(news_data: str, topic: str, limit: int):
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    sys_prompt = (
        'You are an expert investigative journalist and social media analyst. '
        'Create one factual, high-impact tweet with specific names, places, and numbers. '
        'Output only tweet text; no intro lines, no quote marks, and no filler punctuation.'
    )

    user_prompt = (
        f'Current UTC date: {today_str}.\n'
        f'Use only events from the last {NEWS_LOOKBACK_DAYS} day(s). '
        'Do not include older events or historical references unless directly updated today.\n\n'
        f'News data:\n\n{news_data}\n\n'
        f'Task: Generate one strong tweet up to {limit} characters (including spaces). '
        'Keep it sharp and informative. If useful, include 1-2 relevant hashtags naturally.'
    )

    completion = client.chat.completions.create(
        temperature=0.5,
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
    )

    tweet = normalize_tweet(completion.choices[0].message.content)

    if len(tweet) > limit or has_stale_year(tweet):
        rewrite_prompt = (
            f'Rewrite this tweet to be <= {limit} characters and strictly latest-only. '
            f'Remove stale references (for example old years before {datetime.now(timezone.utc).year}) '\
            'unless they are part of a new update today. Keep core facts.\n\n'
            f'Tweet:\n{tweet}'
        )
        rewrite = client.chat.completions.create(
            temperature=0.3,
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': 'You are a precise editor. Return only the rewritten tweet text.'},
                {'role': 'user', 'content': rewrite_prompt},
            ],
        )
        tweet = normalize_tweet(rewrite.choices[0].message.content)

    tweet = trim_to_limit(tweet, limit)
    tweet = add_topic_hashtags(tweet, topic, limit)
    return trim_to_limit(tweet, limit)


def main():
    selected_topic = get_round_robin_topic()
    print(f'Selected topic (round-robin): {selected_topic}')
    query = TOPIC_PROMPTS[selected_topic]

    news_data = web_search_latest(query)
    print(news_data)

    generated_tweet = generate_tweet(news_data, selected_topic, X_FREE_CHAR_LIMIT)
    print('\n--- GENERATED TWEET ---\n')
    print(generated_tweet)
    print(f'\nCharacter count: {len(generated_tweet)}')
    print('\n-----------------------\n')

    send_email(
        subject='Your Weekly Auto-Generated Tweet',
        body=generated_tweet,
        to_emails=[
            'prathamdhanvade25@gmail.com',
            'karmatechnolabs@gmail.com'
        ]
    )


if __name__ == '__main__':
    main()

