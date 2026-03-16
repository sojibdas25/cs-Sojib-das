import logging, requests, asyncio, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ---------- Render keep alive ----------
app_web = Flask('')
@app_web.route('/')
def home():
    return "SYSTEM STATUS: CUY ACTIVE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------- CONFIG ----------
BOT_TOKEN = "YOUR_BOT_TOKEN"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
DURIAN_USER = "rafiqmolla7"
PROJECT_ID = "0257"
GROUP_ID = -1003525081102

ALLOWED_USERS = {
6528471341:"Sojib",
8081334307:"Sojib Das",
8181512467:"Admin",
8164389661:"pc",
6630618306:"Chandon"
}

# COUNTRY CODE (cuy)
COUNTRIES = {
"🇺🇸 USA":"us",
"🇹🇭 Thailand":"th",
"🇮🇳 India":"in",
"🇳🇬 Nigeria":"ng",
"🇷🇺 Russia":"ru",
"🇲🇽 Mexico":"mx",
"🇰🇪 Kenya":"ke",
"🇪🇬 Egypt":"eg"
}

# ---------- OTP CHECK ----------
async def fetch_otp(context, chat_id, message_id, number, user_id, cuy):

    num = ''.join(filter(str.isdigit,str(number)))

    vcode_url=f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num}&serial=2"

    for i in range(60):

        await asyncio.sleep(10)

        try:

            res=requests.get(vcode_url,timeout=10).json()

            if res.get("code")==200 and res.get("data"):

                otp=res.get("data")

                kb=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Get New Number",callback_data=f"get_{cuy}")]
                ])

                await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ OTP RECEIVED\n\n📱 Number : `{number}`\n🔑 Code : `{otp}`",
                parse_mode="Markdown",
                reply_markup=kb)

                await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"🔥 OTP ALERT\n\n📱 {number}\n🔑 {otp}\n👤 {ALLOWED_USERS.get(user_id)}",
                parse_mode="Markdown")

                return

        except:
            pass

    await context.bot.edit_message_text(
    chat_id=chat_id,
    message_id=message_id,
    text=f"⏳ Timeout\nNo OTP for `{number}`",
    parse_mode="Markdown")

# ---------- MENUS ----------
def main_menu():

    return ReplyKeyboardMarkup(
    [
    [KeyboardButton("📱 Get Number")],
    [KeyboardButton("💰 Balance"),KeyboardButton("ℹ️ My ID")]
    ],
    resize_keyboard=True)

def country_menu():

    buttons=[]

    for k,v in COUNTRIES.items():

        buttons.append(
        [InlineKeyboardButton(k,callback_data=f"get_{v}")]
        )

    return InlineKeyboardMarkup(buttons)

# ---------- START ----------
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ALLOWED_USERS:
        return

    await update.message.reply_text(
    "🌑 CS DARK BOT\nSelect option",
    reply_markup=main_menu())

# ---------- MESSAGE ----------
async def handle_msg(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="📱 Get Number":

        await update.message.reply_text(
        "🌍 Select Country",
        reply_markup=country_menu())

    elif text=="ℹ️ My ID":

        await update.message.reply_text(
        f"Your ID : {update.effective_user.id}")

# ---------- CALLBACK ----------
async def callback_query(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    if query.data.startswith("get_"):

        cuy=query.data.split("_")[1]

        await query.edit_message_text(f"⏳ Requesting {cuy} number...")

        url=f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&cuy={cuy}"

        try:

            res=requests.get(url,timeout=15).json()

            if res.get("code")==200:

                number=res.get("data")

                msg=await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"🌍 Country : {cuy}\n📱 Number : `{number}`\n⏳ Waiting OTP...",
                parse_mode="Markdown")

                asyncio.create_task(
                fetch_otp(context,query.message.chat_id,msg.message_id,number,query.from_user.id,cuy)
                )

            else:

                await query.edit_message_text("❌ Stock Out")

        except:

            await query.edit_message_text("❌ Connection Error")

# ---------- MAIN ----------
async def main():

    keep_alive()

    app=Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_msg))
    app.add_handler(CallbackQueryHandler(callback_query))

    await app.run_polling()

if __name__=="__main__":
    asyncio.run(main())
