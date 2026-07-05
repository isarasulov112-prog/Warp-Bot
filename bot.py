import os
import sqlite3
from telebot import TeleBot, types

TOKEN = os.getenv("TG_TOKEN", "8992833881:AAFyHiWToVXMzq1bvbRxmMfLRTWGjV2Ei8g")
bot = TeleBot(TOKEN)

DB_NAME = "vpn_business.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 50.0,
            referred_by INTEGER DEFAULT NULL,
            vpn_status INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

WIREGUARD_IOS = "https://apps.apple.com/us/app/wireguard/id1441195209"
WIREGUARD_ANDROID = "https://play.google.com/store/apps/details?id=com.wireguard.android"

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == user_id:
            referrer_id = None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute("INSERT INTO users (user_id, username, balance, referred_by) VALUES (?, ?, ?, ?)",
                       (user_id, username, 50.0, referrer_id))
        conn.commit()
        
        if referrer_id:
            cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            try:
                bot.send_message(referrer_id, f"🎉 По вашей реферальной ссылке зарегистрировался новый пользователь! Вам начислено 50 рублей.")
            except Exception:
                pass
                
    conn.close()

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ios = types.InlineKeyboardButton("🍏 iOS (iPhone)", callback_data="device_ios")
    btn_android = types.InlineKeyboardButton("🤖 Android", callback_data="device_android")
    btn_cabinet = types.InlineKeyboardButton("💼 Личный кабинет", callback_data="open_cabinet")
    markup.add(btn_ios, btn_android)
    markup.add(btn_cabinet)

    bot.send_message(
        user_id,
        f"👋 Привет, {username}! Добро пожаловать в наш профессиональный VPN бот.\n\n"
        f"🎁 За регистрацию вам начислено **50 рублей** на баланс!\n"
        f"Наш тариф: всего **8 рублей в день**.\n\n"
        f"Пожалуйста, выберите устройство, на котором будете использовать VPN:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("device_"))
def handle_device_selection(call):
    device = call.data.split("_")[1]
    link = WIREGUARD_IOS if device == "ios" else WIREGUARD_ANDROID
    
    markup = types.InlineKeyboardMarkup()
    btn_download = types.InlineKeyboardButton("📥 Скачать приложение", url=link)
    btn_cabinet = types.InlineKeyboardButton("💼 Перейти в личный кабинет", callback_data="open_cabinet")
    markup.add(btn_download)
    markup.add(btn_cabinet)
    
    text = (
        f"Отлично! Нажмите на кнопку ниже, чтобы скачать **WireGuard** для вашего устройства.\n\n"
        f"После установки перейдите в Личный Кабинет, чтобы получить ваш личный ключ активации VPN."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "open_cabinet")
def handle_cabinet(call):
    user_id = call.message.chat.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, vpn_status FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        balance, status = res
        status_text = "🟢 Активен" if status == 1 and balance >= 8 else "🔴 Неактивен (Недостаточно средств)"
    else:
        balance, status_text = 0, "🔴 Не найден"

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_topup = types.InlineKeyboardButton("💳 Пополнить баланс (Crypto Bot)", callback_data="topup_crypto")
    btn_get_config = types.InlineKeyboardButton("🔑 Получить ключ VPN (.conf)", callback_data="get_vpn_file")
    btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
    markup.add(btn_topup, btn_get_config, btn_back)

    cabinet_text = (
        f"💼 **ЛИЧНЫЙ КАБИНЕТ**\n\n"
        f"🆔 Ваш ID: `{user_id}`\n"
        f"💰 Ваш баланс: **{balance} рублей**\n"
        f"⚡ Статус VPN: {status_text}\n"
        f"降低 Ежедневное списание: 8 рублей\n\n"
        f"🔗 **Ваша реферальная ссылка:**\n`{ref_link}`\n\n"
        f"ℹ️ Отправьте эту ссылку друзьям! За каждого приглашенного пользователя вы получите **50 рублей** на ваш баланс."
    )
    bot.edit_message_text(cabinet_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ios = types.InlineKeyboardButton("🍏 iOS (iPhone)", callback_data="device_ios")
    btn_android = types.InlineKeyboardButton("🤖 Android", callback_data="device_android")
    btn_cabinet = types.InlineKeyboardButton("💼 Личный кабинет", callback_data="open_cabinet")
    markup.add(btn_ios, btn_android)
    markup.add(btn_cabinet)
    
    bot.edit_message_text("Пожалуйста, выберите устройство или перейдите в личный кабинет:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_vpn_file")
def send_vpn_config(call):
    user_id = call.message.chat.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()

    if balance < 8:
        bot.answer_callback_query(call.id, "❌ На балансе недостаточно средств (Минимум 8 рублей).", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🔑 Ваш ключ VPN создается...")
    
    config_data = "[Interface]\nPrivateKey = SAMPLE_PRIVATE_KEY\nAddress = 10.0.0.2/32\nDNS = 1.1.1.1\n\n[Peer]\nPublicKey = SAMPLE_PUBLIC_KEY\nEndpoint = engage.cloudflareclient.com:2408\nAllowedIPs = 0.0.0.0/0"
    
    filename = f"Warp_Portal_{user_id}.conf"
    with open(filename, "w") as f:
        f.write(config_data)
        
    with open(filename, "rb") as doc:
        bot.send_document(user_id, doc, caption="🚀 Ваш личный VPN ключ готов! Скачайте этот файл и импортируйте его в приложение WireGuard.")
        
    os.remove(filename)

@bot.callback_query_handler(func=lambda call: call.data == "topup_crypto")
def topup_crypto(call):
    bot.answer_callback_query(call.id, "💳 Запуск платежной системы...")
    bot.send_message(call.message.chat.id, "🔄 Интеграция с @CryptoBot выполняется. Скоро здесь появится ссылка на оплату.")

if __name__ == "__main__":
    print("🚀 Бот успешно запущен...")
    bot.infinity_polling()
