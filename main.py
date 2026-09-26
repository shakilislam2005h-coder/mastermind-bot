import telebot
import sqlite3
from google import genai

# ==================== ১. আপনার তথ্য ====================
BOT_TOKEN = "8994833168:AAHom9vjjfDF7SznmvUbJuuNe8pszm47vcI"
GEMINI_API_KEY = "AQ.Ab8RN6J8dkCPC5PRE3f5jp2L2hQZqSUh5zFdit4pAPsdVgknLA"
ADMIN_ID = 8734226927

BKASH_NUMBER = "01788280643"
NAGAD_NUMBER = "01788280643"
SHORTLINK_URL = "https://gplinks.in/xxxx"

# ==================== ২. বট ও জেমিনি সেটআপ ====================
bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# ডাটাবেজ তৈরি (SQLite)
conn = sqlite3.connect("mastermind_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referred_by INTEGER,
        refer_count INTEGER DEFAULT 0,
        daily_limit INTEGER DEFAULT 5,
        is_premium INTEGER DEFAULT 0
    )
''')
conn.commit()

# ==================== ৩. কমান্ড ও লজিক ====================

@bot.message_handler(commands=['start'])
def start_msg(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        referred_by = None
        if len(text_args) > 1 and text_args[1].isdigit():
            ref_id = int(text_args[1])
            if ref_id != user_id:
                referred_by = ref_id
                
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()

        if referred_by:
            cursor.execute("UPDATE users SET refer_count = refer_count + 1 WHERE user_id = ?", (referred_by,))
            conn.commit()
            
            cursor.execute("SELECT refer_count FROM users WHERE user_id = ?", (referred_by,))
            current_refs = cursor.fetchone()[0]
            
            if current_refs % 5 == 0:
                cursor.execute("UPDATE users SET daily_limit = daily_limit + 5 WHERE user_id = ?", (referred_by,))
                conn.commit()
                try:
                    bot.send_message(referred_by, "🎉 অভিনন্দন! আপনি ৫ জন বন্ধুকে ইনভাইট করেছেন। আপনাকে ৫টি অতিরিক্ত প্রশ্ন বোনাস দেওয়া হয়েছে!")
                except:
                    pass

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    welcome_text = (
        f"🤖 **MasterMind AI Bot**-এ আপনাকে স্বাগতম!\n\n"
        f"পড়াশোনা, গণিত, অ্যাসাইনমেন্ট, কোডিং বা পৃথিবীর যেকোনো প্রশ্ন লিখে পাঠান, AI আপনাকে সাথে সাথে উত্তর দেবে।\n\n"
        f"🎁 **ফ্রি বোনাস পান:**\n"
        f"আপনার রেফারেল লিংক দিয়ে ৫ জন বন্ধুকে জয়েন করালে আরও ৫টি ফ্রি প্রশ্ন পাবেন!\n"
        f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['addpremium'])
def add_premium(message):
    if message.from_user.id == ADMIN_ID:
        try:
            target_id = int(message.text.split()[1])
            cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (target_id,))
            conn.commit()
            bot.reply_to(message, f"✅ ইউজার `{target_id}` সফলভাবে প্রিমিয়াম করা হয়েছে!", parse_mode="Markdown")
            bot.send_message(target_id, "🎉 অভিনন্দন! আপনার প্রিমিয়াম সাবস্ক্রিপশন চালু হয়েছে। এখন থেকে আপনি আনলিমিটেড প্রশ্ন করতে পারবেন।")
        except:
            bot.reply_to(message, "সঠিক ফরম্যাট: `/addpremium USER_ID`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_ai(message):
    user_id = message.from_user.id
    cursor.execute("SELECT daily_limit, is_premium FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        daily_limit, is_premium = 5, 0
    else:
        daily_limit, is_premium = row

    # ৫টি প্রশ্ন শেষ হয়ে গেলে নোটিশ মেসেজ
    if is_premium == 0 and daily_limit <= 0:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        limit_finish_msg = (
            f"🚫 **আপনার আজকের ৫টি ফ্রি প্রশ্নের লিমিট শেষ হয়ে গেছে!**\n\n"
            f"আমি আবার আপনার সকল প্রশ্নের উত্তর দিতে পারবো, শুধু নিচের যেকোনো একটি উপায় অবলম্বন করুন:\n\n"
            f"✨ **উপায় ১: রেফার করে ফ্রি প্রশ্ন পান**\n"
            f"• আপনার এই রেফারেল লিংকটি শেয়ার করুন:\n`{ref_link}`\n"
            f"• আপনার লিংক দিয়ে ৫ জন বন্ধু জয়েন করলে আপনি আবার ৫টি ফ্রি প্রশ্ন করতে পারবেন!\n\n"
            f"🌐 **উপায় ২: শর্টলিংক / অ্যাডস দেখুন**\n"
            f"• এই লিংকে গিয়ে অ্যাড দেখে প্রশ্ন আনলক করুন: {SHORTLINK_URL}\n\n"
            f"-----------------------------------\n"
            f"👑 **উপায় ৩: প্রিমিয়াম সাবস্ক্রিপশন (আনলিমিটেড এক্সেস)**\n"
            f"• কোনো লিমিট ছাড়া ১ মাস আনলিমিটেড প্রশ্ন করতে প্রিমিয়াম প্যাক নিন (৫০ টাকা/মাস)!\n"
            f"• বিকাশ (Personal): `{BKASH_NUMBER}`\n"
            f"• নগদ (Personal): `{NAGAD_NUMBER}`\n\n"
            f"📌 *টাকা পাঠানোর পর আপনার Telegram ID (`{user_id}`) সহ অ্যাডমিনকে মেসেজ দিন।*"
        )
        bot.reply_to(message, limit_finish_msg, parse_mode="Markdown")
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # প্রথমে চেষ্টা করবে Gemini 3.8 Flash দিয়ে
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=message.text,
            )
        except Exception:
            # ৫০৩ বা সার্ভার প্রেসার থাকলে ব্যাকআপ মডেল দিয়ে চেষ্টা করবে
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=message.text,
            )
        
        if response.text:
            bot.reply_to(message, response.text)
            
            if is_premium == 0:
                cursor.execute("UPDATE users SET daily_limit = daily_limit - 1 WHERE user_id = ?", (user_id,))
                conn.commit()
        else:
            bot.reply_to(message, "আমি দুঃখিত, আপনার প্রশ্নটি বুঝতে পারিনি। অনুগ্রহ করে আবার লিখে পাঠান।")

    except Exception as e:
        print(f"Error Details: {e}")
        bot.reply_to(message, "সার্ভারে অতিরিক্ত চাপের কারণে একটু সমস্যা হচ্ছে। অনুগ্রহ করে কয়েক সেকেন্ড পর আবার চেষ্টা করুন।")

print("Bot is running smoothly with auto-fallback system...")
bot.infinity_polling()
