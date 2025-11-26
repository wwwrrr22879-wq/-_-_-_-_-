# main.py
import asyncio
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading

TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

reply_map = {}
banned_users = set()

def load_rewards():
    try:
        with open("rewards.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_rewards(data):
    with open("rewards.json", "w") as f:
        json.dump(data, f)

user_rewards = load_rewards()
all_users = set()   # список всіх юзерів

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🎖 Мои награды")]],
    resize_keyboard=True
)

broadcast_waiting = {}   # тимчасове очікування тексту розсилки

async def check_rewards(message: types.Message):
    user_id = str(message.from_user.id)
    now = datetime.now()

    all_users.add(message.from_user.id)   # зберігаємо користувача

    if user_id not in user_rewards:
        user_rewards[user_id] = {"messages": 0, "awards": []}

    user_rewards[user_id]["messages"] += 1
    count = user_rewards[user_id]["messages"]

    awards = user_rewards[user_id]["awards"]
    new_award = None

    if count == 1:
        new_award = "🥉 Перше повiдомлення"
    elif count == 10:
        new_award = "🥈 10 повiдомлень"
    elif count == 100:
        new_award = "🥇 100 повiдомлень"
    elif count == 1000:
        new_award = "🏆 1000 повiдомлень"

    if 22 <= now.hour or now.hour < 8:
        if "🌙 Ночная смена" not in awards:
            new_award = "🌙 Ночная смена"

    if now.hour == 10 and now.minute == 23:
        new_award = "🎁 Секретная награда 10:23"

    if new_award and new_award not in awards:
        awards.append(new_award)
        save_rewards(user_rewards)
        await message.answer(f"✨ Ты получил новую награду:\n**{new_award}** 🎉", parse_mode="Markdown")
        await bot.send_message(ADMIN_CHAT_ID, f"🆕 Награда у пользователя {user_id}: {new_award}")


@dp.message(Command("start"))
async def start(message: types.Message):
    all_users.add(message.from_user.id)
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши мне любое сообщение — и я передам его администраторам ❤️",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.message(lambda m: m.text == "🎖 Мои награды")
@dp.message(Command("награды"))
async def show_rewards(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in user_rewards or not user_rewards[user_id]["awards"]:
        await message.answer("У тебя пока нет наград 😢\nПиши — и будешь зарабатывать 💛")
        return

    text = "🎖 *Твои награды:*\n\n" + "\n".join(user_rewards[user_id]["awards"])
    await message.answer(text, parse_mode="Markdown")


# 📢 Розсилка
@dp.message(Command("send"))
async def start_broadcast(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ У тебя нет прав.")
        return

    broadcast_waiting[message.from_user.id] = True
    await message.answer("📝 Введи текст рассылки, и я отправлю его всем пользователям.")


async def send_broadcast(text):
    success = 0
    for uid in list(all_users):
        try:
            await bot.send_message(uid, f"📢 *Рассылка:*\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass
    return success


@dp.message()
async def handle_all(message: types.Message):
    user_id = message.from_user.id

    if message.from_user.id in broadcast_waiting:
        del broadcast_waiting[message.from_user.id]
        sent = await send_broadcast(message.text)
        await message.answer(f"📨 Рассылка завершена!\nОтправлено: **{sent}** пользователям.")
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"

    await check_rewards(message)

    if message.chat.id != ADMIN_CHAT_ID:
        sent = await bot.send_message(ADMIN_CHAT_ID, f"💬 Сообщение от {username} (ID: {user_id}):\n\n{message.text}")
        reply_map[sent.message_id] = user_id
    else:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            uid = reply_map[message.reply_to_message.message_id]
            await bot.send_message(uid, f"💌 Ответ администратора:\n\n{message.text}")


app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
