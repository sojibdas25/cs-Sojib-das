import logging, requests, asyncio, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. ওয়েব সার্ভার (রেন্ডার পোর্টের জন্য) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM STATUS: ACTIVE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. কনফিগারেশন ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 

ALLOWED_USERS = {6528471341: "Sojib", 8081334307: "Sojib Das", 8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"}

# কান্ট্রি প্রিফিক্স ডাটাবেজ (Turkmenistan যুক্ত করা হয়েছে)
COUNTRY_DATA = {
    "us": "1", "ao": "244", "ng": "234", "mz": "258", "mx": "52", "ke": "254",
    "th": "66", "cm": "237", "eg": "20", "sn": "221", "ly": "218", "in": "91",
    "ru": "7", "cg": "242", "af": "93", "mr": "222", "tg": "228", "tn": "216",
    "ar": "54", "dz": "213", "mw": "265", "zm": "260", "ve": "58", "ug": "256",
    "gh": "233", "et": "251", "do": "1", "cd": "243", "tm": "993"
}

# --- ৩. ওটিপি ইঞ্জিন ---
async def fetch_otp_task(context, chat_id, full_number, msg_id, iso_code):
    num_only = ''.join(filter(str.isdigit, str(full_number)))
    expected_prefix = COUNTRY_DATA.get(iso_code, "")
    
    # ভুল দেশ আসলে সাথে সাথে অটো-ক্যান্সেল
    if expected_prefix and not num_only.startswith(expected_prefix):
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data=f"get_{iso_code}")]])
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⚠️ ভুল দেশ ({num_only[:3]}) এসেছে। অটো-ক্যান্সেল করা হয়েছে।", reply_markup=kb)
        return

    # ওটিপি ফেচিং শুরু
    requests.get(f"https://api.durianrcs.com/out/ext_api/setRelease?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2")
    vcode_url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    
    for _ in range(60): # ১০ সেকেন্ড পর পর ৬০ বার চেক (১০ মিনিট)
        await asyncio.sleep(10)
        try:
            res = requests.get(vcode_url, timeout=10).json()
            if res.get('code') == 200 and res.get('data'):
                otp = str(res.get('data'))
                if otp.lower() != "none" and len(otp) > 1:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
                        text=f"✅ **OTP Received!**\n\n📱 **Num:** `{full_number}`\n🔑 **OTP:** `{otp}`", parse_mode='Markdown')
                    return
        except: pass
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data=f"get_{iso_code}")]])
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! `{full_number}`", reply_markup=kb)

# --- ৪. ইউজার ইন্টারফেস ---
def main_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Get Number")], [KeyboardButton("💰 Balance")]], resize_keyboard=True)

def country_menu():
    buttons = [
        [InlineKeyboardButton("🇹🇲 Turkmenistan", callback_data="get_tm")],
        [InlineKeyboardButton("🇻🇪 Venezuela", callback_data="get_ve"), InlineKeyboardButton("🇩🇿 Algeria", callback_data="get_dz")],
        [InlineKeyboardButton("🇿🇲 Zambia", callback_data="get_zm"), InlineKeyboardButton("🇺🇬 Uganda", callback_data="get_ug")]
    ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ALLOWED_USERS:
        await update.message.reply_text("🌑 **CS DARK BOT**\nShort & Fast Mode Active.", reply_markup=main_menu())

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_"):
        iso = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Requesting **{iso.upper()}**...")
        
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&iso={iso}&force_country=1"
        
        try:
            res = requests.get(url, timeout=15).json()
            if res.get('code') == 200:
                number = res.get('data')
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Block", callback_data=f"block_{number}_{iso}")]])
                await query.edit_message_text(f"🌍 **{iso.upper()}**\n📱 `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
                asyncio.create_task(fetch_otp_task(context, query.message.chat_id, number, sent_msg.message_id, iso))
            else:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data=f"get_{iso}")]])
                await query.edit_message_text(f"❌ **No Number Available** for {iso.upper()}", reply_markup=kb, parse_mode='Markdown')
        except: await query.edit_message_text("❌ Connection Error!")

    elif query.data.startswith("block_"):
        data = query.data.split("_")
        num = ''.join(filter(str.isdigit, data[1]))
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num}&serial=2")
        await query.edit_message_text(f"🚫 `{data[1]}` Canceled.", reply_markup=country_menu())

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid = update.message.text, update.effective_user.id
    if uid not in ALLOWED_USERS: return
    if text == "📱 Get Number": await update.message.reply_text("🌍 Select Country:", reply_markup=country_menu())
    elif text == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getBalance?name={DURIAN_USER}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 Balance: `{res.get('data', '0')}`", parse_mode='Markdown')

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.add_handler(CallbackQueryHandler(callback_query))
    keep_alive()
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
