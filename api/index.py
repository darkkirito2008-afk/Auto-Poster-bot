import os
import telebot
from flask import Flask, request
from PIL import Image, ImageDraw, ImageFont
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException

# Configuration Settings
BOT_TOKEN = "8771629849:AAEdtO2SerdffCHtUAjgZIzXhwlkBkiegwE"
FORCE_SUB_CHANNEL = "@Anicore_Animes" 
CHANNEL_INVITE_LINK = "https://t.me/Anicore_Animes"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# 1. Helper function to check channel subscription status
def check_user_joined(user_id):
    try:
        member = bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except ApiTelegramException:
        return False

def get_force_sub_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK))
    markup.add(InlineKeyboardButton("🔄 Verified / Try Again", callback_data="check_sub"))
    return markup

# 2. Vercel Webhook Listener
@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot Webhook Server is Alive!', 200

# 3. Message Handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if not check_user_joined(user_id):
        bot.send_message(
            message.chat.id, 
            "❌ <b>Access Denied!</b>\n\nYou must join our channel to use this bot.", 
            parse_mode="HTML", 
            reply_markup=get_force_sub_keyboard()
        )
        return

    bot.send_message(
        message.chat.id,
        "👋 <b>Welcome to the Anime Poster Maker!</b>\n\nJust send me any image, and I will automatically watermark it with your channel branding link!",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_callback(call):
    user_id = call.from_user.id
    if check_user_joined(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!", show_alert=True)
        try: 
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception: 
            pass

        # Direct Catbox URL Configuration
        image_url = "https://files.catbox.moe/sla8rd.jpg" 
        caption_text = (
            "🎉 <b>Success! Account Verified.</b>\n\n"
            "Welcome to the team! You can now send me any image, "
            "and I will instantly convert it into a watermarked poster for your channel."
        )

        try:
            bot.send_photo(chat_id=call.message.chat.id, photo=image_url, caption=caption_text, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id=call.message.chat.id, text=caption
