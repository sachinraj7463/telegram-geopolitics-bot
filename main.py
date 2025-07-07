import os
import time
import requests.exceptions
import http.client
import tweepy
import google.generativeai as genai
import requests
from dotenv import load_dotenv
from datetime import datetime
import json

# Load .env variables
load_dotenv()

# Twitter API (v2) credentials
consumer_key = os.getenv("TWITTER_API_KEY")
consumer_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")  # Optional, not required for posting

# Gemini + News API
genai_api_key = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Set up Tweepy Client for v2
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True
)

# Set up Gemini
genai.configure(api_key=genai_api_key)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

# News endpoints
INDIA_NEWS_ENDPOINT = f"https://newsapi.org/v2/top-headlines?country=in&language=en&pageSize=20&apiKey={NEWS_API_KEY}"
CRICKET_ENDPOINT = f"https://newsapi.org/v2/everything?q=cricket+IPL+BCCI+India&language=en&sortBy=publishedAt&pageSize=30&apiKey={NEWS_API_KEY}"
SPORTS_ENDPOINT = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&country=in&pageSize=20&apiKey={NEWS_API_KEY}"

# Store posted titles
POSTED_FILE = "posted_titles.json"

def load_posted_titles():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_posted_titles(titles):
    with open(POSTED_FILE, 'w') as f:
        json.dump(list(titles), f)

posted_titles = load_posted_titles()

def fetch_combined_news():
    seen_titles = set()
    articles = []
    for url in [CRICKET_ENDPOINT, SPORTS_ENDPOINT, INDIA_NEWS_ENDPOINT]:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                new_articles = response.json().get("articles", [])
                for article in new_articles:
                    title = article.get("title")
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        articles.append(article)
            else:
                print(f"⚠️ Failed to fetch news from {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching news from {url}: {e}")
    return articles

def generate_tweet(title, description):
    prompt = f"""
Write one brutally honest, sarcastic, or savage tweet (ONLY ONE, NO OPTIONS) under 280 characters.
Make it engaging and tweet-worthy for Indian politics/cricket/sports viewers. It should go viral.
News title: {title}
News description: {description}
"""
    try:
        response = model.generate_content(prompt)
        lines = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
        return lines[0] if lines else ""
    except Exception as e:
        print("❌ Gemini error:", e)
        return ""

def run_bot():
    print("🤖 Starting cricket bot using Twitter API v2...")
    while True:
        articles = fetch_combined_news()
        print(f"📥 Found {len(articles)} articles.")

        post_count = 0
        for article in articles:
            title = article.get("title")
            description = article.get("description") or ""
            url = article.get("url") or ""

            if not title or title in posted_titles:
                continue

            tweet = generate_tweet(title, description)
            if not tweet:
                continue

            if len(tweet) + len(url) + 2 <= 280:
                tweet = f"{tweet}\n{url}"

            try:
                client.create_tweet(text=tweet)
                print(f"✅ Tweeted: {title}")
                posted_titles.add(title)
                save_posted_titles(posted_titles)
                post_count += 1
            except tweepy.TooManyRequests:
                print("⏳ Rate limit hit. Sleeping 15 minutes...")
                time.sleep(15 * 60)
            except Exception as e:
                print("❌ Tweet error:", e)

            if post_count >= 10:
                break

            time.sleep(6 * 60)  # wait 6 minutes between tweets

        print("😴 Sleeping for 1 hour before next cycle...")
        time.sleep(60 * 60)

if __name__ == "__main__":
    run_bot()
