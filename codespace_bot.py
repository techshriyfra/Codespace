import time
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Define your tokens
TELEGRAM_TOKEN = '7507479675:AAGnbw9YuMi6q9V0DUuWsK6DYuEKKJwju0U'  # Replace with actual bot token
OWNER_NAME = 'Tech Shreyansh'
OWNER_URL = 'https://t.me/Tech_Shreyansh29'
CHANNEL_URL = 'https://t.me/Tech_Shreyansh2'

# Global variable to store GitHub token
github_token = None

# Function to get the inline keyboard
def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("Owner", url=OWNER_URL)],
        [InlineKeyboardButton("Join Channel", url=CHANNEL_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command handler
def start(update: Update, context: CallbackContext):
    reply_markup = get_inline_keyboard()
    update.message.reply_text(
        "👾 Welcome to the GitHub Codespace Manager Bot! 👾\n\n"
        "Use the commands:\n"
        "1️⃣ /on <GitHub_Token> - Set your GitHub token\n"
        "2️⃣ /codespaces - List available Codespaces\n"
        "3️⃣ Select a Codespace to start 🚀\n"
        "4️⃣ /off <Codespace_Name> - Stop a Codespace 🛑",
        reply_markup=reply_markup
    )

# On command handler to set GitHub token
def on(update: Update, context: CallbackContext):
    global github_token
    if context.args:
        github_token = context.args[0]
        update.message.reply_text("✅ GitHub token set successfully! Use /codespaces to list your Codespaces.")
    else:
        update.message.reply_text("⚠️ Please provide your GitHub token. Example: /on YOUR_GITHUB_TOKEN")

# Codespaces command handler to list Codespaces
def codespaces(update: Update, context: CallbackContext):
    if not github_token:
        update.message.reply_text("⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑")
        return

    headers = {'Authorization': f'Bearer {github_token}'}
    response = requests.get('https://api.github.com/user/codespaces', headers=headers)

    if response.status_code == 200:
        codespaces_data = response.json()
        if "codespaces" in codespaces_data and codespaces_data["codespaces"]:
            keyboard = [
                [InlineKeyboardButton(f"{cs.get('name')}", callback_data=f"start_{cs.get('name')}")]
                for cs in codespaces_data["codespaces"]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("🔍 Select a Codespace to start:", reply_markup=reply_markup)
        else:
            update.message.reply_text("⚠️ You have no Codespaces available.")
    else:
        update.message.reply_text(f"❌ Failed to retrieve Codespaces. GitHub API Error: {response.status_code}")

# Callback query handler to start a selected Codespace
def start_codespace(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    codespace_name = query.data.split("_", 1)[1]
    headers = {'Authorization': f'Bearer {github_token}'}
    
    response = requests.post(f'https://api.github.com/user/codespaces/{codespace_name}/start', headers=headers)

    if response.status_code == 202:
        query.edit_message_text(text=f"⏳ Starting Codespace '{codespace_name}'... Please wait ⏳")

        # ✅ Wait for the Codespace to start
        time.sleep(5)  # Give it some time before checking its status

        # 🔍 Check the status of the Codespace
        status_response = requests.get(f'https://api.github.com/user/codespaces/{codespace_name}', headers=headers)
        if status_response.status_code == 200:
            codespace_info = status_response.json()
            if codespace_info.get("state") == "Available":
                query.edit_message_text(
                    text=f"✅ Successfully started Codespace '{codespace_name}'! 🚀\n"
                         f"💻 Open it here: {codespace_info.get('web_url')}"
                )
            else:
                query.edit_message_text(
                    text=f"⚠️ Codespace '{codespace_name}' is still starting... Try again later."
                )
        else:
            query.edit_message_text(
                text=f"❌ Codespace started but unable to fetch status. GitHub API Error: {status_response.status_code}"
            )

    elif response.status_code == 403:
        query.edit_message_text(text="❌ Permission denied. Ensure your GitHub token has `codespace` permissions.")
    elif response.status_code == 404:
        query.edit_message_text(text=f"❌ Codespace '{codespace_name}' not found. Check if it's available.")
    else:
        query.edit_message_text(text=f"❌ Failed to start Codespace {codespace_name}. GitHub API Error: {response.status_code}")

# Off command handler to stop a Codespace
def off(update: Update, context: CallbackContext):
    if not github_token:
        update.message.reply_text("⚠️ Please set your GitHub token first using the /on command.")
        return

    if not context.args:
        update.message.reply_text("⚠️ Please provide the name of the Codespace to stop. Example: /off CODESPACE_NAME")
        return

    codespace_name = context.args[0]
    headers = {'Authorization': f'Bearer {github_token}'}
    response = requests.delete(f'https://api.github.com/user/codespaces/{codespace_name}', headers=headers)

    if response.status_code == 204:
        update.message.reply_text(f"✅ Codespace '{codespace_name}' stopped successfully.")
    elif response.status_code == 404:
        update.message.reply_text(f"❌ Codespace '{codespace_name}' not found. Ensure the name is correct.")
    else:
        update.message.reply_text(f"❌ Failed to stop Codespace {codespace_name}. GitHub API Error: {response.status_code}")

# Main function to set up the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('on', on, pass_args=True))
    dp.add_handler(CommandHandler('codespaces', codespaces))
    dp.add_handler(CommandHandler('off', off, pass_args=True))
    dp.add_handler(CallbackQueryHandler(start_codespace, pattern='^start_'))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
