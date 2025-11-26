import telebot
from telebot import types
import json
import time
from datetime import datetime

BOT_TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"
ADMIN_GROUP_ID = 3205863933
ADMIN_ID = 1470389051

bot = telebot.TeleBot(BOT_TOKEN)

# Файлы хранений
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

users = load_json(USERS_FILE)
banned = load_json(BANNED_FILE)


# ----------------------------------------------------------
# СИСТЕМА НАГРАД
# ----------------------------------------------------------
AWARDS = {
    1: "🏅 Первая реплика",
    10: "🎖 10 сообщений",
    50: "🥇 50 сообщений",
    100: "🏆 100 сообщений",
    500: "💎 500 сообщений",
    1000: "👑 1000 сообщений",
}

SPECIAL_AWARDS = {
    "night": "🌙 Ночная смена",
    "long": "📜 Длинное сообщение",
    "week": "⏳ 7 дней активности",
    "first_photo": "📸 Первая фотография",
    "1000_chars": "📚 1000 символов",
    "streak_10": "🔥 Серия из 10 сообщений без перерыва"
}


def give_award(uid, award):
    if award not in users[uid]["awards"]:
        users[uid]["awards"].append(award)
        save_json(USERS_FILE, users)
        bot.send_message(uid, f"🔔 Ты получил награду: **{award}**")


# ----------------------------------------------------------
# НАЧАЛО / START
# ----------------------------------------------------------
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.from_user.id)

    if uid not in users:
        users[uid] = {
            "messages": 0,
            "awards": [],
            "first_time": time.time(),
            "last_msg": 0,
            "streak": 0
        }
        save_json(USERS_FILE, users)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✉ Написать сообщение", "🏆 Мои награды")

    bot.send_message(uid,
                     "👋 Приветствую! Я бот поддержки 'Шёпот Сердец'.\n\n"
                     "📝 Ты можешь написать сюда любое сообщение, и администрация ответит тебе.\n"
                     "👇 Нажми «Написать сообщение» чтобы начать.",
                     reply_markup=markup)

    give_award(uid, "🎉 Первая команда /start")


# ----------------------------------------------------------
# СИСТЕМА БАНА
# ----------------------------------------------------------
@bot.message_handler(commands=["ban"])
def ban_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = msg.text.split()[1]
        banned[uid] = True
        save_json(BANNED_FILE, banned)
        bot.reply_to(msg, f"🚫 Пользователь {uid} заблокирован")
    except:
        bot.reply_to(msg, "❌ Использование: /ban ID")


@bot.message_handler(commands=["unban"])
def unban_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = msg.text.split()[1]
        if uid in banned:
            del banned[uid]
            save_json(BANNED_FILE, banned)
        bot.reply_to(msg, f"✅ Пользователь {uid} разблокирован")
    except:
        bot.reply_to(msg, "❌ Использование: /unban ID")


@bot.message_handler(commands=["banned"])
def banned_list(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.reply_to(msg, "📍 Заблокированные:\n" + "\n".join(banned.keys()))


# ----------------------------------------------------------
# НАГРАДЫ
# ----------------------------------------------------------
@bot.message_handler(func=lambda m: m.text == "🏆 Мои награды")
def show_awards(msg):
    uid = str(msg.from_user.id)
    if not users[uid]["awards"]:
        bot.send_message(uid, "🏅 У тебя пока нет наград 😢")
    else:
        bot.send_message(uid, "🏆 Твои награды:\n\n" + "\n".join(users[uid]["awards"]))


# ----------------------------------------------------------
# ОСНОВНОЙ HANLDER ПЕРЕПИСКИ
# ----------------------------------------------------------
@bot.message_handler(content_types=["text", "photo", "voice", "video", "document"])
def forward(msg):
    uid = str(msg.from_user.id)

    if uid in banned:
        return bot.send_message(uid, "🚫 Ты заблокирован.")

    # Считаем сообщения
    users[uid]["messages"] += 1
    save_json(USERS_FILE, users)

    # Награды за количество
    if users[uid]["messages"] in AWARDS:
        give_award(uid, AWARDS[users[uid]["messages"]])

    # Ночная награда
    hour = datetime.now().hour
    if 0 <= hour <= 5:
        give_award(uid, SPECIAL_AWARDS["night"])

    # Длинный текст
    if msg.content_type == "text" and len(msg.text) > 300:
        give_award(uid, SPECIAL_AWARDS["long"])

    # Фото
    if msg.content_type == "photo":
        give_award(uid, SPECIAL_AWARDS["first_photo"])

    # 1000 символов суммарно
    if msg.content_type == "text":
        if len(msg.text) >= 1000:
            give_award(uid, SPECIAL_AWARDS["1000_chars"])

    # Пересылка в группу
    bot.forward_message(ADMIN_GROUP_ID, msg.chat.id, msg.message_id)

    # Ответ пользователю с уведомлением
    bot.send_message(ADMIN_GROUP_ID,
                     f"📩 Сообщение от @{msg.from_user.username} ({uid})")


# ----------------------------------------------------------
# Ответ администратора пользователю
# ----------------------------------------------------------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_GROUP_ID and m.reply_to_message)
def admin_reply(msg):
    text = msg.text
    uid_line = msg.reply_to_message.text.split("(")[-1].replace(")", "")

    try:
        uid = int(uid_line)
        bot.send_message(uid, f"💬 Администрация:\n{text}")
    except:
        pass


print("BOT STARTED")
bot.infinity_polling()
