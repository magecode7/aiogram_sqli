import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import aiosqlite
import time
# import OPi.GPIO as GPIO
# import time

# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(7, GPIO.OUT)

TOKEN = "XXXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXX"

FLAG = "flag{test}"
names = ["Kate", "Mark", FLAG, "James", "Test", "Alice"]

user_last_message = {}

async def init_db():
	async with aiosqlite.connect("database.db") as conn: # Init
		cursor = await conn.cursor()
		await cursor.execute("DELETE FROM users")
		await cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT)")
		await cursor.executemany("INSERT INTO users (name) VALUES (?)", [(name,) for name in names])
		await conn.commit()

async def search_name_db(name):
	async with aiosqlite.connect("database.db", uri=True) as conn:
		cursor = await conn.cursor()
		await cursor.execute(f"SELECT name FROM users WHERE name = '{name}'") # SQL injection (example=' OR name LIKE 'flag%)
		return await cursor.fetchone()

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart()) # Start init 
async def start(message: types.Message):
	name = message.from_user.full_name # pyright: ignore
	result = await search_name_db(name)

	if not result:
		async with aiosqlite.connect("database.db") as conn:
			cursor = await conn.cursor()
			await cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
			await conn.commit()
		await message.answer("Registered new user")
	await message.answer("Hello, enter the username to find the person")


@dp.message() # Name search
async def search_name(message: types.Message):
	name = message.text

	# Anti-flood protection
	user_id = message.from_user.id # pyright: ignore
	current_time = time.time()
	if user_id in user_last_message and current_time - user_last_message[user_id] < 1:
		await message.answer("Please slow down, you're sending messages too frequently.")
		return
	user_last_message[user_id] = current_time
	
	try:
		result = await search_name_db(name)
	except aiosqlite.Error as e:
		await message.answer(f"Error: {e}")
		return

	if result:
		await message.answer(f"User {result[0]} found in database")
		# GPIO.output(7, 1)
		# time.sleep(1)
		# GPIO.output(7, 0)
	else:
		await message.answer("User not found")

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.create_task(init_db())
	loop.run_until_complete(dp.start_polling(bot))
	