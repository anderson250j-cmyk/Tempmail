import telebot
import requests
import time
import re
import random
import threading
from flask import Flask

# --- CONFIGURATION ---
API_TOKEN = '8639179377:AAHlTxPL8tTpU9HnycAJKd9CsGQF-IFvPS0'  # আপনার বট টোকেন দিন
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ১০টি প্রিমিয়াম ডোমেইন
DOMAINS = [
    "1secmail.com", "1secmail.org", "1secmail.net", 
    "vjuum.com", "laafd.com", "txcct.com", 
    "wuuvo.com", "icznn.com", "ezvmo.com", "dcctb.com"
]

# OTP খোঁজার ফাংশন
def extract_otp(text):
    otp = re.findall(r'\b\d{4,6}\b', text)
    return otp[0] if otp else None

# মেসেজ চেক করার ফাংশন
def wait_for_otp(chat_id, login, domain):
    bot.send_message(chat_id, "⏳ OTP-র জন্য অপেক্ষা করছি... (নতুন মেসেজ এলে জানানো হবে)")
    
    seen_messages = set()
    # প্রথমবার চেক করে বর্তমান মেসেজগুলো এড়িয়ে যাওয়া
    try:
        init_res = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}").json()
        for m in init_res:
            seen_messages.add(m['id'])
    except:
        pass

    # লুপ চালিয়ে চেক করা
    for _ in range(60):  # ৫ মিনিট পর্যন্ত চেক করবে (প্রতি ৫ সেকেন্ডে একবার)
        try:
            res = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}").json()
            for msg in res:
                if msg['id'] not in seen_messages:
                    # নতুন মেসেজ ডিটেইলস আনা
                    detail = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg['id']}").json()
                    otp = extract_otp(detail.get('textBody', ''))
                    
                    if otp:
                        msg_text = f"✅ **নতুন OTP এসেছে!**\n\n🔢 OTP: `{otp}`\n\n(কপি করতে ওটিপির ওপর ক্লিক করুন)"
                        bot.send_message(chat_id, msg_text, parse_mode="Markdown")
                    else:
                        bot.send_message(chat_id, f"📩 নতুন মেসেজ এসেছে, কিন্তু OTP পাওয়া যায়নি।\nবডি: {detail.get('textBody')[:100]}...")
                    return # মেসেজ পেলে লুপ বন্ধ
        except:
            pass
        time.sleep(5)
    
    bot.send_message(chat_id, "⚠️ ৫ মিনিট হয়ে গেছে, কিন্তু কোনো OTP আসেনি। আবার ট্রাই করতে মেইলটি সেন্ড করুন।")

# বটের কমান্ডগুলো
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("Generate New Mail 📧"))
    bot.send_message(message.chat.id, "স্বাগতম! নিচের বাটন টিপে মেইল তৈরি করুন।", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Generate New Mail 📧")
def generate(message):
    login = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
    domain = random.choice(DOMAINS)
    mail = f"{login}@{domain}"
    
    bot.send_message(message.chat.id, f"📫 আপনার মেইল:\n`{mail}`\n\n(কপি করতে মেইলের ওপর ক্লিক করুন)", parse_mode="Markdown")
    
    # আলাদা থ্রেডে OTP চেক শুরু করা যাতে বট হ্যাং না হয়
    threading.Thread(target=wait_for_otp, args=(message.chat.id, login, domain)).start()

@bot.message_handler(func=lambda message: "@" in message.text)
def activate_old(message):
    mail = message.text.strip()
    try:
        login, domain = mail.split('@')
        bot.send_message(message.chat.id, f"🔄 মেইল একটিভ করা হয়েছে: `{mail}`", parse_mode="Markdown")
        threading.Thread(target=wait_for_otp, args=(message.chat.id, login, domain)).start()
    except:
        bot.send_message(message.chat.id, "❌ সঠিক মেইল দিন।")

# Render-এর হেলথ চেক এর জন্য একটি ছোট সার্ভার
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)