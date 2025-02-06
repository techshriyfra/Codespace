import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler

# Define your tokens
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'
OWNER_NAME = 'YOUR_NAME_HERE'
OWNER_URL = 'https://your-url-here.com'  # Replace with your URL
CHANNEL_URL = 'https://t.me/YOUR_CHANNEL_NAME'  # Replace with your channel URL

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
def start(update, context):
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
def on(update, context):
    global github_token
    reply_markup = get_inline_keyboard()
    if context.args:
        github_token = context.args[0]
        update.message.reply_text("GitHub token set successfully! Use /codespaces to list your Codespaces.", reply_markup=reply_markup)
    else:
        update.message.reply_text("Please provide your GitHub token. Example: /on YOUR_GITHUB_TOKEN", reply_markup=reply_markup)

# Codespaces command handler to list Codespaces
def codespaces(update, context):
    reply_markup = get_inline_keyboard()
    if not github_token:
        update.message.reply_text("Please set your GitHub token first using the /on command.", reply_markup=reply_markup)
        return

    headers = {'Authorization': f'token {github_token}'}
    response = requests.get('https://api.github.com/user/codespaces', headers=headers)

    if response.status_code == 200:
        codespaces_data = response.json()
        if codespaces_data:
            message = 'Your Codespaces:\n'
            for codespace in codespaces_data:
                message += f"- {codespace['name']} (ID: {codespace['id']})\n"
            update.message.reply_text(message, reply_markup=reply_markup)
        else:
            update.message.reply_text('You have no Codespaces.', reply_markup=reply_markup)
    else:
        update.message.reply_text('Failed to retrieve Codespaces.', reply_markup=reply_markup)

# Off command handler to stop a Codespace
def off(update, context):
    reply_markup = get_inline_keyboard()
    if not github_token:
        update.message.reply_text("Please set your GitHub token first using the /on command.", reply_markup=reply_markup)
        return

    if not context.args:
        update.message.reply_text("Please provide the ID of the Codespace to stop. Example: /off CODESPACE_ID", reply_markup=reply_markup)
        return

    codespace_id = context.args[0]
    headers = {'Authorization': f'token {github_token}'}
    response = requests.delete(f'https://api.github.com/user/codespaces/{codespace_id}', headers=headers)

    if response.status_code == 204:
        update.message.reply_text(f"Codespace {codespace_id} stopped successfully.", reply_markup=reply_markup)
    else:
        update.message.reply_text(f"Failed to stop Codespace {codespace_id}. Ensure the ID is correct.", reply_markup=reply_markup)

# Main function to set up the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('on', on, pass_args=True))
    dp.add_handler(CommandHandler('codespaces', codespaces))
    dp.add_handler(CommandHandler('off', off, pass_args=True))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
