import logging, requests, asyncio, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. ওয়েব সার্ভার (রেন্ডার পোর্টের জন্য) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM: DIRECT COUNTRY SEARCH ACTIVE"

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

# কান্ট্রি ডাটাবেজ (ISO এবং সঠিক প্রিফিক্স)
COUNTRY_DATA = {
    "ss": {"name": "South Sudan", "prefix": "211"},
    "tm": {"name": "Turkmenistan", "prefix": "993"},
    "ve": {"name": "Venezuela", "prefix": "58"},
    "dz": {"name": "Algeria", "prefix": "213"}
}

# --- ৩. ওটিপি ইঞ্জিন ---
async def fetch_otp_task(context, chat_id, full_number, msg_id, iso_code):
    num_only = ''.join(filter(str.isdigit, str(full_number)))
    
    # ওটিপি ফেচিং শুরু (সেট রিলিজ কল করে)
    requests.get(f"https://api.durianrcs.com/out/ext_api/setRelease?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2")
    vcode_url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    
    for _ in range(60): 
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
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! No OTP for `{full_number}`", reply_markup=kb)

# --- ৪. ইউজার ইন্টারফেস ও নম্বর হান্টিং ---
async def get_number_handler(context, chat_id, msg_id, iso_code):
    country_info = COUNTRY_DATA.get(iso_code)
    # প্যানেলকে নির্দিষ্ট দেশে বাধ্য করার জন্য এপিআই কল
    url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&iso={iso_code}&force_country=1"
    
    try:
        res = requests.get(url, timeout=15).json()
        if res.get('code') == 200:
            number = res.get('data')
            num_clean = ''.join(filter(str.isdigit, str(number)))

            # প্যানেল যদি তবুও ভুল দেয় (সেফটি গার্ড)
            if not num_clean.startswith(country_info['prefix']):
                requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_clean}&serial=2")
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Search Again", callback_data=f"get_{iso_code}")]])
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ প্যানেল ভুল নম্বর দিয়েছে। শুধু {country_info['name']} নম্বর ফিল্টার হচ্ছে...", reply_markup=kb)
                return

            # সঠিক নম্বর পাওয়া গেলে
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Block", callback_data=f"block_{number}_{iso_code}")]])
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
                text=f"🌍 **Country:** {country_info['name']}\n📱 **Number:** `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
            asyncio.create_task(fetch_otp_task(context, chat_id, number, msg_id, iso_code))
        else:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data=f"get_{iso_code}")]])
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ **No Stock** for {country_info['name']}. Please try again.", reply_markup=kb)
    except:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⚠️ Connection Error!")

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("get_"):
        iso = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Searching for **{iso.upper()}** number only...")
        await get_number_handler(context, query.message.chat_id, sent_msg.message_id, iso)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ALLOWED_USERS:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇸🇸 South Sudan", callback_data="get_ss")],
            [InlineKeyboardButton("🇹🇲 Turkmenistan", callback_data="get_tm")],
            [InlineKeyboardButton("🇻🇪 Venezuela", callback_data="get_ve"), InlineKeyboardButton("🇩🇿 Algeria", callback_data="get_dz")]
        ])
        await update.message.reply_text("🌑 **CS DARK BOT**\nTargeted Country Search Enabled.", reply_markup=kb)

# (বাকি মেইন ফাংশন আগের মতোই)
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
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
