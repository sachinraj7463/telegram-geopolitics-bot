import os
import tweepy
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()

client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)

def check_post_limits():
    response = client.get_rate_limit_status()
    if "resources" in response.data:
        tweet_limits = response.data["resources"]["statuses"]["/statuses/update"]
        remaining = tweet_limits["remaining"]
        reset = tweet_limits["reset"]
        print(f"🚨 Remaining tweets: {remaining}")
        print(f"🔁 Reset at (Unix timestamp): {reset}")
    else:
        print("❌ Could not fetch rate limit data.")

check_post_limits()
