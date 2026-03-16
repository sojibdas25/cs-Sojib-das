import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs"

DURIAN_USERNAME = "rafiqmolla7"
DURIAN_API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
PROJECT_ID = "0257"

OTP_GROUP_ID = -1003525081102

# Allowed Users (Name + ID)
ALLOWED_USERS = {
6528471341: "Sojib",
8081334307: "Sojib Das",
8181512467: "Admin",
8164389661: "pc",
6630618306: "Chandon"
}

keyboard = [
["📱 Get Number"],
["💰 Balance","🆔 My ID"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def check_user(user_id):
    return user_id in ALLOWED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not check_user(user_id):
        await update.message.reply_text("❌ You are not allowed to use this bot")
        return

    name = ALLOWED_USERS[user_id]

    await update.message.reply_text(
        f"✅ Welcome {name} to CS Dark SMS Bot",
        reply_markup=reply_markup
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not check_user(user_id):
        return

    text = update.message.text

    if text == "🆔 My ID":

        name = ALLOWED_USERS[user_id]

        await update.message.reply_text(
            f"👤 Name: {name}\n🆔 ID: {user_id}"
        )


    elif text == "💰 Balance":

        url = f"https://api.durianpanel.com/balance?username={DURIAN_USERNAME}&api_key={DURIAN_API_KEY}"

        r = requests.get(url).json()

        balance = r.get("balance","0")

        await update.message.reply_text(f"💰 Balance: {balance}$")


    elif text == "📱 Get Number":

        url = f"https://api.durianpanel.com/get_number?username={DURIAN_USERNAME}&api_key={DURIAN_API_KEY}&pid={PROJECT_ID}"

        r = requests.get(url).json()

        if r["status"] == "success":

            number = r["number"]
            order_id = r["id"]

            await update.message.reply_text(
                f"📱 Number: {number}\n🆔 Order ID: {order_id}"
            )

        else:

            await update.message.reply_text("❌ Number not available")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, message))

app.run_polling()
