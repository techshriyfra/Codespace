import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Define your tokens
TELEGRAM_TOKEN = '7507479675:AAGnbw9YuMi6q9V0DUuWsK6DYuEKKJwju0U'
OWNER_NAME = 'Tech Shreyansh'
OWNER_URL = 'https://t.me/Tech_Shreyansh29'  # Replace with your URL
CHANNEL_URL = 'https://t.me/Tech_Shreyansh2'  # Replace with your channel URL

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
        update.message.reply_text("GitHub token set successfully! Use /codespaces to list your Codespaces.", reply_markup=reply_markup)
    else:
        update.message.reply_text("Please provide your GitHub token. Example: /on YOUR_GITHUB_TOKEN", reply_markup=reply_markup)

# Codespaces command handler to list Codespaces with selection buttons
def codespaces(update: Update, context: CallbackContext):
    if not github_token:
        update.message.reply_text("⚠️ You need to provide a GitHub token. Use /on <token> to authorize. 🔑")
        return

    headers = {'Authorization': f'token {github_token}'}
    response = requests.get('https://api.github.com/user/codespaces', headers=headers)

    if response.status_code == 200:
        codespaces_data = response.json()
        if "codespaces" in codespaces_data:
            codespaces_list = codespaces_data["codespaces"]
            message = '🔍 Select a Codespace to start from the list below:'
            keyboard = [
                [InlineKeyboardButton(f"{codespace.get('name')}", callback_data=f"start_{codespace['name']}")]
                for codespace in codespaces_list
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup)
        else:
            update.message.reply_text('You have no Codespaces.')
    else:
        update.message.reply_text('Failed to retrieve Codespaces.')

# Callback query handler to start a selected Codespace
def start_codespace(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    codespace_name = query.data.split("_")[1]
    headers = {'Authorization': f'token {github_token}'}
    response = requests.post(f'https://api.github.com/user/codespaces/{codespace_name}/start', headers=headers)
    
    if response.status_code == 202:
        query.edit_message_text(text=f"✅ Successfully started the Codespace '{codespace_name}'! 🛠️\n\n")
    else:
        query.edit_message_text(text=f"Failed to start the Codespace '{codespace_name}'. Ensure the name is correct.\n\n")

# Off command handler to stop a Codespace
def off(update: Update, context: CallbackContext):
    reply_markup = get_inline_keyboard()
    if not github_token:
        update.message.reply_text("Please set your GitHub token first using the /on command.", reply_markup=reply_markup)
        return

    if not context.args:
        update.message.reply_text("Please provide the name of the Codespace to stop. Example: /off CODESPACE_NAME", reply_markup=reply_markup)
        return

    codespace_name = context.args[0]
    headers = {'Authorization': f'token {github_token}'}
    response = requests.delete(f'https://api.github.com/user/codespaces/{codespace_name}', headers=headers)

    if response.status_code == 204:
        update.message.reply_text(f"Codespace '{codespace_name}' stopped successfully.", reply_markup=reply_markup)
    else:
        update.message.reply_text(f"Failed to stop Codespace '{codespace_name}'. Ensure the name is correct.", reply_markup=reply_markup)

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
