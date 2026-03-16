import logging, requests, asyncio, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার কানেক্টিভিটি ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM STATUS: CUY PARAMETER ACTIVE"

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
GROUP_ID = -1003525081102 

ALLOWED_USERS = {6528471341: "Sojib", 8081334307: "Sojib Das", 8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"}

# প্যানেল অনুযায়ী নির্দিষ্ট দেশের নাম (cuy parameter এর জন্য)
COUNTRIES = {
    "🇺🇸 USA": "United States", "🇦🇴 Angola": "Angola", "🇳🇬 Nigeria": "Nigeria",
    "🇲🇿 Mozambique": "Mozambique", "🇲🇽 Mexico": "Mexico", "🇰🇪 Kenya": "Kenya",
    "🇹🇭 Thailand": "Thailand", "🇨🇲 Cameroon": "Cameroon", "🇪🇬 Egypt": "Egypt",
    "🇸🇳 Senegal": "Senegal", "🇱🇾 Libya": "Libya", "🇮🇳 India": "India",
    "🇷🇺 Russia": "Russia", "🇨🇬 Congo (cg)": "Congo", "🇦🇫 Afghanistan": "Afghanistan",
    "🇲🇷 Mauritania": "Mauritania", "🇹🇬 Togo": "Togo", "🇹🇳 Tunisia": "Tunisia",
    "🇦🇷 Argentina": "Argentina", "🇩🇿 Algeria": "Algeria", "🇲🇼 Malawi": "Malawi",
    "🇿🇲 Zambia": "Zambia", "🇻🇪 Venezuela": "Venezuela", "🇺🇬 Uganda": "Uganda",
    "🇬🇭 Ghana": "Ghana", "🇪🇹 Ethiopia": "Ethiopia", "🇩🇴 Dominican": "Dominican Republic",
    "🇨🇩 Congo (cd)": "Democratic Republic of the Congo"
}

# --- ৩. ওটিপি ও পিক-আপ লজিক ---
async def fetch_otp_task(context, chat_id, full_number, msg_id, user_id, cuy_name):
    num_only = ''.join(filter(str.isdigit, str(full_number)))
    
    # প্যানেলে নম্বরটি "Pick Up" করার জন্য setRelease কল
    pickup_url = f"https://api.durianrcs.com/out/ext_api/setRelease?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    requests.get(pickup_url, timeout=5)
    
    vcode_url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    
    for _ in range(60): 
        await asyncio.sleep(10)
        try:
            res = requests.get(vcode_url, timeout=10).json()
            if res.get('code') == 200 and res.get('data'):
                otp = res.get('data')
                
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Get New Number", callback_data=f"get_{cuy_name}")]])
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
                    text=f"✅ **OTP Received!**\n\n📱 **Num:** `{full_number}`\n🔑 **Code:** `{otp}`", 
                    reply_markup=kb, parse_mode='Markdown')
                
                await context.bot.send_message(chat_id=GROUP_ID, 
                    text=f"🔥 **New OTP Alert!**\n🔑 Code: `{otp}`\n📱 Num: `{full_number}`\n👤 User: {ALLOWED_USERS.get(user_id, 'Admin')}", 
                    parse_mode='Markdown')
                return
        except: pass
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! No OTP for `{full_number}`.")

# --- ৪. ইউজার ইন্টারফেস ---
def main_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Get Number")], [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")]], resize_keyboard=True)

def country_menu():
    buttons = []
    keys = list(COUNTRIES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(keys[i], callback_data=f"get_{COUNTRIES[keys[i]]}")]
        if i+1 < len(keys): row.append(InlineKeyboardButton(keys[i+1], callback_data=f"get_{COUNTRIES[keys[i+1]]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ALLOWED_USERS:
        await update.message.reply_text("🌑 **CS DARK BOT**\n`cuy` parameter enabled.", reply_markup=main_menu(), parse_mode='Markdown')

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_"):
        cuy = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Requesting **{cuy}** Number...")
        
        # এখানে 'cuy' প্যারামিটার ব্যবহার করা হয়েছে নির্দিষ্ট দেশের জন্য
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&cuy={cuy}&operator=any&force_country=1"
        
        try:
            res = requests.get(url, timeout=15).json()
            if res.get('code') == 200:
                number = res.get('data')
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Block/Cancel", callback_data=f"block_{number}_{cuy}")]])
                await query.edit_message_text(f"🌍 **Country:** {cuy}\n📱 **Number:** `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
                asyncio.create_task(fetch_otp_task(context, query.message.chat_id, number, sent_msg.message_id, query.from_user.id, cuy))
            else:
                await query.edit_message_text(f"❌ {cuy} Stock Out.", reply_markup=country_menu())
        except: await query.edit_message_text("❌ Connection Error!")

    elif query.data.startswith("block_"):
        data = query.data.split("_")
        num = ''.join(filter(str.isdigit, data[1]))
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num}&serial=2")
        await query.edit_message_text(f"🚫 Number `{data[1]}` Blocked.", reply_markup=country_menu())

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
