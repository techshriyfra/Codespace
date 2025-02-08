import telebot
import requests
import json
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_BOT_TOKEN = "7507479675:AAGnbw9YuMi6q9V0DUuWsK6DYuEKKJwju0U"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

user_tokens = {}  # Store user tokens in memory

# Function to make requests with retries
def make_request(url, headers, method='GET', data=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 403:
                return None, "⚠️ GitHub API rate limit exceeded. Try again later."
            
            if response.status_code in [200, 201]:
                return response, None
            
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                return None, f"❌ Network error: {str(e)}. Please try again later."
        
        time.sleep(delay)
    return None, "❌ Failed after multiple attempts. Please try again later."

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "\U0001F47E Welcome to the GitHub Codespace Manager Bot! \U0001F47E\n\n"
                                      "Here’s the deal:\n"
                                      "1️⃣ Use the /on command followed by your GitHub token to take control of your Codespaces. \U0001F511\n"
                                      "2️⃣ Pick a Codespace from the list, and we’ll fire it up for you. ⚙️\n"
                                      "3️⃣ Already running? We’ll let you know so you’re not left wondering. 🔍\n\n"
                                      "Let’s get this show on the road! 🚀")

# Handle GitHub token input
@bot.message_handler(commands=['on'])
def on_command(message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑")
        return
    
    token = parts[1]
    user_tokens[message.chat.id] = token
    bot.send_message(message.chat.id, "🔍 Fetching your Codespaces...")
    list_codespaces(message.chat.id, token)

# List Codespaces
def list_codespaces(chat_id, token):
    url = "https://api.github.com/user/codespaces"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response, error = make_request(url, headers)
    
    if error:
        bot.send_message(chat_id, error)
        return
    
    codespaces = response.json().get("codespaces", [])
    if not codespaces:
        bot.send_message(chat_id, "😕 No Codespaces found. Please ensure your token is correct and try again. 📜")
        return
    
    markup = InlineKeyboardMarkup()
    for cs in codespaces:
        markup.add(InlineKeyboardButton(cs['name'], callback_data=f"start_{cs['name']}"))
    bot.send_message(chat_id, "🔍 Select a Codespace to start from the list below:", reply_markup=markup)

# Handle Codespace start request
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_"))
def start_codespace(call):
    chat_id = call.message.chat.id
    if chat_id not in user_tokens:
        bot.send_message(chat_id, "⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑")
        return
    
    token = user_tokens[chat_id]
    codespace_name = call.data.replace("start_", "")
    bot.send_message(chat_id, f"🔄 Please wait, we're firing up your Codespace `{codespace_name}`")
    
    url = f"https://api.github.com/user/codespaces/{codespace_name}/start"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response, error = make_request(url, headers, method='POST')
    
    if error:
        bot.send_message(chat_id, error)
        return
    
    if response.status_code == 201:
        bot.send_message(chat_id, f"✅ Successfully started the Codespace '{codespace_name}'! 🛠️")
    elif response.status_code == 409:
        bot.send_message(chat_id, f"⚠️ Codespace '{codespace_name}' is currently shutting down. Please wait a moment. ⏳")
    else:
        bot.send_message(chat_id, f"❌ Failed to start Codespace '{codespace_name}'. Please try again.")

bot.polling()
