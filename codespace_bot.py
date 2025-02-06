import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Define your tokens
TELEGRAM_TOKEN = '7507479675:AAGnbw9YuMi6q9V0DUuWsK6DYuEKKJwju0U'  # Replace with your bot token
OWNER_NAME = 'Your Name'
OWNER_URL = 'https://t.me/YourUsername'
CHANNEL_URL = 'https://t.me/YourChannel'

# GitHub token and Codespace management
github_token = None
codespaces_list = []
current_codespace = None

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
        "Here’s the deal:\n"
        "1️⃣ Use the /on command followed by your GitHub token to take control of your Codespaces. 🔑\n"
        "2️⃣ Pick a Codespace from the list, and we’ll fire it up for you. ⚙️\n"
        "3️⃣ Already running? We’ll let you know so you’re not left wondering. 🔍\n\n"
        "Let’s get this show on the road! 🚀",
        reply_markup=reply_markup
    )

# On command handler to set GitHub token
def on(update: Update, context: CallbackContext):
    global github_token
    reply_markup = get_inline_keyboard()
    if context.args:
        github_token = context.args[0]
        update.message.reply_text("🔍 GitHub token set successfully! Use /codespaces to list your Codespaces.", reply_markup=reply_markup)
    else:
        update.message.reply_text("⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑", reply_markup=reply_markup)

# Codespaces command handler to list Codespaces
def codespaces(update: Update, context: CallbackContext):
    if not github_token:
        update.message.reply_text("⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑")
        return

    headers = {'Authorization': f'token {github_token}'}
    response = requests.get('https://api.github.com/user/codespaces', headers=headers)

    if response.status_code == 200:
        codespaces_data = response.json()
        if "codespaces" in codespaces_data and codespaces_data["codespaces"]:
            global codespaces_list
            codespaces_list = codespaces_data["codespaces"]
            message = '🔍 Select a Codespace to start from the list below:'
            keyboard = [
                [InlineKeyboardButton(f"{cs.get('name')} (ID: {cs['id']})", callback_data=f"start_{cs['id']}")]
                for cs in codespaces_list
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup)
        else:
            update.message.reply_text('⚠️ You have no Codespaces available.')
    else:
        update.message.reply_text(f"❌ Failed to retrieve Codespaces. GitHub API Error: {response.status_code}")

# Callback query handler to start a selected Codespace
def start_codespace(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    codespace_id = query.data.split("_")[1]
    headers = {'Authorization': f'token {github_token}'}
    
    # Check if the Codespace is already running
    global current_codespace
    if current_codespace and current_codespace['id'] == codespace_id:
        query.edit_message_text(f"✅ Codespace '{current_codespace['name']}' is already running! 🚀")
        return
    
    # Start the Codespace
    response = requests.post(f'https://api.github.com/user/codespaces/{codespace_id}/start', headers=headers)

    if response.status_code == 202:
        query.edit_message_text(f"⏳ Please wait, we are firing your Codespace... ⏳")
        
        # Check the status of the Codespace
        status_response = requests.get(f'https://api.github.com/user/codespaces/{codespace_id}', headers=headers)
        
        if status_response.status_code == 200:
            codespace_info = status_response.json()
            if codespace_info.get("state") == "Available":
                current_codespace = codespace_info
                query.edit_message_text(
                    text=f"✅ Successfully started the Codespace '{codespace_info['name']}'! 🛠️"
                )
            else:
                query.edit_message_text(
                    text=f"⚠️ Codespace '{codespace_info['name']}' is still starting... Try again later."
                )
        else:
            query.edit_message_text(f"❌ Failed to retrieve Codespace status. GitHub API Error: {status_response.status_code}")
    else:
        query.edit_message_text(f"❌ Failed to start Codespace. GitHub API Error: {response.status_code}")

# Off command handler to stop a Codespace
def off(update: Update, context: CallbackContext):
    if not github_token:
        update.message.reply_text("⚠️ Please set your GitHub token first using the /on command.")
        return

    if not context.args:
        update.message.reply_text("⚠️ Please provide the name of the Codespace to stop. Example: /off CODESPACE_NAME")
        return

    codespace_name = context.args[0]
    headers = {'Authorization': f'token {github_token}'}
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
