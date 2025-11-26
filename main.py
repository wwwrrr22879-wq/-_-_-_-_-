# main.py
import asyncio
import json
from datetime import datetime, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
import threading
import os
import random

# 🔐 Твои данные
TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Связь сообщения админа ↔ пользователь
reply_map = {}  # key: message_id админа, value: user_id

# 🚫 Заблокированные пользователи
banned_users = set()

# 🏆 Награды
REWARDS_FILE = "rewards.json"
if os.path.exists(REWARDS_FILE):
    with open(REWARDS_FILE, "r") as f:
        rewards_db = json.load(f)
else:
    rewards_db = {}  # {user_id: {"messages": 0, "rewards": []}}

# --- Сохраняем базу наград ---
def save_rewards():
    with open(REWARDS_FILE, "w") as f:
        json.dump(rewards_db, f, indent=2, ensure_ascii=False)

# --- Проверка и выдача наград ---
def check_rewards(user_id):
    now = datetime.now()
    user_data = rewards_db.setdefault(str(user_id), {"messages": 0, "rewards": []})
    user_data["messages"] += 1
    new_rewards = []

    # --- Основные награды ---
    if "Первое сообщение" not in user_data["rewards"]:
        user_data["rewards"].append("Первое сообщение")
        new_rewards.append("🏅 Первое сообщение")

    if user_data["messages"] >= 10 and "10 сообщений" not in user_data["rewards"]:
        user_data["rewards"].append("10 сообщений")
        new_rewards.append("🎖 10 сообщений")

    if user_data["messages"] >= 50 and "50 сообщений" not in user_data["rewards"]:
        user_data["rewards"].append("50 сообщений")
        new_rewards.append("🎗 50 сообщений")

    if user_data["messages"] >= 100 and "100 сообщений" not in user_data["rewards"]:
        user_data["rewards"].append("100 сообщений")
        new_rewards.append("🏆 100 сообщений")

    if user_data["messages"] >= 500 and "500 сообщений" not in user_data["rewards"]:
        user_data["rewards"].append("500 сообщений")
        new_rewards.append("🌟 500 сообщений")

    if user_data["messages"] >= 1000 and "1000 сообщений" not in user_data["rewards"]:
        user_data["rewards"].append("1000 сообщений")
        new_rewards.append("💎 1000 сообщений")

    # --- Ночная активность 22:00-08:00 ---
    if time(22, 0) <= now.time() or now.time() <= time(8, 0):
        if "Ночная активность" not in user_data["rewards"]:
            user_data["rewards"].append("Ночная активность")
            new_rewards.append("🌙 Ночная активность")

    # --- Время-секретная награда ---
    if now.hour == 10 and now.minute == 23:
        if "Секретная награда 10:23" not in user_data["rewards"]:
            user_data["rewards"].append("Секретная награда 10:23")
            new_rewards.append("🤫 Секретная награда 10:23")

    # --- Рандомные сюрпризы ---
    chance = random.randint(1, 1000)
    if chance == 777 and "Счастливый 777" not in user_data["rewards"]:
        user_data["rewards"].append("Счастливый 777")
        new_rewards.append("🍀 Счастливый 777")

    # --- Особые даты ---
    if now.month == 1 and now.day == 1 and "Новогодняя награда" not in user_data["rewards"]:
        user_data["rewards"].append("Новогодняя награда")
        new_rewards.append("🎉 Новогодняя награда")

    # --- Случайные уникальные награды ---
    if random.random() < 0.005 and "Редкая награда" not in user_data["rewards"]:
        user_data["rewards"].append("Редкая награда")
        new_rewards.append("💫 Редкая награда")

    save_rewards()
    return new_rewards

# --- Клавиатура ---
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Мои награды")
    return kb

# --- Команды ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши своё сообщение — и я передам его администраторам.\n"
        "Они обязательно ответят тебе с лучиком тепла ☀️",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# --- Команда Мои награды ---
@dp.message(lambda m: m.text == "Мои награды")
async def show_rewards(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = rewards_db.get(user_id, {"rewards": []})
    rewards_list = user_data["rewards"]
    if rewards_list:
        text = "🏆 Ваши награды:\n" + "\n".join(rewards_list)
    else:
        text = "⚠️ У вас пока нет наград."
    await message.answer(text, reply_markup=main_keyboard())

# --- Обработка сообщений ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # --- Проверка наград ---
    new_rewards = check_rewards(user_id)
    if new_rewards:
        await message.answer("🎉 Вы получили новые награды:\n" + "\n".join(new_rewards),
                             reply_markup=main_keyboard())

    # --- Користувач пише → пересилаємо адміну ---
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n"

        # Перевірка типу повідомлення
        if message.text:
            text += message.text
            sent = await bot.send_message(ADMIN_CHAT_ID, text)
        elif message.photo:
            sent = await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=text)
        elif message.video:
            sent = await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=text)
        elif message.voice:
            sent = await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=text)
        elif message.document:
            sent = await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=text)
        else:
            sent = await bot.send_message(ADMIN_CHAT_ID, text + "[неподдерживаемый тип]")

        reply_map[sent.message_id] = user_id

    # --- Адмін відповідає у reply → пересилаємо назад користувачу ---
    elif message.chat.id == ADMIN_CHAT_ID:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            user_id = reply_map[message.reply_to_message.message_id]
            try:
                if message.text:
                    await bot.send_message(user_id, f"💌 Ответ администратора:\n\n{message.text}")
                elif message.photo:
                    await bot.send_photo(user_id, message.photo[-1].file_id, caption="💌 Ответ администратора")
                elif message.video:
                    await bot.send_video(user_id, message.video.file_id, caption="💌 Ответ администратора")
                elif message.voice:
                    await bot.send_voice(user_id, message.voice.file_id, caption="💌 Ответ администратора")
                elif message.document:
                    await bot.send_document(user_id, message.document.file_id, caption="💌 Ответ администратора")
                else:
                    await bot.send_message(user_id, "💌 Ответ администратора [неподдерживаемый тип]")
            except:
                await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {user_id} заблокировал бота.")

# --- Flask для Keep Alive ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# --- Запуск бота ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
