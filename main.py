# main.py
import asyncio, json, os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
import threading
from datetime import datetime

# ------------------ Твои данные ------------------
TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"
ADMIN_CHAT_ID = -1003120877184  # сюда пересылаем сообщения
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ------------------ База наград ------------------
if os.path.exists("rewards.json"):
    with open("rewards.json", "r", encoding="utf-8") as f:
        rewards_db = json.load(f)
else:
    rewards_db = {}

def save_rewards():
    with open("rewards.json", "w", encoding="utf-8") as f:
        json.dump(rewards_db, f, ensure_ascii=False, indent=2)

# ------------------ Забаненные пользователи ------------------
banned_users = set()

# ------------------ Связка сообщений ------------------
reply_map = {}  # key: message_id админа, value: user_id

# ------------------ Клавиатура ------------------
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Мои награды")
    return kb

# ------------------ Награды ------------------
def check_rewards(user_id):
    user_id = str(user_id)
    if user_id not in rewards_db:
        rewards_db[user_id] = {"messages": 0, "rewards": []}
    data = rewards_db[user_id]
    data["messages"] += 1
    new_rewards = []

    # Награды за количество сообщений
    if data["messages"] == 1:
        new_rewards.append("Первое сообщение ✅")
    if data["messages"] == 10:
        new_rewards.append("10 сообщений 🎉")
    if data["messages"] == 100:
        new_rewards.append("100 сообщений 🏆")
    if data["messages"] == 1000:
        new_rewards.append("1000 сообщений 🌟")
    
    # Награды за ночную активность
    hour = datetime.now().hour
    if 22 <= hour or hour < 8 and "Ночная смена 🌙" not in data["rewards"]:
        new_rewards.append("Ночная смена 🌙")
    
    # Секретные награды
    now_time = datetime.now().strftime("%H:%M")
    if now_time == "10:23" and "Секретная награда ⏰" not in data["rewards"]:
        new_rewards.append("Секретная награда ⏰")

    for r in new_rewards:
        data["rewards"].append(r)

    save_rewards()
    return new_rewards

# ------------------ Команды ------------------
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет, солнышко!\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши своё сообщение — и я передам его администраторам.\n"
        "Они обязательно ответят тебе с лучиком тепла ☀️",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(Command("ban"))
async def ban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может банить.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось определить пользователя.")
        return
    banned_users.add(user_id)
    await message.reply(f"✅ Пользователь {user_id} заблокирован.")

@dp.message(Command("unban"))
async def unban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может разбанить.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось определить пользователя.")
        return
    banned_users.discard(user_id)
    await message.reply(f"✅ Пользователь {user_id} разблокирован.")

@dp.message(Command("banned"))
async def banned_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может смотреть заблокированных.")
        return
    if banned_users:
        await message.reply("🚫 Заблокированные пользователи:\n" + "\n".join(map(str, banned_users)))
    else:
        await message.reply("✅ Нет заблокированных пользователей.")

# ------------------ Кнопка Мои награды ------------------
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

# ------------------ Обработка всех сообщений ------------------
@dp.message(lambda m: True)
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # Награды
    new_rewards = check_rewards(user_id)
    if new_rewards:
        await message.answer("🎉 Вы получили новые награды:\n" + "\n".join(new_rewards),
                             reply_markup=main_keyboard())

    # Пересылка админу
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n"
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

    # Ответ админу
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

# ------------------ Flask Keep Alive ------------------
app = Flask("")
@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# ------------------ Запуск бота ------------------
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
