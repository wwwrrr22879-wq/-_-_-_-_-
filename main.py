# main.py
import asyncio
import json
from datetime import datetime, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os

# ===================== ВАШІ ДАНІ =====================
TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"  # <-- встав свій токен
ADMIN_CHAT_ID =  8398382607 # <-- твій ID або групи адміністрації
OWNER_ID = 1470389051
DATA_FILE = "rewards_db.json"
# ======================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Відповідність повідомлення адміна ↔ користувач
reply_map = {}

# 🚫 Заблоковані користувачі
banned_users = set()

# 🏆 Нагороди
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        rewards_db = json.load(f)
else:
    rewards_db = {"users": {}}

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(rewards_db, f, indent=4)

def check_rewards(user_id, message_time=None):
    user = rewards_db["users"].setdefault(str(user_id), {"messages": 0, "rewards": []})
    user["messages"] += 1
    msg_count = user["messages"]
    new_rewards = []

    # Первое сообщение
    if msg_count == 1 and "🏅 Первое сообщение" not in user["rewards"]:
        user["rewards"].append("🏅 Первое сообщение")
        new_rewards.append("🏅 Первое сообщение")

    # За количество сообщений
    milestones = {
        10: "🎉 10 сообщений",
        25: "🥳 25 сообщений",
        50: "🎊 50 сообщений",
        100: "🏆 100 сообщений",
        250: "💎 250 сообщений",
        500: "💎💎 500 сообщений",
        1000: "🌟 1000 сообщений",
        2500: "🌟🌟 2500 сообщений",
        5000: "🌟🌟🌟 5000 сообщений"
    }
    if msg_count in milestones and milestones[msg_count] not in user["rewards"]:
        user["rewards"].append(milestones[msg_count])
        new_rewards.append(milestones[msg_count])

    # Ночная смена
    if message_time:
        if time(22,0) <= message_time.time() or message_time.time() <= time(8,0):
            if "🌙 Ночная смена" not in user["rewards"]:
                user["rewards"].append("🌙 Ночная смена")
                new_rewards.append("🌙 Ночная смена")

        # Специальные часы
        special_times = [
            ("10:23", "⏰ Написал в 10:23"),
            ("00:00", "🌌 Сообщение в полночь"),
            ("12:34", "🕐 Время 12:34"),
            ("03:21", "🌌 Тайная ночная пора")
        ]
        for t_str, reward_name in special_times:
            t_hour, t_min = map(int, t_str.split(":"))
            if message_time.time().hour == t_hour and message_time.time().minute == t_min:
                if reward_name not in user["rewards"]:
                    user["rewards"].append(reward_name)
                    new_rewards.append(reward_name)

    save_db()
    return new_rewards

# ===================== Клавиатура =====================
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Мои награды")
    return kb

# ===================== Команды =====================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет! Я — бот *Шёпот сердец 💌*\n"
        "Напиши своё сообщение — я передам его администрации.\n"
        "Они обязательно ответят тебе с теплом ☀️",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(lambda m: m.text == "Мои награды")
async def show_rewards(message: types.Message):
    user_id = str(message.from_user.id)
    user = rewards_db["users"].get(user_id)
    if not user or not user.get("rewards"):
        await message.answer("🏅 У вас пока нет наград.")
        return
    text = "🏆 Ваши награды:\n" + "\n".join(user["rewards"])
    await message.answer(text)

# ===================== Бан/Разбан =====================
@dp.message(Command("ban"))
async def ban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может банить.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите забанить.")
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
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите разбанить.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось определить пользователя.")
        return
    banned_users.discard(user_id)
    await message.reply(f"✅ Пользователь {user_id} разбанен.")

@dp.message(Command("banned"))
async def banned_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может просматривать заблокированных.")
        return
    if banned_users:
        await message.reply("🚫 Заблокированные пользователи:\n" + "\n".join(map(str, banned_users)))
    else:
        await message.reply("✅ Заблокированных пользователей нет.")

# ===================== Пересылка сообщений =====================
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # Награды
    check_rewards(user_id, datetime.now())

    # Отправка админу
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n"
        if message.text:
            sent = await bot.send_message(ADMIN_CHAT_ID, text + message.text)
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

    # Ответ администратора
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

# ===================== Запуск бота =====================
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
