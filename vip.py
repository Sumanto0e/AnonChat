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


async def buying_dayy(message):

	try:
		await bot.send_message(int(message.text), f'Durasi VIP berhasil ditambahkan 1 hari')
		await bot.send_message(5458705482, f'Durasi VIP berhasil {message.text} ditambahkan 1 hari')
		if db.get_vip_ends(int(message.text))[0] is None:
			db.edit_vip_ends((datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
		else:
			db.edit_vip_ends(
				(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
				 timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), message.text)

	except Exception as e:
		warning_log.warning(e)



async def buying_week(message):

	try:
		await bot.send_message(int(message.text), f'Durasi VIP berhasil ditambahkan 7 hari')
		await bot.send_message(5458705482, f'Durasi VIP berhasil {message.text} ditambahkan 1 hari')
		if db.get_vip_ends(int(message.text))[0] is None:
			db.edit_vip_ends((datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
		else:
			db.edit_vip_ends(
				(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
				 timedelta(days=7)).strftime('%d.%m.%Y %H:%M'), message.text)

	except Exception as e:
		warning_log.warning(e)



async def buying_mounth(message):

	try:
		await bot.send_message(int(message.text), f'Durasi VIP berhasil ditambahkan 31 hari')
		await bot.send_message(5458705482, f'Durasi VIP berhasil ditambahkan 31 hari')
		if db.get_vip_ends(int(message.text))[0] is None:
			db.edit_vip_ends((datetime.now() + timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), int(message.text))
           
		else:
			db.edit_vip_ends(
				(datetime.strptime(db.get_vip_ends(int(message.text))[0], '%d.%m.%Y %H:%M') +
				 timedelta(days=31)).strftime('%d.%m.%Y %H:%M'), message.text)

	except Exception as e:
		warning_log.warning(e)