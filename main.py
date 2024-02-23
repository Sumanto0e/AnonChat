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

@dp.message_handler(lambda message: message.text == '🔙 Ke utama')
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
				await bot.send_message(user_id, 'Seseorang bergabung dengan bot menggunakan tautan Anda!')
				if db.get_refs(user_id)[0] % 10 == 0:
					await bot.send_message(user_id, 'Anda dapat mematikan notifikasi tentang referensi baru di pengaturan.')
		if not db.user_exists(message.from_user.id):
			await message.answer(f"🎉Selamat datang di obrolan anonim!🎉\n"
			                     f"Sebelum Anda mulai berkomunikasi, Anda harus mendaftar.\n"
			                     f"Setelah pendaftaran Anda akan menerima VIP selama sebulan gratis!</b>\n"
			                     f"Mulai pendaftaran - /daftar\n"
			                     f"Aturan obrolan - /rules", parse_mode='HTML')
		else:
			await message.answer(f'Halo, {db.get_name(message.from_user.id)[0]}', reply_markup=kb.main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['help'])
async def help(message):
	try:
		await message.answer(f'/start - Memulai\n'
		                     f'/rules - Peraturan\n'
		                     f'/search - Mencari pasangan\n'
		                     f'/stop - keluar dari obrolan\n'
		                     f'/vip - VIP\n'
		                     f'/ref - referal'
				     f'/trade - trade')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['daftar'])
async def registrate(message):
	if not db.user_exists(message.from_user.id):
		await message.answer("Masukkan nama Anda.")
		await RegState.name.set()


@dp.message_handler(state=RegState.name)
async def set_name(message, state: FSMContext):
	await state.update_data(name=message.text)
	await message.answer("Sekarang masukkan jenis kelamin Anda (M/F).")
	await RegState.sex.set()


@dp.message_handler(state=RegState.sex)
async def set_sex(message, state: FSMContext):
	if message.text == 'м' or message.text == 'M':
		await state.update_data(sex='male')
		await message.answer("Sekarang masukkan usia Anda.")
		await RegState.age.set()
	elif message.text == 'F' or message.text == 'F':
		await state.update_data(sex='female')
		await message.answer("Sekarang masukkan usia Anda.")
		await RegState.age.set()
	else:
		await message.reply("Anda memasukkan nilai yang salah, silakan masukkan lagi.")


@dp.message_handler(state=RegState.age)
async def set_age(message, state: FSMContext):
	if 5 < int(message.text) < 100:
		await state.update_data(age=message.text)
		await message.answer("tinggal di negara mana?")
		await RegState.country.set()
	else:
		await message.reply("Anda memasukkan nilai yang salah, ketik dengan angka, silakan masukkan kembali")


@dp.message_handler(state=RegState.country)
async def set_country(message, state: FSMContext):
	await state.update_data(country=message.text)
	await message.answer("Di kota mana kamu tinggal?")
	await RegState.city.set()


@dp.message_handler(state=RegState.city)
async def set_city(message, state: FSMContext):
	await state.update_data(city=message.text)
	await message.answer("Terima kasih telah mendaftar! Anda sekarang dapat mencari - /search.",
	                     reply_markup=kb.main_kb)
	data = await state.get_data()
	db.new_user(data['name'], data['age'], data['sex'], data['country'], data['city'], message.from_user.id)
	await state.finish()
	if db.get_vip_ends(message.from_user.id)[0] is None:
		db.edit_vip_ends((datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y %H:%M'),
		                 message.from_user.id)


@dp.message_handler(commands=['rules'])
@dp.message_handler(lambda message: message.text == 'Peraturan 📖')
async def rules(message):
	try:
		await message.answer(f'<b>Tidak diperbolehkan dalam obrolan:</b>\n'
		                     f'1) Setiap penyebutan zat psikoaktif (narkoba).\n'
		                     f'2) Pertukaran, distribusi 18+ materi apa pun\n'
		                     f'3) Iklan apa pun, spam, penjualan apa pun.\n'
		                     f'4) Perilaku menyerang.\n'
		                     f'5) Tindakan apa pun yang melanggar aturan Telegram.\n',
		                     parse_mode='HTML', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


# Настройки


@dp.message_handler(commands=['edit_name'])
@dp.callback_query_handler(lambda call: call.data == 'name')
async def edit_name(call):
	await bot.answer_callback_query(call.id, 'Masukkan nama Anda:')
	db.set_state(SetName.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetName.waiting.value)
async def editing_name(message):
	try:
			db.edit_name(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Nama disimpan!", reply_markup=kb.main_kb)
			db.set_state(SetName.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_age'])
@dp.callback_query_handler(lambda call: call.data == 'age')
async def edit_age(call):
	await bot.answer_callback_query(call.id, 'Masukkan usia:')
	db.set_state(SetAge.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetAge.waiting.value)
async def editing_age(message):
	try:
			db.edit_age(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Usia disimpan!", reply_markup=kb.main_kb)
			db.set_state(SetAge.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_sex'])
@dp.callback_query_handler(lambda call: call.data == 'sex')
async def edit_sex(call):
	await call.message.edit_reply_markup(reply_markup=kb.sex_kb)
	await bot.answer_callback_query(call.id, 'Pilih jenis kelamin:')
	db.set_state(SetSex.waiting.value, call.from_user.id)


@dp.callback_query_handler(lambda call: call.data == 'male' or call.data == 'female')
async def editing_sex(call):
	try:
		if call.data == 'male':
			db.edit_sex('male', call.from_user.id)
			await bot.send_message(call.from_user.id, "Jenis kelamin disimpan!", reply_markup=kb.main_kb)
			await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
			db.set_state(SetSex.nothing.value, call.from_user.id)
		elif call.data == 'female':
			db.edit_sex('female', call.from_user.id)
			await bot.send_message(call.from_user.id, "Jenis kelamin disimpan!", reply_markup=kb.main_kb)
			await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
			db.set_state(SetSex.nothing.value, call.from_user.id)
		else:
			await call.reply("Anda memasukkan nilai yang salah, ketik 'male' atau 'female' silakan masukkan kembali")
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_country'])
@dp.callback_query_handler(lambda call: call.data == 'country')
async def edit_country(call):
	await bot.answer_callback_query(call.id, 'Masukkan negara Anda:')
	db.set_state(SetCountry.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetCountry.waiting.value)
async def editing_country(message):
	try:
		if message.from_user.id in config.ADMINS:
			await bot.send_message(int(message.text), f'Durasi VIP berhasil ditambahkan 31 hari')
			await bot.send_message(5458705482, f'Durasi VIP berhasil {message.text} ditambahkan 31 hari')
			if db.get_vip_ends(int(message.text))[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
			else:
				db.edit_vip_ends(
					(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
			 	 	 timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), message.text)
		else:
			db.edit_country(message.text, message.from_user.id)
			await bot.send_message(message.from_user.id, "Negara disimpan!", reply_markup=kb.main_kb)
			db.set_state(SetCountry.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['edit_city'])
@dp.callback_query_handler(lambda call: call.data == 'city')
async def edit_city(call):
	await bot.answer_callback_query(call.id, 'Masukkan kota:')
	db.set_state(SetCity.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetCity.waiting.value)
async def editing_city(message):
	try:
		db.edit_city(message.text, message.from_user.id)
		await bot.send_message(message.from_user.id, "Kota ini telah diselamatkan!", reply_markup=kb.main_kb)
		db.set_state(SetCity.nothing.value, message.from_user.id)
	except Exception as e:
		warning_log.warning(e)

@dp.message_handler(commands=['edit_op_sex'])
@dp.callback_query_handler(lambda call: call.data == 'op_sex')
async def edit_op_sex(call):
     await bot.answer_callback_query(call.id, 'Masukkan daerah yang kamu ingin:')
     db.set_state(SetOpSex.waiting.value, call.from_user.id)


@dp.message_handler(lambda message: db.get_state(message.from_user.id)[0] == SetOpSex.waiting.value)
async def editing_op_sex(message):
     try:
         db.edit_op_sex(message.text, message.from_user.id)
         await bot.send_message(message.from_user.id, "Pencarian orang berdasarkan daerah berhasil!")
         db.set_state(SetOpSex.nothing.value, message.from_user.id)
     except Exception as e:
         warning_log.warning(e)

@dp.message_handler(commands=['profile'])
@dp.message_handler(lambda message: message.text == 'Profil 👤')
async def profile(message):
	try:
		sex = 'Tidak dikenal'
		user_id = message.from_user.id
		if db.get_sex(user_id)[0] == 'male':
			sex = 'male'
		elif db.get_sex(user_id)[0] == 'female':
			sex = 'female'
		await message.answer(
			f'🅰️ Nama: {db.get_name(user_id)[0]}\n\n'
			f'🔞 Usia: {db.get_age(user_id)[0]}\n\n'
			f'👫 Jenis kelamin: {sex}\n\n'
			f'🌍 Negara: {db.get_country(user_id)[0]}\n\n'
			f'🏙️ Kota: {db.get_city(user_id)[0]}\n\n'
			f'📍 Looking place: {db.get_op_sex(user_id)[0]}',
   
			reply_markup=kb.profile_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['settings'])
@dp.message_handler(lambda message: message.text == '⚙️ Sunting profil')
async def settings(message):
	await message.answer('Pilih parameter yang ingin Anda ubah:', reply_markup=kb.settings_kb)


@dp.message_handler(commands=['statistic'])
@dp.message_handler(lambda message: message.text == '📈 Statistik')
async def profile(message):
	try:
		user_id = message.from_user.id
		await message.answer(
			f'💬 Obrolan: {db.get_chats(user_id)[0]}\n\n'
			f'⌨️ Pesan: {db.get_messages(user_id)[0]}\n\n'
			f'👍 Suka: {db.get_likes(user_id)[0]}\n\n'
			f'👎 Tidak suka: {db.get_dislikes(user_id)[0]}\n\n'
			f'👨‍💻 Pengguna diundang: {db.get_refs(user_id)[0]}',
			reply_markup=kb.statistic_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['ref'])
@dp.message_handler(lambda message: message.text == '💼 Rujukan' or message.text == '🆓 Dapatkan VIP secara gratis')
async def ref(message):
	try:
		user_id = message.from_user.id
		await message.answer(f'Bagikan tautan rujukan Anda untuk menerima COIN ONS\n'
		                     f'1 klik tautan = 200 COIN ONS\n'
		                     f'1000 COIN ONS = 1 hari status VIP 👑\n')
		await message.answer(f'Diamond anda {db.get_points(user_id)[0]} COIN ONS')
		if bool(db.get_notifications(message.from_user.id)[0]):
			await message.answer(f'🆔 Tautan referensi Anda:\n'
			                     f'{"https://t.me/Cintasatumalambot?start=" + str(user_id)}',
			                     disable_web_page_preview=True, reply_markup=kb.off_kb)
		else:
			await message.answer(f'🆔 Tautan refrensi Anda:\n'
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
@dp.message_handler(lambda message: message.text == 'Tukarkan COIN ONS')
async def trade(message):
	try:
		if db.get_points(message.from_user.id)[0] >= 1000:
			db.edit_points(-1000, message.from_user.id)
			if db.get_vip_ends(message.from_user.id)[0] is None:
				db.edit_vip_ends((datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y %H:%M'),
				                 message.from_user.id)
				await message.answer('Berhasil!')
			else:
				db.edit_vip_ends((datetime.strptime(db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') +
				                  timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), message.from_user.id)
			await message.answer('Успешно!')
		else:
			await message.answer('Anda tidak memiliki cukup poin')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == 'Aktifkan notifikasi 🔔')
async def notifications(message):
	try:
		db.edit_notifications(1, message.from_user.id)
		await message.answer('Pemberitahuan tentang rujukan baru disertakan!', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == 'Matikan notifikasi 🔕')
async def notifications(message):
	try:
		db.edit_notifications(0, message.from_user.id)
		await message.answer('Pemberitahuan tentang referensi baru dimatikan!', reply_markup=kb.to_main_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.callback_query_handler(lambda call: call.data == 'on')
async def notifications_on(call):
	await db.edit_notifications(1, call.from_user.id)
	await call.reply('Notifikasi diaktifkan')


@dp.callback_query_handler(lambda call: call.data == 'off')
async def notifications_off(call):
	await db.edit_notifications(1, call.from_user.id)
	await call.reply('Notifikasi dimatikan')


@dp.message_handler(commands=['top'])
@dp.message_handler(lambda message: message.text == '🏆 Peringkat')
async def top(message):
	try:
		await message.answer('Di bawah ini adalah peringkat berdasarkan berbagai kriteria.', reply_markup=kb.top_kb)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '🔝 5 teratas berdasarkan pesan')
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


@dp.message_handler(lambda message: message.text == '🔝 5 teratas berdasarkan suka')
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


@dp.message_handler(lambda message: message.text == '🔝 5 teratas berdasarkan referal')
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
					f'Tersisa {delta.days} hari, {delta.seconds // 3600} jam, {delta.seconds // 60 % 60} menit VIP',
					reply_markup=kb.vip_kb)
			else:
				await message.answer(f'VIP member:\n'
				                     f'1) Cari berdasarkan jenis kelamin.\n'
				                     f'2) Informasi terperinci tentang lawan bicara: ulasan, nama, jenis kelamin, usia, negara...\n'
				                     f'3) <b>Tempat pertama dalam antrean.\n</b>'
				                     f'<i>Ini belum semuanya, fitur akan terus ditambahkan</i>',
				                     reply_markup=kb.vip_kb, parse_mode='HTML')
		else:
			await message.answer(f'VIP memberi:\n'
			                     f'1) Cari berdasarkan jenis kelamin.\n'
			                     f'2) Informasi terperinci tentang lawan bicara: ulasan, nama, umur, jenis kelamin, negara, kota\n'
			                     f'3) <b>Tempat pertama dalam antrean.\n</b>'
			                     f'<i>Ini belum semuanya, fitur akan terus ditambahkan</i>',
			                     reply_markup=kb.vip_kb, parse_mode='HTML')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['buy_vip'])
@dp.message_handler(lambda message: message.text == '💰 Beli/Perpanjang VIP')
async def buy_vip(message):
	try:
		await message.answer('Pilih durasi:', reply_markup=kb.buy_kb)
	except Exception as e:
		warning_log.warning(e)

@dp.message_handler(lambda message: message.text == '👑 VIP per hari')
async def buy_day(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetName.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 1k COIN ONS')
	except Exception as e:
		warning_log.warning(e)
	

@dp.message_handler(lambda message: message.text == '👑 VIP per minggu')
async def buy_week(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetAge.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 5K COIN ONS')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(lambda message: message.text == '👑 VIP per bulan')
async def buy_mounth(message):
	try:
        
		if str(message.from_user.id) in config.ADMINS:
			await message.answer(f'send id')
			db.set_state(SetCountry.waiting.value, message.from_user.id)
		else :
			await message.answer(f'Contact @nazhak\nPrice 25K COIN ONS')
	except Exception as e:
		warning_log.warning(e)
  

	except Exception as e:
		warning_log.warning(e)
# Поиск

@dp.message_handler(commands=['cancel_search'])
@dp.message_handler(lambda message: message.text == '🚫 Batalkan pencarian')
async def cancel_search(message):
	try:
		await message.answer('Pencarian dibatalkan. 😥\nKetik /search, untuk mulai mencari',
		                     reply_markup=kb.main_kb)
		db.delete_from_queue(message.from_user.id)
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['like'])
@dp.message_handler(lambda message: message.text == '👍 Suka')
async def like(message):
	try:
		await message.answer('Terima kasih atas tanggapan Anda!', reply_markup=kb.main_kb)
		db.edit_likes(1, db.get_last_connect(message.from_user.id)[0])
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['dislike'])
@dp.message_handler(lambda message: message.text == '👎 Tidak suka')
async def dislike(message):
	try:
		await message.answer('Terima kasih untuk umpan baliknya!', reply_markup=kb.main_kb)
		db.edit_dislikes(1, db.get_last_connect(message.from_user.id)[0])
	except Exception as e:
		warning_log.warning(e)


class Chatting(StatesGroup):
	msg = State()


@dp.message_handler(commands=['search'])
@dp.message_handler(lambda message: message.text == 'Acak 🔀' or message.text == '➡️ Dialog selanjutnya')
async def search(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.reply("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Acak 🔀 AGAIN</b>", parse_mode='HTML')
		db.add_to_queue(message.from_user.id, db.get_sex(message.from_user.id)[0])
		await message.answer('Kami sedang mencari seseorang untuk anda.. 🔍', reply_markup=kb.cancel_search_kb)
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
			await bot.send_message(message.from_user.id,
			                       f'Menemukan seseorang untukmu 💕\n'
			                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
			                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
			                       f'👫 Jenis kelamin: {sex}\n'
			                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
			                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
			                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
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
			text = f'Menemukan seseorang untukmu 💕\n🅰️ Nama: {db.get_name(user_id)[0]}\n🔞 Usia: {db.get_age(user_id)[0]}\n👫 Jenis kelamin: {sex}\n🌍 Negara: {db.get_country(user_id)[0]}\n🏙️ Kota: {db.get_city(user_id)[0]}\n👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}'
			profile_pictures = await dp.bot.get_user_profile_photos(user_id)
			await bot.send_photo(db.get_connect_with(message.from_user.id)[0], (dict((profile_pictures.photos[0][0])).get("file_id")), caption=text,
					                       reply_markup=kb.stop_kb)
		else:
			await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Menemukan seseorang untukmu 💕',
			                       reply_markup=kb.stop_kb)
		await Chatting.msg.set()
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['search_male'])
@dp.message_handler(lambda message: message.text == 'Male ♂️')
async def search_male(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.reply("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Acak 🔀 AGAIN</b>", parse_mode='HTML')
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			db.add_to_queue_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'male')
			await message.answer('Kami sedang mencari seseorang untuk anda.. 🔍', reply_markup=kb.cancel_search_kb)
			while True:
				await asyncio.sleep(0.5)
				if db.search_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'male')[0] is not None:
					db.update_connect_with(
						db.search_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'male')[0],
						message.from_user.id)
					db.update_connect_with(
						message.from_user.id, db.search_vip(message.from_user.id,
						                                    db.get_sex(message.from_user.id)[0], 'male')[0])
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
					await bot.send_message(message.from_user.id,
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(message.from_user.id, 'Menemukan seseorang untukmu 💕', reply_markup=kb.stop_kb)
				if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
					db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0],
					'%d.%m.%Y %H:%M') > datetime.now():
					sex = 'Tidak dikenal'
					user_id = message.from_user.id
					if db.get_sex(user_id)[0] == 'male':
						sex = 'male'
					elif db.get_sex(user_id)[0] == 'female':
						sex = 'female'
					await bot.send_message(db.get_connect_with(message.from_user.id)[0],
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Menemukan seseorang untukmu 💕',
					                       reply_markup=kb.stop_kb)
				await Chatting.msg.set()
		else:
			await message.answer('Pencarian gender hanya tersedia untuk 👑 pengguna VIP')
	except Exception as e:
		warning_log.warning(e)


@dp.message_handler(commands=['search_place'])
@dp.message_handler(lambda message: message.text == 'Looking place 📍')
async def search_female(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.answer("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Acak 🔀 AGAIN</b>", parse_mode='HTML')
		user_id = message.from_user.id
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			db.add_to_queue_vip(message.from_user.id, db.get_op_sex(message.from_user.id)[0], db.get_op_sex(user_id)[0])
			await message.answer('Kami sedang mencari seseorang untuk anda.. 🔍\nBila lama coba untuk ganti looking place', reply_markup=kb.cancel_search_kb)
			while True:
				user_id = message.from_user.id
				await asyncio.sleep(0.5)
				if db.get_op_sex(user_id)[0] == 'None':
					return await message.answer("set Looking place terlebih dahulu di sunting profil")
				if db.search_vip(message.from_user.id, db.get_op_sex(message.from_user.id)[0], db.get_op_sex(user_id)[0]) is not None:
					db.update_connect_with(
						db.search_vip(message.from_user.id, db.get_op_sex(message.from_user.id)[0], db.get_op_sex(user_id)[0]),
						message.from_user.id)
					db.update_connect_with(
						message.from_user.id, db.search_vip(message.from_user.id,
						                                    db.get_op_sex(message.from_user.id)[0], db.get_op_sex(user_id)[0]))
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
					await bot.send_message(message.from_user.id,
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(message.from_user.id, 'Menemukan seseorang untukmu 💕', reply_markup=kb.stop_kb)
				if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
					db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0],
					'%d.%m.%Y %H:%M') > datetime.now():
					sex = 'Tidak dikenal'
					user_id = message.from_user.id
					if db.get_sex(user_id)[0] == 'male':
						sex = 'male'
					elif db.get_sex(user_id)[0] == 'female':
						sex = 'female'
					await bot.send_message(db.get_connect_with(message.from_user.id)[0],
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Menemukan seseorang untukmu 💕',
					                       reply_markup=kb.stop_kb)
				await Chatting.msg.set()
		else:
			await message.answer('Pencarian gender hanya tersedia untuk 👑 pengguna VIP')
	except Exception as e:
		warning_log.warning(e)
  
@dp.message_handler(commands=['search_female'])
@dp.message_handler(lambda message: message.text == 'Female ♀️')
async def search_female(message):
	try:
		check_member = await bot.get_chat_member(-1001771712186, message.from_user.id)
		if check_member.status not in ["member", "creator"]:
			return await message.reply("<b>JOIN THE FIRST CHANNEL @ONSBASE AND DO IT Acak 🔀 AGAIN</b>", parse_mode='HTML')
		if db.get_vip_ends(message.from_user.id)[0] is not None and datetime.strptime(
			db.get_vip_ends(message.from_user.id)[0], '%d.%m.%Y %H:%M') > datetime.now():
			db.add_to_queue_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'female')
			await message.answer('Kami sedang mencari seseorang untuk anda.. 🔍', reply_markup=kb.cancel_search_kb)
			while True:
				await asyncio.sleep(0.5)
				if db.search_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'female')[0] is not None:
					db.update_connect_with(
						db.search_vip(message.from_user.id, db.get_sex(message.from_user.id)[0], 'female')[0],
						message.from_user.id)
					db.update_connect_with(
						message.from_user.id, db.search_vip(message.from_user.id,
						                                    db.get_sex(message.from_user.id)[0], 'female')[0])
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
					await bot.send_message(message.from_user.id,
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(message.from_user.id, 'Menemukan seseorang untukmu 💕', reply_markup=kb.stop_kb)
				if db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0] is not None and datetime.strptime(
					db.get_vip_ends(db.get_connect_with(message.from_user.id)[0])[0],
					'%d.%m.%Y %H:%M') > datetime.now():
					sex = 'Tidak dikenal'
					user_id = message.from_user.id
					if db.get_sex(user_id)[0] == 'male':
						sex = 'male'
					elif db.get_sex(user_id)[0] == 'female':
						sex = 'female'
					await bot.send_message(db.get_connect_with(message.from_user.id)[0],
					                       f'Menemukan seseorang untukmu 💕\n'
					                       f'🅰️ Nama: {db.get_name(user_id)[0]}\n'
					                       f'🔞 Usia: {db.get_age(user_id)[0]}\n'
					                       f'👫 Jenis kelamin: {sex}\n'
					                       f'🌍 Negara: {db.get_country(user_id)[0]}\n'
					                       f'🏙️ Kota: {db.get_city(user_id)[0]}\n'
					                       f'👍: {db.get_likes(user_id)[0]} 👎: {db.get_dislikes(user_id)[0]}\n',
					                       reply_markup=kb.stop_kb)
				else:
					await bot.send_message(db.get_connect_with(message.from_user.id)[0], 'Menemukan seseorang untukmu 💕',
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

		if user_data['msg'] == '🏹Kirim tautan ke diri Anda sendiri' or user_data['msg'] == '/link':
			if message.from_user.username is None:
				await bot.send_message(db.get_connect_with(message.from_user.id)[0],
				                       'Pengguna tidak mengisikan nama panggilan pada pengaturan telegram!')
			else:
				await message.answer('@' + message.from_user.username)
		elif user_data['msg'] == '🛑 Hentikan dialog' or user_data['msg'] == '/stop':
			await state.finish()
			await bot.send_message(message.from_user.id,
			                       'Dialog terhenti 😞\nAnda dapat menilai lawan bicara Anda di bawah',
			                       reply_markup=kb.search_kb, parse_mode=ParseMode.HTML)
			await bot.send_message(db.get_connect_with(message.from_user.id)[0],
			                       'Dialog terhenti 😞\nAnda dapat menilai lawan bicara Anda di bawah',
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
				await bot.send_message(db.get_connect_with(message.from_user.id)[0], f'Pesan dari Admin:\n{msg}')
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
		await message.answer('Pengguna telah meninggalkan bot obrolan!')
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
	await message.answer('Saya tidak tahu apa yang harus saya lakukan dengan ini 😲\nSaya hanya mengingatkan Anda bahwa ada perintah /start dan /help')


if __name__ == '__main__':
	print('Работаем👌')
	executor.start_polling(dp, skip_updates=True)
