from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


to_main = KeyboardButton('🔙 Go to main')

cancel_search_kb = ReplyKeyboardMarkup(
    resize_keyboard=True).add('🚫 Cancel search')

stop_kb = ReplyKeyboardMarkup(one_time_keyboard=True,
                              resize_keyboard=True).add('🛑 Stop dialogue')

like = KeyboardButton('👍 Like')
dislike = KeyboardButton('👎 Not like')
next_dialog = KeyboardButton('➡️ Next dialogue')
search_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

like = KeyboardButton('👍 Like')
dislike = KeyboardButton('👎 Not like')
next_dialog = KeyboardButton('➡️ Next dialogue 💕')
search_male_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

like = KeyboardButton('👍 Like')
dislike = KeyboardButton('👎 Not like')
next_dialog = KeyboardButton('➡️ Next dialogue 📍')
search_female_kb = ReplyKeyboardMarkup(
    one_time_keyboard=True, resize_keyboard=True).row(like, dislike).add(next_dialog).add(to_main)

man = KeyboardButton('Couple 💕')
random = KeyboardButton('Random 🔀')
looking = KeyboardButton('Peaplo nearby 📍')
vip = KeyboardButton('VIP 👑')
rules = KeyboardButton('Rules 📖')
profile = KeyboardButton('Profil 👤')
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).row(man, random, looking).row(vip, rules, profile)

name = InlineKeyboardButton('🅰️ Name', callback_data='name')
age = InlineKeyboardButton('🔞 Age', callback_data='age')
sex = InlineKeyboardButton('👫 Gender', callback_data='sex')
country = InlineKeyboardButton('🌍 Country', callback_data='country')
city = InlineKeyboardButton('🏙️ City', callback_data='city')
settings_kb = InlineKeyboardMarkup(
    resize_keyboard=True).add(name).add(age).add(sex).add(country).add(city)

change_profile = KeyboardButton('⚙️ Edit profile')
statistic = KeyboardButton('📈 Statistics')
ref = KeyboardButton('💼 Referral')
profile_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(change_profile).add(
    statistic).add(ref).add(to_main)

vip_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('🆓 Dapatkan VIP secara gratis').add(
    '💰 Buy/Renew VIP').add(to_main)

day = KeyboardButton('👑 VIP / day')
week = KeyboardButton('👑 VIP / week')
month = KeyboardButton('👑 VIP / mouth')
buy_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(day).add(week).add(month).add(to_main)

to_main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(to_main)

male = InlineKeyboardButton('Male ♂️', callback_data='male')
female = InlineKeyboardButton('Female ♀️', callback_data='female')
sex_kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(male, female)

on = KeyboardButton('Enable notifications 🔔')
off = KeyboardButton('Turn off notifications 🔕')
on_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Exchange COIN ONS').add(on).add(to_main)
off_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Exchange COIN ONS').add(off).add(to_main)

top = KeyboardButton('🏆 Rating')
statistic_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(top).add(to_main)

top_messages = KeyboardButton('🔝 5 top based on message')
top_likes = KeyboardButton('🔝 5 top based on likes')
top_refs = KeyboardButton('🔝 5 top based on referrals')
top_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(top_messages).add(top_likes).add(top_refs).add(to_main)
