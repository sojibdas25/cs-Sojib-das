import logging
import requests
import asyncio
import sys
import json
import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- রেন্ডার কানেক্টিভিটি ফিক্স (এটি বটকে ২৪ ঘণ্টা চালু রাখবে) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "CS DARK SMS PRO is Running 24/7!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- আপনার অরিজিনাল কনফিগারেশন (কোনো পরিবর্তন করা হয়নি) ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257'
GROUP_ID = -1003525081102 
BOT_USERNAME = 'CSDarkSMSBot'

ALLOWED_USERS = {
    6528471341: "Sojib",
    8081334307: "Sojib Das",
    8181512467: "Admin",
    8164389661: "pc",
    6630618306 : "Chandon"
}

COUNTRIES = {
    "🇺🇸 USA": "usa", "🇬🇧 UK": "uk", "🇨🇦 Canada": "ca",
    "🇮🇳 India": "in", "🇧🇩 BD": "bd", "🇷🇺 Russia": "ru",
    "🇲🇾 Malaysia": "my", "🇮🇩 Indonesia": "id",
    "🇻🇳 Vietnam": "vn", "🇹🇭 Thailand": "th", "🇸🇦 S. Arabia": "sa", "🇺🇦 Ukraine": "ua"
}

DB_FILE = "user_stats.json"

def get_stats():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_stats(stats):
    with open(DB_FILE, "w") as f: json.dump(stats, f)

def increment_otp(user_id):
    stats = get_stats()
    uid = str(user_id)
    stats[uid] = stats.get(uid, 0) + 1
    save_stats(stats)

logging.basicConfig(level=logging.INFO)

# --- আপনার অরিজিনাল কিবোর্ড ও হ্যান্ডলারস ---
def main_menu():
    keyboard = [
        [KeyboardButton("📱 Get Number")],
        [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")],
        [KeyboardButton("📢 OTP Group")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def country_menu():
    buttons = []
    keys = list(COUNTRIES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(keys[i], callback_data=f"iso_{COUNTRIES[keys[i]]}")]
        if i+1 < len(keys):
            row.append(InlineKeyboardButton(keys[i+1], callback_data=f"iso_{COUNTRIES[keys[i+1]]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ALLOWED_USERS:
        await update.message.reply_text(f"Welcome {ALLOWED_USERS[uid]}! 🌑\nSystem is Online.", reply_markup=main_menu())
    else:
        unauth_msg = "আমি বিশ্বস্ত ব্যক্তিকে কলিজায় রাখি। মীরজাফরদের এড়িয়ে চলি।"
        support_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 Support (Contact Admin)", url="https://t.me/Sojib9690")
        ]])
        await update.message.reply_text(unauth_msg, reply_markup=support_keyboard)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS: return

    if text == "📱 Get Number":
        await update.message.reply_text("🌍 Select Country to Get Fast Number:", reply_markup=country_menu())
async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("iso_"):
        # ইউজার যে দেশে ক্লিক করেছে তার কোড বড় হাতের অক্ষরে রূপান্তর (যেমন: BD, IN)
        iso = query.data.split("_")[1].upper()
        
        await query.edit_message_text(f"🛰 Requesting {iso} Number...")
        
        # প্যানেলকে নির্দিষ্ট দেশ দিতে বাধ্য করতে iso={iso} নিশ্চিত করা হয়েছে
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&iso={iso}"
        
        try:
            res = requests.get(url).json()
            if res.get('code') == 200:
                number = res.get('data')
                msg = f"✅ **Country:** {iso}\n✅ **Number:** `{number}`\n📩 Waiting for OTP..."
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Block Number", callback_data=f"block_{number}")],
                    [InlineKeyboardButton("🔄 Request Again", callback_data=f"iso_{iso.lower()}")]
                ])
                await query.edit_message_text(msg, reply_markup=kb, parse_mode='Markdown')
            else:
                # যদি ওই দেশে নাম্বার না থাকে তবে প্যানেলের মেসেজ দেখাবে
                await query.edit_message_text(f"❌ Error: {res.get('msg')} (In {iso})", reply_markup=country_menu())
        except Exception as e:
            await query.edit_message_text(f"❌ Connection Error: {str(e)}")
        if res.get('code') == 200:
            number = res.get('data')
            msg = f"✅ **Number:** `{number}`\n📩 Waiting for OTP..."
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 Block Number", callback_data=f"block_{number}")],
                [InlineKeyboardButton("🔄 Request Again", callback_data=f"iso_{iso}")]
            ])
            await query.edit_message_text(msg, reply_markup=kb, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ Error: {res.get('msg')}\n(Insufficient Balance)", reply_markup=country_menu())

# --- মেইন রানার ---
async def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.add_handler(CallbackQueryHandler(callback_query))
    
    print("CS DARK SMS PRO - ONLINE")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == '__main__':
    keep_alive() # রেন্ডার সার্ভার চালু করা
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
