import telebot
import requests
import time
import re
import random
from telebot import types

# এখানে আপনার Bot Token দিন
API_TOKEN = '8639179377:AAHlTxPL8tTpU9HnycAJKd9CsGQF-IFvPS0'
bot = telebot.TeleBot(API_TOKEN)

# 1secmail API ডোমেইন লিস্ট
DOMAINS = ["1secmail.com", "1secmail.org", "1secmail.net", "vjuum.com", "laafd.com", "txcct.com", "wuuvo.com", "icznn.com", "ezvmo.com", "dcctb.com"]

# ইউজার স্টেট সেভ করার জন্য
active_sessions = {}

def extract_otp(text):
    # ৪ থেকে ৮ ডিজিটের কোড খোঁজার জন্য
    otp = re.findall(r'\b\d{4,8}\b', text)
    return otp[0] if otp else None

def monitor_mail(chat_id, login, domain):
    bot.send_message(chat_id, f"🔍 মেইল এক্টিভ: `{login}@{domain}`\nOTP-র জন্য অপেক্ষা করছি...", parse_mode="Markdown")
    
    # এটি লুপের মাধ্যমে চেক করবে যতক্ষণ না মেসেজ আসে
    start_time = time.time()
    while active_sessions.get(chat_id) == f"{login}@{domain}":
        # ৫ মিনিট পর অটোমেটিক চেক বন্ধ হবে (সার্ভার লোড কমাতে)
        if time.time() - start_time > 300: 
            bot.send_message(chat_id, "⏰ ৫ মিনিট পার হয়ে গেছে। পুনরায় চেক করতে মেইলটি আবার পাঠান।")
            break
            
        try:
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
            msgs = requests.get(url).json()
            
            if msgs:
                msg_id = msgs[0]['id']
                msg_detail = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
                data = requests.get(msg_detail).json()
                
                content = data.get('textBody', '')
                otp = extract_otp(content)
                
                if otp:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Copy OTP 📋", callback_data=f"copy_{otp}"))
                    bot.send_message(chat_id, f"✅ আপনার OTP কোড: `{otp}`", parse_mode="Markdown", reply_markup=markup)
                else:
                    bot.send_message(chat_id, f"📩 নতুন মেসেজ এসেছে কিন্তু OTP পাওয়া যায়নি।\nবডি: {content[:100]}...")
                
                break # মেসেজ পেলে লুপ শেষ
        except:
            pass
        
        time.sleep(5)

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Generate New Mail 📧"))
    bot.send_message(message.chat.id, "স্বাগতম! 'Generate' বাটনে ক্লিক করে মেইল তৈরি করুন। যেকোনো পুরানো মেইল এখানে পেস্ট করলেও সেটি এক্টিভ হবে।", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Generate New Mail 📧")
def create_mail(message):
    # র‍্যান্ডম ডোমেইন সিলেক্ট করা
    login = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=10))
    domain = random.choice(DOMAINS)
    full_mail = f"{login}@{domain}"
    
    active_sessions[message.chat.id] = full_mail
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Copy Mail 📧", callback_data=f"copy_{full_mail}"))
    
    bot.send_message(message.chat.id, f"📫 আপনার টেম্প মেইল:\n`{full_mail}`", parse_mode="Markdown", reply_markup=markup)
    
    # মেসেজ মনিটরিং শুরু
    monitor_mail(message.chat.id, login, domain)

@bot.message_handler(func=lambda message: "@" in message.text)
def re_activate(message):
    try:
        mail = message.text.strip()
        login, domain = mail.split('@')
        if domain in DOMAINS:
            active_sessions[message.chat.id] = mail
            monitor_mail(message.chat.id, login, domain)
        else:
            bot.send_message(message.chat.id, "❌ এই ডোমেইনটি সাপোর্ট করে না।")
    except:
        bot.send_message(message.chat.id, "❌ সঠিক মেইল ফরম্যাট দিন।")

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_callback(call):
    data = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"কপি হয়েছে: {data}", show_alert=False)

bot.polling()