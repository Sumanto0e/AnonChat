from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


to_main = KeyboardButton('🔙 Ke utama')

cancel_search_kb = ReplyKeyboardMarkup(
    resize_keyboard=True).add('🚫 Batalkan pencarian')

stop_kb = ReplyKeyboardMarkup(one_time_keyboard=True,
                              resize_keyboard=True).add('🛑 Hentikan dialog')

like = KeyboardButton('👍 Suka')
dislike = KeyboardButton('👎 Tidak suka')
next_dialog = KeyboardButton('➡️ Dialog selanjutnya')
search_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

like = KeyboardButton('👍 Suka')
dislike = KeyboardButton('👎 Tidak suka')
next_dialog = KeyboardButton('➡️ Dialog selanjutnya (♂️)')
search_male_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

like = KeyboardButton('👍 Suka')
dislike = KeyboardButton('👎 Tidak suka')
next_dialog = KeyboardButton('➡️ Dialog selanjutnya (♀️)')
search_female_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

man = KeyboardButton('Male ♂️')
random = KeyboardButton('Acak 🔀')
looking = KeyboardButton('Looking place 📍')
woman = KeyboardButton('Female ♀️')
vip = KeyboardButton('VIP 👑')
rules = KeyboardButton('Peraturan 📖')
profile = KeyboardButton('Profil 👤')
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).row(man, random, looking, woman).row(vip, rules, profile)

name = InlineKeyboardButton('🅰️ Nama', callback_data='name')
age = InlineKeyboardButton('🔞 Usia', callback_data='age')
sex = InlineKeyboardButton('👫 Jenis kelamin', callback_data='sex')
country = InlineKeyboardButton('🌍 Negara', callback_data='country')
city = InlineKeyboardButton('🏙️ Kota', callback_data='city')
op_sex = InlineKeyboardButton('📍 Looking place', callback_data='op_sex')
settings_kb = InlineKeyboardMarkup(
    resize_keyboard=True).add(name).add(age).add(sex).add(country).add(city)

change_profile = KeyboardButton('⚙️ Sunting profil')
statistic = KeyboardButton('📈 Statistik')
ref = KeyboardButton('💼 Rujukan')
profile_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(change_profile).add(
    statistic).add(ref).add(to_main)

vip_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('🆓 Dapatkan VIP secara gratis').add(
    '💰 Beli/Perpanjang VIP').add(to_main)

day = KeyboardButton('👑 VIP per hari')
week = KeyboardButton('👑 VIP per minggu')
month = KeyboardButton('👑 VIP per bulan')
buy_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(day).add(week).add(month).add(to_main)

to_main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(to_main)

male = InlineKeyboardButton('Male ♂️', callback_data='male')
female = InlineKeyboardButton('Female ♀️', callback_data='female')
sex_kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(male, female)

on = KeyboardButton('Aktifkan notifikasi 🔔')
off = KeyboardButton('Matikan notifikasi 🔕')
on_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Tukarkan 💎').add(on).add(to_main)
off_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Tukarkan 💎').add(off).add(to_main)

top = KeyboardButton('🏆 Peringkat')
statistic_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(top).add(to_main)

top_messages = KeyboardButton('🔝 5 teratas berdasarkan pesan')
top_likes = KeyboardButton('🔝 5 teratas berdasarkan suka')
top_refs = KeyboardButton('🔝 5 teratas berdasarkan referal')
top_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(top_messages).add(top_likes).add(top_refs).add(to_main)
