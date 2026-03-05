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


def webSearch(query:str):
    print('tool calling...')
    responses = tavilyclient.search(query)
    result = '\n\n'.join(
        response['content'] for response in responses['results']
    )
    return result


def main():
    query = '''List the top 10 most important global news headlines from the past 7 days. For each, provide the headline and detail description about what happened.'''
    news_data = webSearch(query)
    print(news_data)
    
    sys_prompt = "You are an expert investigative journalist and social media analyst. Your goal is to extract the most critical, factual details from a list of news stories and craft a high-impact, information-dense tweet. Avoid vague generalizations; include specific names, locations, and numbers where possible. Focus on 'Why this matters now'. "
    
    user_prompt = f"Here is the detailed news data from the past 7 days:\n\n{news_data}\n\nTask: Based on these facts, generate the most informative and detailed tweet possible. Prioritize specific breakthroughs, conflict developments, or economic figures. Make it 'news-first', not just hype."

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
        subject="🗞️ Your Weekly Auto-Generated Tweet",
        body=generated_tweet,
        to_email='prathamdhanvade25@gmail.com'
    )


if __name__ == '__main__':
    main()