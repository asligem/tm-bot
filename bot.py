import telebot
from telebot import types
import google.generativeai as genai
from PIL import Image
import io

# اطلاعات اختصاصی شما (تنظیم‌شده)
TOKEN = "8920863311:AAHpra6BEQ_kW_XCe9I03MCkdYEHwmTn-tE"
GEMINI_API_KEY = "AQ.Ab8RN6I5TiB0_ejG5q6p7N-Wz05kB_unLqrcYNKTSw4AP6OOFw"
ADMIN_ID = 7963578223

CHANNEL_USERNAME = "@Tm_Artwork"
CARD_NUMBER = "6219861956736424"
ADMIN_NAME = "سید مصطفی جعفری بهمنیاری"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

users_db = {}
user_state = {}

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except:
        pass
    return False

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💳 خرید اشتراک", "💰 کیف پول و موجودی")
    markup.add("💸 برداشت پول", "📞 پشتیبانی")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت در کانال TM", url="https://t.me/Tm_Artwork"))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data="check_join"))
        bot.send_message(message.chat.id, "سلام! برای استفاده از ربات TM باید اول عضو کانال زیر بشی:\n@Tm_Artwork", reply_markup=markup)
        return

    if user_id not in users_db:
        users_db[user_id] = {"sub": False, "slots": 0, "balance": 0, "level": 1, "pending_withdraw": False}

    bot.send_message(message.chat.id, "خوش اومدی قهرمان! 🎨\nعکس تامنیل یا گرافیکت رو بفرست و زیرش بنویس **گرافیک** تا هوش مصنوعی سخت‌گیرانه بررسی‌اش کنه.", reply_markup=get_main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check(call):
    if is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "عضویت تایید شد!")
        bot.send_message(call.message.chat.id, "عضویتت تایید شد! حالا دستور /start رو بفرست.")
    else:
        bot.answer_callback_query(call.id, "هنوز توی کانال عضو نشدی!", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "💳 خرید اشتراک")
def buy_sub(message):
    text = (
        f"💳 **خرید اشتراک ویژه TM**\n\n"
        f"مبلغ: **۱۵۰,۰۰۰ تومان**\n"
        f"شماره کارت: `{CARD_NUMBER}`\n"
        f"به نام: **{ADMIN_NAME}**\n\n"
        f"لطفاً مبلغ رو کارت‌به‌کارت کن و **عکس رسید** رو همینجا بفرست تا برای ادمین ارسال بشه!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 پشتیبانی")
def support(message):
    text = (
        f"📞 **ارتباط با پشتیبانی TM**\n\n"
        f"برای هرگونه سوال، مشکل یا پیگیری می‌توانید به آیدی زیر پیام دهید:\n"
        f"👉 @TmArtwork_pv"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "💰 کیف پول و موجودی")
def wallet(message):
    user_id = message.from_user.id
    data = users_db.get(user_id, {"slots": 0, "balance": 0, "level": 1, "sub": False})
    sub_status = "✅ فعال" if data["sub"] else "❌ غیرفعال (برای کسب جایزه باید اشتراک بخوری)"
    
    text = (
        f"📊 **حساب کاربری شما در TM**\n\n"
        f"💎 وضعیت اشتراک: {sub_status}\n"
        f"⭐ لول فعلی: Level {data['level']}\n"
        f"🎯 سهمیه تامنیل‌های جایزه‌دار: {data['slots']} عدد\n"
        f"💰 موجودی قابل برداشت: {data['balance']} تومان"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "💸 برداشت پول")
def withdraw_request(message):
    user_id = message.from_user.id
    user_data = users_db.get(user_id, {"balance": 0, "sub": False, "pending_withdraw": False})
    
    if not user_data["sub"]:
        bot.send_message(message.chat.id, "❌ شما اشتراک فعال ندارید! ابتدا باید اشتراک ویژه تهیه کنید تا بتوانید موجودی خود را برداشت کنید.")
        return

    if user_data["pending_withdraw"]:
        bot.send_message(message.chat.id, "⏳ شما یک درخواست برداشت در حال انتظار دارید! لطفاً صبر کنید تا توسط ادمین واریز شود.")
        return

    if user_data["balance"] <= 0:
        bot.send_message(message.chat.id, "❌ موجودی کیف پول شما صفر است و امکان برداشت ندارید.")
        return

    user_state[user_id] = {"step": "waiting_amount", "balance": user_data["balance"]}
    bot.send_message(message.chat.id, f"💰 موجودی فعلی شما: {user_data['balance']} تومان\n\nلطفاً **مبلغی** که می‌خواهید برداشت کنید را به تومان وارد کنید:")

@bot.message_handler(func=lambda message: message.from_user.id in user_state)
def handle_user_steps(message):
    user_id = message.from_user.id
    state = user_state[user_id]

    if state["step"] == "waiting_amount":
        try:
            amount = int(message.text)
            if amount <= 0:
                bot.send_message(message.chat.id, "❌ مبلغ باید بیشتر از صفر باشد. دوباره وارد کنید:")
                return
            if amount > state["balance"]:
                bot.send_message(message.chat.id, f"❌ مبلغ درخواستی بیشتر از موجودی شماست! (موجودی: {state['balance']} تومان)")
                return

            state["amount"] = amount
            state["step"] = "waiting_card"
            bot.send_message(message.chat.id, "💳 عالی! حالا **شماره کارت** یا شبای بانکی خود را برای واریز وجه ارسال کنید:")
        except ValueError:
            bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد صحیح وارد کنید:")

    elif state["step"] == "waiting_card":
        card_info = message.text
        amount = state["amount"]
        del user_state[user_id]

        users_db[user_id]["pending_withdraw"] = True

        bot.send_message(message.chat.id, "⏳ درخواست برداشت شما ثبت شد و برای ادمین ارسال گردید.")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ پول واریز شد (اعلام به کاربر)", callback_data=f"paid_{user_id}_{amount}"))
        
        admin_text = (
            f"💸 **درخواست برداشت وجه جدید!**\n\n"
            f"👤 کاربر: {message.from_user.first_name} (ID: `{user_id}`)\n"
            f"💵 مبلغ درخواستی: **{amount} تومان**\n"
            f"📌 شماره کارت مقصد: `{card_info}`"
        )
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "دستور ادمین گرامی دریافت شد.")
        return

    if not is_member(user_id):
        bot.send_message(message.chat.id, "اول باید توی کانال `@Tm_Artwork` عضو بشی!")
        return

    caption = message.caption if message.caption else ""
    
    if "گرافیک" in caption:
        handle_graphic_ai(message)
    else:
        bot.send_message(message.chat.id, "⏳ رسید شما برای ادمین ارسال شد. پس از بررسی، اشتراک شما فعال خواهد شد.")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تأیید اشتراک", callback_data=f"approve_{user_id}"),
            types.InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_{user_id}")
        )
        forward_caption = f"🔔 **رسید جدید واریز وجه!**\n👤 کاربر: {message.from_user.first_name} (ID: `{user_id}`)"
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=forward_caption, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return

    data = call.data

    if data.startswith("approve_") or data.startswith("reject_"):
        action, target_user_id = data.split("_")
        target_user_id = int(target_user_id)

        if target_user_id not in users_db:
            users_db[target_user_id] = {"sub": False, "slots": 0, "balance": 0, "level": 1, "pending_withdraw": False}

        if action == "approve":
            users_db[target_user_id]["sub"] = True
            users_db[target_user_id]["slots"] += 10 
            
            bot.answer_callback_query(call.id, "اشتراک با موفقیت تأیید شد!")
            try:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **وضعیت: تأیید و فعال شد**", parse_mode="Markdown")
            except:
                pass
            
            bot.send_message(target_user_id, "🎉 **تبریک!** رسید شما تأیید شد و **۱۰ سهمیه بررسی تامنیل جایزه‌دار** به حسابتان اضافه شد!", reply_markup=get_main_keyboard(target_user_id))
        
        elif action == "reject":
            bot.answer_callback_query(call.id, "رسید رد شد.")
            try:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **وضعیت: رد شد**", parse_mode="Markdown")
            except:
                pass
            bot.send_message(target_user_id, "❌ متأسفانه رسید واریزی شما توسط ادمین تأیید نشد.")

    elif data.startswith("paid_"):
        parts = data.split("_")
        target_user_id = int(parts[1])
        amount = int(parts[2])

        if target_user_id in users_db:
            if users_db[target_user_id]["balance"] >= amount:
                users_db[target_user_id]["balance"] -= amount
            users_db[target_user_id]["pending_withdraw"] = False

        bot.answer_callback_query(call.id, "اعلام واریز وجه به کاربر ارسال شد!")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + "\n\n✅ **وضعیت: وجه به حساب کاربر واریز شد**", parse_mode="Markdown")
        except:
            pass

        bot.send_message(target_user_id, f"💸 **مبلغ {amount} تومان جایزه شما به کارت‌تان واریز شد!**")

def handle_graphic_ai(message):
    user_id = message.from_user.id
    processing_msg = bot.send_message(message.chat.id, "⏳ در حال بررسی سخت‌گیرانه تامنیل توسط هوش مصنوعی TM...")

    try:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image = Image.open(io.BytesIO(downloaded_file))

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            "تو یک منتقد بسیار سخت‌گیر تامنیل یوتیوب و گرافیک هستی. "
            "این عکس را به دقت تحلیل کن و پاسخ را دقیقا با این فرمت بده:\n"
            "نمره: [یک عدد صحیح سخت‌گیرانه از 1 تا 10]\n"
            "نقاط قوت: [مزایای کار به صورت کوتاه]\n"
            "ایرادات: [عیب و ایرادهای دقیق گرافیکی و تامنیل]"
        )
        
        response = model.generate_content([image, prompt])
        ai_text = response.text
        
        score = 5
        for line in ai_text.split('\n'):
            if "نمره:" in line:
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    score = int(numbers[0])

        user = users_db.get(user_id, {"sub": False, "slots": 0, "balance": 0, "level": 1, "pending_withdraw": False})
        
        if score >= 8:
            user["level"] += 1

        reward_text = "\n❌ تامنیل به حد نصاب جایزه نرسید."
        
        if user["sub"] and user["slots"] > 0:
            user["slots"] -= 1
            if score >= 8:
                prize = 30000
                user["balance"] += prize
                reward_text = f"\n🎁 **فوق‌العاده! تامنیلت خیلی خفن بود و {prize} تومان جایزه گرفتی!**"
        elif not user["sub"] and score >= 8:
            reward_text = f"\n⚠️ تامنیلت نمره عالی گرفت ولی چون اشتراک نداری، جایزه نقدی تعلق نگرفت! (اول اشتراک بخر)"

        result_text = (
            f"🎨 **تحلیل تخصصی تامنیل (TM)**\n\n"
            f"{ai_text}\n\n"
            f"📈 **لول کاربر:** Level {user['level']}"
            f"{reward_text}"
        )
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.send_message(message.chat.id, result_text, parse_mode="Markdown")

    except Exception as e:
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.send_message(message.chat.id, "خطایی در پردازش عکس رخ داد. لطفاً دوباره تلاش کن.")

bot.infinity_polling()
