import os
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Put in .env
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))      # Your ID: 2100460652

# Twitter credentials
consumer_key = os.getenv("TWITTER_API_KEY")
consumer_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

# Twitter client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# Conversation states
HEADLINE, DESCRIPTION = range(2)

# Store temporary user inputs
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 Send the headline:")
    return HEADLINE

async def get_headline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["headline"] = update.message.text.strip()
    await update.message.reply_text("📝 Now send the full description (multi-line). Send /done when finished.")
    user_data["description"] = []
    return DESCRIPTION

async def collect_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["description"].append(update.message.text.strip())

async def finish_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = user_data.get("headline", "")
    description = " ".join(user_data.get("description", []))

    prompt = f"""
You're a viral tweet writer with a flair for sarcasm, satire, and savage one-liners. Given a news headline and summary, generate exactly ONE tweet under 280 characters.

Instructions:
- Be brutally honest, ironic, witty, sarcastic, or savagely clever.
- Reframe or expose the truth behind the headline.
- Use pop culture, hypocrisy, or drama.
- Your audience is Indian Twitter.
- Return only one tweet.
- Avoid repeating the headline.

Input:
Headline: {title}
Description: {description}
    """

    try:
        response = model.generate_content(prompt)
        tweet = response.text.strip().split('\n')[0]
    except Exception as e:
        await update.message.reply_text(f"❌ Gemini error: {e}")
        return ConversationHandler.END

    context.user_data["final_tweet"] = tweet

    keyboard = [["✅ Post", "❌ Cancel"]]
    await update.message.reply_text(
        f"📢 Generated Tweet:\n\n{tweet}",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return ConversationHandler.END

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    decision = update.message.text.lower()
    tweet = context.user_data.get("final_tweet")

    if "post" in decision:
        try:
            client.create_tweet(text=tweet)
            await update.message.reply_text("✅ Tweet posted successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error posting tweet: {e}")
    else:
        await update.message.reply_text("❌ Tweet cancelled.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_headline)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_description),
                CommandHandler("done", finish_description)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^(✅ Post|❌ Cancel)$"), handle_reply))

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
