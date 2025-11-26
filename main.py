from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

TOKEN = "8398382607:AAFYlAxCH0SuJBovS3v9FMxiphT06VIVUjM"
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(commands=["start"])
async def start_test(message: types.Message):
    await message.answer("Привіт, я працюю!")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
