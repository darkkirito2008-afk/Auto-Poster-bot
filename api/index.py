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

        image_path = "welcome.jpg" 
        caption_text = (
            "🎉 <b>Success! Account Verified.</b>\n\n"
            "Welcome to the team! You can now send me any image, "
            "and I will instantly convert it into a watermarked poster for your channel."
        )

        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                bot.send_photo(chat_id=call.message.chat.id, photo=photo, caption=caption_text, parse_mode="HTML")
        else:
            bot.send_message(chat_id=call.message.chat.id, text=caption_text, parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ You still haven't joined the channel!", show_alert=True)

# 4. Poster Generation Image Processing
@bot.message_handler(content_types=['photo'])
def handle_poster_generation(message):
    user_id = message.from_user.id
    if not check_user_joined(user_id):
        bot.send_message(message.chat.id, "❌ Action Blocked!", reply_markup=get_force_sub_keyboard())
        return

    status_msg = bot.reply_to(message, "⏳ <i>Processing image and building poster...</i>", parse_mode="HTML")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_path = "/tmp/input_image.jpg"
        output_path = "/tmp/output_poster.jpg"
        
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        img = Image.open(input_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        font_size = max(20, int(height * 0.04)) 
        font = ImageFont.load_default()

        watermark_text = " @Anicore_Animes "
        draw.rectangle([(0, height - font_size - 20), (width, height)], fill=(0, 0, 0, 160))
        draw.text((20, height - font_size - 10), watermark_text, fill=(255, 255, 255), font=font)
        img.save(output_path, "JPEG", quality=95)

        with open(output_path, 'rb') as poster:
            bot.send_photo(message.chat.id, poster, caption="<b>✅ Poster Created Successfully!</b>", parse_mode="HTML")
            
        bot.delete_message(message.chat.id, status_msg.message_id)
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

    except Exception as e:
        bot.edit_message_text(f"❌ Poster generation failed: {e}", message.chat.id, status_msg.message_id)
