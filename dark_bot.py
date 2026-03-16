import logging, requests, asyncio, sys, json, os, time
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার কানেক্টিভিটি (২৪ ঘণ্টা বট সচল রাখার জন্য) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM STATUS: 100% STABLE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. আপনার কনফিগারেশন ডাটা ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 
GROUP_ID = -1003525081102 

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

# কান্ট্রি লিস্ট আপডেট করা হয়েছে
COUNTRIES = {
    "🇺🇸 USA": "usa", "🇬🇧 UK": "uk", "🇨🇦 Canada": "ca",
    "🇮🇳 India": "in", "🇧🇩 BD": "bd", "🇷🇺 Russia": "ru",
    "🇲🇾 Malaysia": "my", "🇮🇩 Indonesia": "id",
    "🇻🇳 Vietnam": "vn", "🇹🇭 Thailand": "th", "🇸🇦 S. Arabia": "sa", 
    "🇺🇦 Ukraine": "ua", "🇸🇸 S. Sudan": "ssd", "🇱🇨 S. Lucia": "lca"
}

DB_FILE = "/tmp/user_stats.json" 

def get_stats():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f: return json.load(f)
    except: pass
    return {}

# --- ৩. কিবোর্ড ও লজিক ---
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ALLOWED_USERS:
        await update.message.reply_text(f"Welcome {ALLOWED_USERS[uid]}! 🌑\nSystem is Online.", reply_markup=main_menu())
    else:
        await update.message.reply_text("Unauthorised Access!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url="https://t.me/Sojib9690")]]))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS: return

    if text == "📱 Get Number":
        await update.message.reply_text("🌍 Select Country (Trying to Match Target):", reply_markup=country_menu())
    elif text == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getBalance?name={DURIAN_USER}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 Balance: `{res.get('data', '0')}` Credits", parse_mode='Markdown')
    elif text == "ℹ️ My ID":
        stats = get_stats()
        count = stats.get(str(uid), 0)
        await update.message.reply_text(f"👤 Name: {ALLOWED_USERS[uid]}\n🆔 ID: `{uid}`\n📩 Total OTP: `{count}`", parse_mode='Markdown')
    elif text == "📢 OTP Group":
        await update.message.reply_text("Join OTP Zone:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Join", url="https://t.me/CsDrakOtpZone")]]))

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("iso_"):
        iso = query.data.split("_")[1]
        await query.edit_message_text(f"🛰 Requesting **{iso.upper()}** (Checking Stock)...", parse_mode='Markdown')
        
        # প্যানেলকে বাধ্য করার জন্য এলাকা (area) এবং অতিরিক্ত প্যারামিটার যোগ করা হয়েছে
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&iso={iso}&area={iso}&is_not_standard=1"
        
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('code') == 200:
                number = res.get('data')
                msg = f"✅ **Selected Country:** {iso.upper()}\n✅ **Number:** `{number}`\n📩 Waiting for OTP..."
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Block", callback_data=f"block_{number}")],
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"iso_{iso}")]
                ])
                await query.edit_message_text(msg, reply_markup=kb, parse_mode='Markdown')
            else:
                # যদি স্টক না থাকে
                await query.edit_message_text(
                    f"❌ **{iso.upper()}** স্টক আউট।\nপ্যানেল সার্ভারে এই মুহূর্তে নাম্বার নেই। আবার চেষ্টা করুন।", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Request Again", callback_data=f"iso_{iso}")]])
                )
        except:
            await query.edit_message_text("❌ সার্ভার কানেকশন এরর!")

# --- ৪. মেইন রানার ---
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
