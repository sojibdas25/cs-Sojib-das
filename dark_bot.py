import logging, requests, asyncio, sys, json, os, time
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার কানেক্টিভিটি (বট ২৪ ঘণ্টা সচল রাখতে) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "CS DARK SMS PRO - OTP AUTO-SYSTEM ACTIVE!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. আপনার কনফিগারেশন ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 
GROUP_ID = -1003525081102 

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

# আপনি যে দেশগুলো চেয়েছিলেন এবং স্ক্রিনশটে আসা দেশগুলো সব অ্যাড করা হয়েছে
COUNTRIES = {
    "🇺🇦 Ukraine": "ua", "🇸🇸 S. Sudan": "ssd", "🇱🇨 S. Lucia": "lca",
    "🇺🇸 USA": "usa", "🇬🇧 UK": "uk", "🇨🇦 Canada": "ca",
    "🇮🇳 India": "in", "🇧🇩 BD": "bd", "🇷🇺 Russia": "ru",
    "🇲🇾 Malaysia": "my", "🇮🇩 Indonesia": "id",
    "🇻🇳 Vietnam": "vn", "🇹🇭 Thailand": "th", "🇸🇦 S. Arabia": "sa",
    "🇸🇱 S. Leone": "sle", "🇩🇿 Algeria": "dza", "🇹🇿 Tanzania": "tza"
}

DB_FILE = "/tmp/user_stats.json" 

def get_stats():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f: return json.load(f)
    except: pass
    return {}

def save_stats(stats):
    try:
        with open(DB_FILE, "w") as f: json.dump(stats, f)
    except: pass

# --- ৩. ওটিপি অটো-ফেচিং ফাংশন (নতুন আপগ্রেড) ---
async def fetch_otp_task(context, chat_id, number, msg_id, user_id):
    url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={number}&serial=2"
    
    for _ in range(30): # ৫ মিনিট পর্যন্ত চেক করবে
        await asyncio.sleep(10)
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('code') == 200 and res.get('data'):
                otp = res.get('data')
                
                # সাকসেস হলে My ID কাউন্ট বাড়ানো
                stats = get_stats()
                uid = str(user_id)
                stats[uid] = stats.get(uid, 0) + 1
                save_stats(stats)
                
                success_text = f"✅ **OTP Received for** `{number}`\n\n💬 **Code:** `{otp}`"
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=success_text, parse_mode='Markdown')
                
                # গ্রুপে ওটিপি ফরওয়ার্ড করা
                await context.bot.send_message(chat_id=GROUP_ID, text=f"🔥 **New OTP Forwarded:**\nNum: `{number}`\nCode: `{otp}`", parse_mode='Markdown')
                return
        except: pass
    
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! No OTP received for `{number}`. Try again.")

# --- ৪. বাটন ও হ্যান্ডলারস ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📱 Get Number")],
        [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")],
        [KeyboardButton("📢 OTP Group")]
    ], resize_keyboard=True)

def country_menu():
    buttons = []
    keys = list(COUNTRIES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(keys[i], callback_data=f"iso_{COUNTRIES[keys[i]]}")]
        if i+1 < len(keys):
            row.append(InlineKeyboardButton(keys[i+1], callback_data=f"iso_{COUNTRIES[keys[i+1]]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update
