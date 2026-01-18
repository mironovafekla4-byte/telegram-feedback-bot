import telebot
import sys
import os

TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("ERROR: BOT_TOKEN environment variable not set")
    print("Set it with: export BOT_TOKEN=your_token")
    sys.exit(1)

print("Testing bot connection...")
print(f"Token: {TOKEN[:10]}...")

try:
    bot = telebot.TeleBot(TOKEN)
    
    # Получаем информацию о боте
    bot_info = bot.get_me()
    print(f"\nBot connected successfully!")
    print(f"Bot username: @{bot_info.username}")
    print(f"Bot name: {bot_info.first_name}")
    print(f"Bot ID: {bot_info.id}")
    print(f"\nBot is ready to receive messages!")
    
except Exception as e:
    print(f"\nERROR: Failed to connect to bot")
    print(f"Error details: {e}")
    print("\nPossible reasons:")
    print("1. Invalid token")
    print("2. No internet connection")
    print("3. Telegram API is unavailable")
    sys.exit(1)
