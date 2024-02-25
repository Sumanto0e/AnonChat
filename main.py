import config
from config import RegState
from config import SetName, SetAge, SetSex, SetCountry, SetCity, SetId, SetOpSex
import keyboards as kb
from db import DbWorker

import logging
import asyncio
from datetime import datetime, timedelta
from aiopayok import Payok

from aiogram import Bot
from aiogram.types import ParseMode
from aiogram.types.message import ContentTypes
from aiogram.utils import executor, exceptions
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

db = DbWorker(config.DB)

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(filename="all_log.log", level=logging.INFO, format='%(asctime)s - %(levelname)s -%(message)s')
warning_log = logging.getLogger("warning_log")
warning_log.setLevel(logging.WARNING)
fh = logging.FileHandler("warning_log.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
warning_log.addHandler(fh)

pay = Payok(api_id=config.API_ID, api_key=config.API_KEY, secret_key=config.SECRET_KEY, shop=config.SHOP_ID)


# Регистрация

@dp.message_handler(lambda message: message.text == '🔙 Go to main')
@dp.message_handler(commands=['start'])
async def start(message):
	try:
		db.set_state(None, message.from_user.id)
		sp = message.text.split()
		if len(sp) > 1 and not db.user_exists(message.from_user.id):
			user_id = sp[1]
			db.edit_refs(1, user_id)
			db.edit_points(+200, user_id)
			if bool(db.get_notifications(user_id)[0]):
				await bot.send_message(user_id, 'Someone joins the bot using your link!')
				if db.get_refs(user_id)[0] % 10 == 0:
					await bot.send_message(user_id, 'You can turn off notifications about new referrals in the settings.')
		if not db.user_exists(message.from_user.id):
			await message.answer(f"🎉Welcome to ONS🎉\n"
			                     f"Before you start communicating, you must register.\n"
			                     f"After registration you will receive <b>VIP for a month for free!</b>\n"
			                     f"Start registration - /daftar\n"
			                     f"Chat rules - /rules", parse_mode='HTML')
		else:
			await message.answer(f'Halo, {db.get_name(message.from_user.id)[0]}', reply_markup=kb.main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['help'])
async def help(message):
	try:
		await message.answer(f'/start - Memulai\n'
		                     f'/rules - Peraturan\n'
		                     f'/search - Find a partner\n'
		                     f'/stop - stop chat\n'
		                     f'/vip - VIP\n'
		                     f'/ref - referal'
				     f'/trade - trade')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['daftar'])
async def registrate(message):
	if not db.user_exists(message.from_user.id):
		await message.answer("Enter your name.")
		await RegState.name.set()


@dp.message_handler(state=RegState.name)
async def set_name(message, state: FSMContext):
	await state.update_data(name=message.text)
	await message.answer("Now enter your gender (M/F).")
	await RegState.sex.set()


@dp.message_handler(state=RegState.sex)
async def set_sex(message, state: FSMContext):
	if message.text == 'м' or message.text == 'M':
		await state.update_data(sex='male')
		await state.update_data(op_sex='female')
		await message.answer("Now enter your age.")
		await RegState.age.set()
	elif message.text == 'F' or message.text == 'F':
		await state.update_data(sex='female')
		await state.update_data(op_sex='male')
		await message.answer("Now enter your age.")
		await RegState.age.set()
	else:
		await message.reply("You entered the wrong value, type it with numbers, please re-enter it.")


@dp.message_handler(state=RegState.age)
async def set_age(message, state: FSMContext):
	if 5 < int(message.text) < 100:
		await state.update_data(age=message.text)
		await message.answer("What country do you live in?")
		await RegState.country.set()
	else:
		await message.reply("You entered the wrong number, please enter it again.")


@dp.message_handler(state=RegState.country)
async def set_country(message, state: FSMContext):
	await state.update_data(country=message.text)
	await message.answer("What city do you live in?")
	await RegState.city.set()


@dp.message_handler(state=RegState.city)
async def set_city(message, state: FSMContext):
	await state.update_data(city=message.text)
	await message.answer("Thank you for signing up! You can now search - /search.",
	                     reply_markup=kb.main_kb)
	data = await state.get_data()
	db.new_user(data['name'], data['age'], data['sex'], data['country'], data['city'], message.from_user.id)
	await state.finish()
	if db.get_vip_ends(message.from_user.id)[0] is None:
		db.edit_vip_ends((datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y %H:%M'),
		                 message.from_user.id)


@dp.message_handler(commands=['rules'])
@dp.message_handler(lambda message: message.text == 'Rules 📖')
async def rules(message):
	try:
		await message.answer(f'<b>Not allowed in chat:</b>\n'
		                     f'1) Any mention of psychoactive substances (drugs).\n'
		                     f'2) Change, distribution of any 18+ materials\n'
		                     f'3) Any advertising, spam, any sales.\n'
		                     f'4) Attacking behavior.\n'
		                     f'5) Any action that violates Telegram rules.\n',
		                     parse_mode='HTML', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


# Настройки


@dp.message_handler(commands=['edit_name'])
@dp.callback_query_handler(lambda call: call.data == 'name')
async def edit_name(call):
	await bot.answer_callback_query(call.id, 'Enter your name:')
	db.set_state(SetName.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetName.waiting.value)
async def editing_name(message):
	try:
		if str(message.from_user.id) in config.ADMINS:
			await bot.send_message(int(message.text), f'VIP duration successfully added 1 day')
			await bot.send_message(5458705482, f'VIP duration is successful {message.text} added 1 day')
			if db.get_vip_ends(int(message.text))[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), int(message.text))
       
			else:
				db.edit_vip_ends(
					(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
			 	 	 timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), message.text)
		else:
			db.edit_name(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Name saved!", reply_markup=kb.main_kb)
			db.set_state(SetName.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_age'])
@dp.callback_query_handler(lambda call: call.data == 'age')
async def edit_age(call):
	await bot.answer_callback_query(call.id, 'Enter age:')
	db.set_state(SetAge.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetAge.waiting.value)
async def editing_age(message):
	try:
		if str(message.from_user.id) in config.ADMINS:
			await bot.send_message(int(message.text), f'VIP duration successfully added 7 day')
			await bot.send_message(5458705482, f'Durasi VIP berhasil {message.text} ditambahkan 7 hari')
			if db.get_vip_ends(int(message.text))[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
			else:
				db.edit_vip_ends(
					(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
			 	 	 timedelta(days=7)).strftime('%d.%m.%Y %H:%M'), message.text)
		else:
			db.edit_age(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Age saved!", reply_markup=kb.main_kb)
			db.set_state(SetAge.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_sex'])
@dp.callback_query_handler(lambda call: call.data == 'sex')
async def edit_sex(call):
	await call.message.edit_reply_markup(reply_markup=kb.sex_kb)
	await bot.answer_callback_query(call.id, 'Select gender:')
	db.set_state(SetSex.waiting.value, call.from_user.id)


@dp.callback_query_handler(lambda call: call.data == 'male' or call.data == 'female')
async def editing_sex(call):
	try:
		if call.data == 'male':
			db.edit_sex('male', call.from_user.id)
			db.edit_op_sex('female', call.from_user.id)
			await bot.send_message(call.from_user.id, "Gender is saved!", reply_markup=kb.main_kb)
			await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
			db.set_state(SetSex.nothing.value, call.from_user.id)
		elif call.data == 'female':
			db.edit_sex('female', call.from_user.id)
			db.edit_op_sex('male', call.from_user.id)
			await bot.send_message(call.from_user.id, "Gender is saved!", reply_markup=kb.main_kb)
			await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
			db.set_state(SetSex.nothing.value, call.from_user.id)
		else:
			await call.reply("You entered the wrong value, type 'male' or 'female' please enter it again")
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_country'])
@dp.callback_query_handler(lambda call: call.data == 'country')
async def edit_country(call):
	await bot.answer_callback_query(call.id, 'Enter your country:')
	db.set_state(SetCountry.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetCountry.waiting.value)
async def editing_country(message):
	try:
		if str(message.from_user.id) in config.ADMINS:
			await bot.send_message(int(message.text), f'VIP duration successfully added 31 days')
			await bot.send_message(5458705482, f'VIP duration is successful {message.text} added 31 days')
			if db.get_vip_ends(int(message.text))[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
			else:
				db.edit_vip_ends(
					(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
			 	 	 timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), message.text)
		else:
			db.edit_country(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Country saved!", reply_markup=kb.main_kb)
			db.set_state(SetCountry.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_city'])
@dp.callback_query_handler(lambda call: call.data == 'city')
async def edit_city(call):
	await bot.answer_callback_query(call.id, 'Enter the city:')
	db.set_state(SetCity.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetCity.waiting.value)
async def editing_city(message):
	try:
		db.edit_city(message.text, message.from_user.id)
		await bot.send_message(message.from_user.id, "This city has been saved!", reply_markup=kb.main_kb)
		db.set_state(SetCity.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)

@dp.message_handler(commands=['profile'])
@dp.message_handler(lambda message: message.text == 'Profil 👤')
async def profile(message):
	try:
		sex = 'Unknown'
		user_id = message.from_user.id
		if db.get_sex(user_id)[0] == 'male':
			sex = 'male'
		elif db.get_sex(user_id)[0] == 'female':
			sex = 'female'
		await message.answer(
			f'🅰️ Name: {db.get_name(user_id)[0]}\n\n'
			f'🔞 Age: {db.get_age(user_id)[0]}\n\n'
			f'👫 Gender: {sex}\n\n'
			f'🌍 Country: {db.get_country(user_id)[0]}\n\n'
			f'🏙️ Ciry: {db.get_city(user_id)[0]}\n\n'
			f'💕 Couple {db.get_op_sex(user_id)[0]}',
   
			reply_markup=kb.profile_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['settings'])
@dp.message_handler(lambda message: message.text == '⚙️ Edit profile')
async def settings(message):
	await message.answer('Pilih parameter yang ingin Anda ubah:', reply_markup=kb.settings_kb)


@dp.message_handler(commands=['statistic'])
@dp.message_handler(lambda message: message.text == '📈 Statistics')
async def profile(message):
	try:
		user_id = message.from_user.id
		await message.answer(
			f'💬 Chat: {db.get_chats(user_id)[0]}\n\n'
			f'⌨️ Message: {db.get_messages(user_id)[0]}\n\n'
			f'👍 Like: {db.get_likes(user_id)[0]}\n\n'
			f'👎 Not like: {db.get_dislikes(user_id)[0]}\n\n'
			f'👨‍💻 Referral: {db.get_refs(user_id)[0]}',
			reply_markup=kb.statistic_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['ref'])
@dp.message_handler(lambda message: message.text == '💼 Referral' or message.text == '🆓 Dapatkan VIP secara gratis')
async def ref(message):
	try:
		user_id = message.from_user.id
		await message.answer(f'Share your referral link to receive COIN ONS\n'
		                     f'1 click the link = 200 COIN ONS\n'
		                     f'1000 COIN ONS = 1 day VIP 👑\n')
		await message.answer(f'Your coins {db.get_points(user_id)[0]} COIN ONS')
		if bool(db.get_notifications(message.from_user.id)[0]):
			await message.answer(f'🆔 Your referral link:\n'
			                     f'{"https://t.me/Cintasatumalambot?start=" + str(user_id)}',
			                     disable_web_page_preview=True, reply_markup=kb.off_kb)
		else:
			await message.answer(f'🆔 Your referral link:\n'
			                     f'{"https://t.me/Cintasatumalambot?start=" + str(user_id)}',
			                     disable_web_page_preview=True, reply_markup=kb.on_kb)
	except Exception as e:
		warning_log.warning(e)
		
@dp.message_handler(commands=['getcoin'])
async def getcoin(message):
	try:
		if str(message.from_user.id) in config.ADMINS:
			db.edit_points(+100, message.from_user.id)
			await message.answer('Berhasil mendapatkan 100 diamons')
		else:
			await message.answer('Anda bukan andmin')
			
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['trade'])
@dp.message_handler(lambda message: message.text == 'Exchange COIN ONS')
async def trade(message):
	try:
		if db.get_points(message.from_user.id)[0] >= 1000:
			db.edit_points(-1000, message.from_user.id)
			if db.get_vip_ends(message.from_user.id)[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y %H:%M'),
				                 message.from_user.id)
				await message.answer('succeed!')
			else:
				db.edit_vip_ends((datetime.strptime(db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') +
				                  timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), message.from_user.id)
			await message.answer('succeed!')
		else:
			await message.answer('You dont have enough coins!')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == 'Enable notifications 🔔')
async def notifications(message):
	try:
		db.edit_notifications(1, message.from_user.id)
		await message.answer('Notifications about new referrals are turn on!', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == 'Turn off notifications 🔕')
async def notifications(message):
	try:
		db.edit_notifications(0, message.from_user.id)
		await message.answer('Notifications about new referrals are turned off!', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.callback_query_handler(lambda call: call.data == 'on')
async def notifications_on(call):
	await db.edit_notifications(1, call.from_user.id)
	await call.reply('Notifications enabled')


@dp.callback_query_handler(lambda call: call.data == 'off')
async def notifications_off(call):
	await db.edit_notifications(1, call.from_user.id)
	await call.reply('Notifications are turned off')


@dp.message_handler(commands=['top'])
@dp.message_handler(lambda message: message.text == '🏆 Rating')
async def top(message):
	try:
		await message.answer('Below is the ranking by criteria.', reply_markup=kb.top_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '🔝 5 top based on message')
async def top(message):
	try:
		sp = list(db.top_messages())
		for i in range(len(sp)):
			if i == 0:
				c = '🥇'
			elif i == 1:
				c = '🥈'
			elif i == 2:
				c = '🥉'
			else:
				c = str(i + 1) + '.'
			await message.answer(f'{c} {sp[i][0]} — <b>{sp[i][1]}</b> <i>pesan</i>', parse_mode='HTML')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '🔝 5 top based on likesa')
async def top(message):
	try:
		sp = list(db.top_likes())
		for i in range(len(sp)):
			if i == 0:
				c = '🥇'
			elif i == 1:
				c = '🥈'
			elif i == 2:
				c = '🥉'
			else:
				c = str(i + 1) + '.'
			await message.answer(f'{c} {sp[i][0]} — <b>{sp[i][1]}</b> <i>suka</i>', parse_mode='HTML')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '🔝 5 top based on referrals')
async def top(message):
	try:
		sp = list(db.top_refs())
		for i in range(len(sp)):
			if i == 0:
				c = '🥇'
			elif i == 1:
				c = '🥈'
			elif i == 2:
				c = '🥉'
			else:
				c = str(i + 1) + '.'
			await message.answer(f'{c} {sp[i][0]} — <b>{sp[i][1]}</b> <i>referal</i>', parse_mode='HTML')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['vip'])
@dp.message_handler(lambda message: message.text == 'VIP 👑')
async def vip(message):
	try:
		if db.get_vip_ends(message.from_user.id)[0] is not None:
			if datetime.strptime(db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
				delta = datetime.strptime(db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') - datetime.now()
				await message.answer(
					f'Remaining {delta.days} day, {delta.seconds // 3600} hours, {delta.seconds // 60 % 60} second VIP',
					reply_markup=kb.vip_kb)
			else:
				await message.answer(f'VIP member:\n'
			                     	 f'1) <b>Search by your opposite gender..\n</b>'
								 	 f'2) <b>Search by your city...\n</b>'
			                     	 f'3) <b>Detailed information about the interlocutor: reviews, name, age, gender, country, city, and photo profile\n</b>'
			                     	 f'4) <b>First place in line.\n</b>'
			                     	 f'<i>Ini belum semuanya, fitur akan terus ditambahkan</i>',
				                     reply_markup=kb.vip_kb, parse_mode='HTML')
		else:
			await message.answer(f'VIP member:\n'
			                     f'1) <b>Search by your opposite gender..\n</b>'
								 f'2) <b>Search by your city...\n</b>'
			                     f'3) <b>Detailed information about the interlocutor: reviews, name, age, gender, country, city, and photo profile\n</b>'
			                     f'4) <b>First place in line.\n</b>'
			                     f'<i>Ini belum semuanya, fitur akan terus ditambahkan</i>',
			                     reply_markup=kb.vip_kb, parse_mode='HTML')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['buy_vip'])
@dp.message_handler(lambda message: message.text == '💰 Buy/Renew VIP')
async def buy_vip(message):
	try:
		await message.answer('Select duration:', reply_markup=kb.buy_kb)
	except Exception as e:
		warning_log.warning(e)

@dp.message_handler(lambda message: message.text == '👑 VIP / day')
async def buy_day(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetName.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 1k COIN ONS')
	except Exception as e:
		warning_log.warning(e)
	

@dp.message_handler(lambda message: message.text == '👑 VIP / week')
async def buy_week(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetAge.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 5K COIN ONS')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '👑 VIP / mouth')
async def buy_mounth(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetCountry.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 15K COIN ONS')
	except Exception as e:
		warning_log.warning(e)
  

	except Exception as e:
		warning_log.warning(e)
# Поиск

@dp.message_handler(commands=['cancel_search'])
@dp.message_handler(lambda message: message.text == '🚫 Cancel search')
async def cancel_search(message):
	try:
		await message.answer('Search cancelled. 😥\nType /search, to start searching',
		                     reply_markup=kb.main_kb)
		db.delete_from_queue(message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['like'])
@dp.message_handler(lambda message: message.text == '👍 Like')
async def like(message):
	try:
		await message.answer('Thank you for your response!', reply_markup=kb.main_kb)
		db.edit_likes(1, db.get_last_connect(message.from_user.id)[0])
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['dislike'])
@dp.message_handler(lambda message: message.text == '👎 Not like')
async def dislike(message):
	try:
		await message.answer('Thanks for the feedback!', reply_markup=kb.main_kb)
		db.edit_dislikes(1, db.get_last_connect(message.from_user.id)[0])
	except Exception as e:
		warning_log.warning(e)


class Chatting(StatesGroup):
	msg = State()


@dp.message_handler(commands=['search'])
@dp.message_handler(lambda message: message.text == 'Random 🔀' or message.text == '➡️ Dialog selanjutnya')
async def search(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.reply("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Random 🔀 AGAIN</b>", parse_mode='HTML')
		db.add_to_queue(message.from_user.id, db.get_sex(message.from_user.id)[0])
		await message.answer('We are looking for someone for you.. 🔍', reply_markup=kb.cancel_search_kb)
		while True:
			await asyncio.sleep(0.5)
			if db.search(message.from_user.id)[0] is not None:
				db.update_connect_with(db.search(message.from_user.id)[0], message.from_user.id)
				db.update_connect_with(message.from_user.id, db.search(message.from_user.id)[0])
				break
		while True:
			await asyncio.sleep(0.5)
			if db.get_connect_with(message.from_user.id)[0] is not None:
				db.delete_from_queue(message.from_user.id)
				db.delete_from_queue(db.get_connect_with(message.from_user.id)[0])
				break
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			sex = 'Tidak dikenal'
			user_id = db.get_connect_with(message.from_user.id)[0]
			if db.get_sex(user_id)[0] == 'male':
				sex = 'male'
			elif db.get_sex(user_id)[0] == 'female':
				sex = 'female'
			text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
			profile_pictures = await dp.bot.get_user_profile_photos(user_id)
			await bot.send_photo(message.from_user.id, (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
					                       reply_markup=kb.stop_kb)
		else:
			await bot.send_message(message.from_user.id, 'Menemukan seseorang untukmu 💕', reply_markup=kb.stop_kb)
   
		if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
			db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0], '%d.%m.%Y %H:%M') > datetime.now():
			sex = 'Tidak dikenal'
			user_id = message.from_user.id
			if db.get_sex(user_id)[0] == 'male':
				sex = 'male'
			elif db.get_sex(user_id)[0] == 'female':
				sex = 'female'
			text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
			profile_pictures = await dp.bot.get_user_profile_photos(user_id)
			await bot.send_photo(db.get_connect_with(message.from_user.id)[0], (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
					                       reply_markup=kb.stop_kb)
		else:
			await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Menemukan seseorang untukmu 💕',
			                       reply_markup=kb.stop_kb)
		await Chatting.msg.set()
	except Exception as e:
		warning_log.warning(e)



@dp.message_handler(commands=['search_nearby'])
@dp.message_handler(lambda message: message.text == 'Peaplo nearby 📍')
async def search_nearby(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.answer("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Acak 🔀 AGAIN</b>", parse_mode='HTML')
		user_id = message.from_user.id
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			db.add_to_queue_vip(message.from_user.id, db.get_city(message.from_user.id)[0], db.get_city(user_id)[0])
			await message.answer('Kami sedang mencari seseorang untuk anda.. 🔍\nBila lama coba untuk ganti looking place', reply_markup=kb.cancel_search_kb)
			while True:
				user_id = message.from_user.id
				await asyncio.sleep(0.5)	
				if db.search_vip(message.from_user.id, db.get_city(message.from_user.id)[0], db.get_city(user_id)[0]) is not None:
					if db.get_city(db.search(message.from_user.id)[0])[0] == db.get_city(message.from_user.id)[0]:
							db.update_connect_with(
								db.search(message.from_user.id)[0], message.from_user.id)
							db.update_connect_with(
								message.from_user.id, db.search(message.from_user.id)[0])
							break
			while True:
				await asyncio.sleep(0.5)
				if db.get_connect_with(message.from_user.id)[0] is not None:
					db.delete_from_queue(message.from_user.id)
					db.delete_from_queue(db.get_connect_with(message.from_user.id)[0])
					break
 
			if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
				db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
				sex = 'Tidak dikenal'
				user_id = db.get_connect_with(message.from_user.id)[0]
				if db.get_sex(user_id)[0] == 'male':
					sex = 'male'
				elif db.get_sex(user_id)[0] == 'female':
					sex = 'female'
				text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
				profile_pictures = await dp.bot.get_user_profile_photos(user_id)
				await bot.send_photo(message.from_user.id, (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
						                       reply_markup=kb.stop_kb)
			else:
				await bot.send_message(message.from_user.id, 'Find someone for you 💕', reply_markup=kb.stop_kb)
   
			if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
				db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0], '%d.%m.%Y %H:%M') > datetime.now():
				sex = 'Tidak dikenal'
				user_id = message.from_user.id
				if db.get_sex(user_id)[0] == 'male':
					sex = 'male'
				elif db.get_sex(user_id)[0] == 'female':
					sex = 'female'
				text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
				profile_pictures = await dp.bot.get_user_profile_photos(user_id)
				await bot.send_photo(db.get_connect_with(message.from_user.id)[0], (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
						                       reply_markup=kb.stop_kb)
			else:
				await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Find someone for you 💕',
			    	                   reply_markup=kb.stop_kb)
			await Chatting.msg.set()
		else:
			await message.answer('People nearby search is only available for 👑 VIP users')
	except Exception as e:
		warning_log.warning(e)
  
@dp.message_handler(commands=['search_couple'])
@dp.message_handler(lambda message: message.text == 'Couple 💕')
async def search_male(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.answer("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT AGAIN</b>", parse_mode='HTML')
		user_id = message.from_user.id
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			db.add_to_queue_vip(message.from_user.id, db.get_op_sex(message.from_user.id)[0], db.get_sex(user_id)[0])
			await message.answer('We are looking for someone for you.. 🔍\If it takes a long time, try changing your city', reply_markup=kb.cancel_search_kb)
			while True:
				user_id = message.from_user.id
				await asyncio.sleep(0.5)	
				if db.search_vip(message.from_user.id, db.get_op_sex(message.from_user.id)[0], db.get_sex(user_id)[0]) is not None:
					if db.get_op_sex(db.search(message.from_user.id)[0])[0] == db.get_sex(message.from_user.id)[0]:
							db.update_connect_with(
								db.search(message.from_user.id)[0], message.from_user.id)
							db.update_connect_with(
								message.from_user.id, db.search(message.from_user.id)[0])
							break
			while True:
				await asyncio.sleep(0.5)
				if db.get_connect_with(message.from_user.id)[0] is not None:
					db.delete_from_queue(message.from_user.id)
					db.delete_from_queue(db.get_connect_with(message.from_user.id)[0])
					break
 
			if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
				db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
				sex = 'Tidak dikenal'
				user_id = db.get_connect_with(message.from_user.id)[0]
				if db.get_sex(user_id)[0] == 'male':
					sex = 'male'
				elif db.get_sex(user_id)[0] == 'female':
					sex = 'female'
				text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
				profile_pictures = await dp.bot.get_user_profile_photos(user_id)
				await bot.send_photo(message.from_user.id, (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
						                       reply_markup=kb.stop_kb)
			else:
				await bot.send_message(message.from_user.id, 'Find someone for you 💕', reply_markup=kb.stop_kb)
   
			if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
				db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0], '%d.%m.%Y %H:%M') > datetime.now():
				sex = 'Tidak dikenal'
				user_id = message.from_user.id
				if db.get_sex(user_id)[0] == 'male':
					sex = 'male'
				elif db.get_sex(user_id)[0] == 'female':
					sex = 'female'
				text = f'Find someone for you 💕\n🅰️ Name: {db.get_name(user_id)[0]}\n🔞 Age: {db.get_age(user_id)[0]}\n👫 Gender: {sex}\n🌍 Country: {db.get_country(user_id)[0]}\n🏙️ City: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
				profile_pictures = await dp.bot.get_user_profile_photos(user_id)
				await bot.send_photo(db.get_connect_with(message.from_user.id)[0], (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
						                       reply_markup=kb.stop_kb)
			else:
				await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Find someone for you 💕',
			    	                   reply_markup=kb.stop_kb)
			await Chatting.msg.set()
		else:
			await message.answer('Pencarian gender hanya tersedia untuk 👑 pengguna VIP')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(content_types=ContentTypes.TEXT)
@dp.message_handler(state=Chatting.msg)
async def chatting(message, state: FSMContext):
	try:
		await state.update_data(msg=message.text)
		user_data = await state.get_data()

		if user_data['msg'] == '🏹 Send the link to yourself' or user_data['msg'] == '/link':
			if message.from_user.username is None:
				await bot.send_message(db.get_connect_with(message.from_user.id)[0],
				                       'Users do not enter a username in Telegram settings!')
			else:
				await message.answer('@' + message.from_user.username)
		elif user_data['msg'] == '🛑 Stop dialogue' or user_data['msg'] == '/stop':
			await state.finish()
			await bot.send_message(message.from_user.id,
			                       'Dialogue stops 😞\nYou can rate your interlocutor below',
			                       reply_markup=kb.search_kb, parse_mode=ParseMode.HTML)
			await bot.send_message(db.get_connect_with(message.from_user.id)[0],
			                       'Dialogue stops 😞\nYou can rate your interlocutor below',
			                       reply_markup=kb.search_kb, parse_mode=ParseMode.HTML)
			db.delete_from_queue(db.get_connect_with(message.from_user.id)[0])
			db.delete_from_queue(message.from_user.id)
			db.edit_chats(1, db.get_connect_with(message.from_user.id)[0])
			db.edit_chats(1, message.from_user.id)
			db.save_last_connect(db.get_connect_with(message.from_user.id)[0])
			db.save_last_connect(message.from_user.id)
			db.update_connect_with(None, db.get_connect_with(message.from_user.id)[0])
			db.update_connect_with(None, message.from_user.id)

		elif user_data['msg'].startswith('/admin'):
			if str(message.from_user.id) in config.ADMINS:
				msg = user_data['msg'].strip('/admin')
				print(msg)
				await bot.send_message(db.get_connect_with(message.from_user.id)[0], f'Message from Admin:\n{msg}')
			else:
				await message.answer('Akses ditolak')
    

		# elif user_data['msg'] == '➡️≈':
		#     await search(message, state)
		#
		# elif user_data['msg'] == 'Подбросить монетку🎲':
		#     coin = random.randint(1, 2)
		#
		#     if coin == 1:
		#         coin = text(italic('Решка'))
		#     else:
		#         coin = text(italic('Орёл'))
		#
		#     await message.answer(coin, parse_mode=ParseMode.MARKDOWN)
		#     await bot.send_message(db.get_connect_with(message.from_user.id)[0], coin,
		#     parse_mode=ParseMode.MARKDOWN)
		#
		# elif user_data['msg'] == 'Назад':
		#     await state.finish()

		else:
			await bot.send_message(db.get_connect_with(message.from_user.id)[0], user_data['msg'])
			db.log_message(message.from_user.id, user_data['msg'])
			db.edit_messages(1, message.from_user.id)

	except exceptions.ChatIdIsEmpty:
		await state.finish()

	except exceptions.BotBlocked:
		await message.answer('The user has left the bot conversation!')
		await state.finish()

	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(content_types=['photo'])
@dp.message_handler(state=Chatting.msg)
async def chatting_photo(message, state: FSMContext):
	try:
		await state.update_data(msg=message.text, photo=message.photo[-1])
		user_data = await state.get_data()
		await bot.send_photo(db.get_connect_with(message.from_user.id)[0], user_data['photo'].file_id,
		                     caption=user_data['msg'])
		await bot.send_photo(-1001774215660, user_data['photo'].file_id,
		                     caption=user_data['msg'])
		await bot.send_message(-1001774215660, f'ID - @{str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')

	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(content_types=['video'])
@dp.message_handler(state=Chatting.msg)
async def chatting_video(message, state: FSMContext):
	try:
		await bot.send_video(db.get_connect_with(message.from_user.id)[0], message.video.file_id,
		                     caption=message.text)
		await bot.send_video(-1001774215660, message.video.file_id,
		                     caption=message.text)
		await bot.send_message(-1001774215660, f'ID - {str(message.from_user.id)}\nusername - @{str(message.from_user.username)}\nmessage - {str(message.text)}')
		
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(content_types=['animation'])
@dp.message_handler(state=Chatting.msg)
async def chatting_gif(message, state: FSMContext):
	try:
		await bot.send_animation(db.get_connect_with(message.from_user.id)[0], message.animation.file_id,
		                         caption=message.text)

	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(content_types=['sticker'])
@dp.message_handler(state=Chatting.msg)
async def chatting_sticker(message, state: FSMContext):
	try:
		await bot.send_sticker(db.get_connect_with(message.from_user.id)[0], message.sticker.file_id)
	except Exception as e:
		warning_log.warning(e)


#@dp.message_handler(commands=['back'])
# @dp.message_handler(lambda message: message.text == 'Назад')
# async def back(message, state: FSMContext):
#     await state.finish()


# логи в телеграм канал
# async def send_to_channel_log(message):
#     await bot.send_message(-1111111,
#                            f'ID - {str(message.from_user.id)}\nusername - {str(
#                            message.from_user.username)}\nmessage - {str(message.text)}')
#
#
# async def send_to_channel_log_exception(message, except_name):
#     await bot.send_message(-111111111, f'Ошибка\n\n{except_name}')


@dp.message_handler()
async def end(message):
	await message.answer('I dont know what to do with this 😲\nIm just reminding you that there are commands/start dan /help')


if __name__ == '__main__':
	print('Работаем👌')
	executor.start_polling(dp, skip_updates=True)
