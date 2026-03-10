from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from send_email import send_email
import os

load_dotenv()

client = Groq(
    api_key = os.getenv('GROQ_API_KEY')
)

tavilyclient = TavilyClient(
    api_key = os.getenv('TAVILY_API_KEY')
)

TOPIC_PROMPTS = {
    "world news": (
        "Fetch the best and most important world news developments from the last 2 days. "
        "For each item, provide: what happened, where, who is involved, key numbers/dates, "
        "why it matters now, and likely short-term impact."
    ),
    "financial markets": (
        "Fetch the best and most impactful financial market stories from the last 2 days. "
        "Include equities, bonds, commodities, forex, crypto, central bank actions, and major earnings. "
        "For each item, provide index/asset moves with percentages, key drivers, and implications."
    ),
    "tech revolution in india": (
        "Fetch the best and most important technology developments in India from the last 2 days. "
        "Cover AI, startups, funding rounds, policy updates, semiconductors, telecom, DPI/UPI, and enterprise tech. "
        "For each item, include company/government names, numbers, timeline, and why it matters."
    ),
    "india economy & policy": (
        "Fetch the best and most important India economy and policy updates from the last 2 days. "
        "Include inflation, GDP-related signals, jobs, taxation, RBI actions, trade, and government announcements. "
        "For each item, include key statistics and expected economic impact."
    ),
    "startup & venture capital": (
        "Fetch the best and most impactful startup and VC stories from the last 2 days. "
        "Include funding rounds, valuations, exits, layoffs, pivots, and major product launches. "
        "For each item, include company, investor names, amount, stage, and significance."
    ),
    "ai & emerging technology": (
        "Fetch the best and most impactful AI and emerging tech stories from the last 2 days globally. "
        "Include model releases, regulations, partnerships, hardware/chips, and enterprise adoption. "
        "For each item, include concrete facts, numbers, and practical impact."
    ),
    "cybersecurity": (
        "Fetch the best and most critical cybersecurity stories from the last 2 days. "
        "Include breaches, ransomware, vulnerabilities, patches, and government advisories. "
        "For each item, include affected entities, scale of impact, CVE/technical details if available, and response actions."
    ),
    "climate & energy": (
        "Fetch the best and most important climate and energy stories from the last 2 days. "
        "Include extreme weather, climate policy, emissions actions, oil/gas, renewables, and grid developments. "
        "For each item, include locations, numbers, and economic/social impact."
    ),
    "geopolitics & conflicts": (
        "Fetch the best and most important geopolitics and conflict developments from the last 2 days. "
        "Include diplomacy, sanctions, military escalations, ceasefire talks, and multilateral decisions. "
        "For each item, include actors, timeline, and global market/humanitarian implications."
    ),
    "business & corporate": (
        "Fetch the best and most impactful business and corporate stories from the last 2 days. "
        "Include mergers, acquisitions, leadership changes, regulation, antitrust actions, and strategic moves. "
        "For each item, include company names, deal values, and impact on sector trends."
    ),
    "festivals & culture": (
        "Fetch the best and most notable festivals and cultural event stories from the last 2 days in India. "
        "Include attendance, tourism impact, revenue estimates, major incidents, and cultural significance. "
        "For each item, include location, organizers, and measurable outcomes."
    ),
    "sports business": (
        "Fetch the best and most important sports business stories from the last 2 days. "
        "Include media rights, sponsorships, major tournament updates, franchise valuation moves, and governance changes. "
        "For each item, include numbers, stakeholders, and commercial impact."
    )
}
TOPIC_ORDER = list(TOPIC_PROMPTS.keys())
TOPIC_STATE_FILE = "topic_state.txt"


def webSearch(query:str):
    print('tool calling...')
    responses = tavilyclient.search(query)
    result = '\n\n'.join(
        response['content'] for response in responses['results']
    )
    return result


def get_round_robin_topic():
    current_index = 0

    if os.path.exists(TOPIC_STATE_FILE):
        try:
            with open(TOPIC_STATE_FILE, "r", encoding="utf-8") as state_file:
                current_index = int(state_file.read().strip() or "0")
        except (ValueError, OSError):
            current_index = 0

    current_index = current_index % len(TOPIC_ORDER)
    selected_topic = TOPIC_ORDER[current_index]
    next_index = (current_index + 1) % len(TOPIC_ORDER)

    try:
        with open(TOPIC_STATE_FILE, "w", encoding="utf-8") as state_file:
            state_file.write(str(next_index))
    except OSError as e:
        print(f"Failed to persist round-robin state: {e}")

    return selected_topic


def main():
    selected_topic = get_round_robin_topic()
    print(f"Selected topic (round-robin): {selected_topic}")
    query = TOPIC_PROMPTS[selected_topic]
    news_data = webSearch(query)
    print(news_data)
    
    sys_prompt = "You are an expert investigative journalist and social media analyst. Your goal is to extract the most critical, factual details from a list of news stories and craft a high-impact, information-dense tweet. Avoid vague generalizations; include specific names, locations, and numbers where possible. Focus on 'Why this matters now'. The tweet must be 280 characters(including spaces)."
    
    user_prompt = f"Here is the detailed news data from the past 2 days:\n\n{news_data}\n\nTask: Based on these facts, generate one informative tweet that is strictly 280 characters(including spaces). Prioritize specific breakthroughs, conflict developments, or economic figures. Make it news-first, not hype."

    completion = client.chat.completions.create(
        temperature = 0.7,
        model = 'llama-3.3-70b-versatile',
        messages=[
            {
                'role':'system',
                'content':sys_prompt
            },
            {
                'role':'user',
                'content':user_prompt
            }
        ]
    )
    
    generated_tweet = completion.choices[0].message.content
    print("\n--- GENERATED TWEET ---\n")
    print(generated_tweet)
    print("\n-----------------------\n")

    send_email(
        subject="Your Weekly Auto-Generated Tweet",
        body=generated_tweet,
        to_emails=[
            "prathamdhanvade25@gmail.com",
            "karmatechnolabs@gmail.com"
        ]
    )


if __name__ == '__main__':
    main()




