import os
import tweepy
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Twitter credentials (v2)
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
consumer_key = os.getenv("TWITTER_API_KEY")
consumer_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Set up Tweepy Client (v2)
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# Get tweet content
user_input = input("Enter the tweet you want to post: ")

# Confirm & post
print("\n💬 Tweet Preview:\n", user_input)
confirm = input("\nPost this tweet? (y/n): ")

if confirm.lower() == "y":
    try:
        client.create_tweet(text=user_input)
        print("✅ Tweet posted successfully!")
    except Exception as e:
        print("❌ Error posting tweet:", e)
else:
    print("❌ Tweet cancelled.")
