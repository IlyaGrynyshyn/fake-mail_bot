import logging
import json
import asyncio
import sqlite3
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import API_TOKEN, admin
import keyboard as kb
from onesec_api import Mailbox


storage = MemoryStorage()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


connection = sqlite3.connect('data.db')
q = connection.cursor()

q.execute('CREATE TABLE IF NOT EXISTS users (user_id integer)')
connection.commit()


class sender(StatesGroup):
    text = State()


@dp.message_handler(content_types=['text'], text='✉️ Отримати пошту')
async def takeamail(m: types.Message):
    ma = Mailbox('')
    email = f'{ma._mailbox_}@1secmail.com'
    await m.answer(
        '📫 Ось твоя пошта: {}\nНадсилай листа.\n'
        'Пошта перевіряється автоматично, кожні 5 секунд, якщо прийде новий лист, ми вас про це повідомимо!\n\n'
        '<b>Працездатність пошти – 10 хвилин!</b>'.format(email), parse_mode='HTML')
    timeout = 600
    timer = {}
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        test = 0
        if test == 5:
            break
        test -= 1
        mb = ma.filtred_mail()
        if mb != 'not found':
            for i in mb:
                if i not in timer:
                    timer[i] = i
                    if isinstance(mb, list):
                        mf = ma.mailjobs('read', mb[0])
                        js = mf.json()
                        fromm = js['from']
                        theme = js['subject']
                        mes = js['textBody']
                        await m.answer(f'📩 Новий лист:\n<b>От</b>: {fromm}\n<b>Тема</b>: {theme}\n<b>Повідомлення</b>: {mes}', reply_markup=kb.menu, parse_mode='HTML')
                        continue
        await asyncio.sleep(5)


@dp.message_handler(content_types=['text'], text='🔐 Випадковий пароль')
async def randompass(m: types.Message):
    ma = Mailbox('')
    passw = ma.rand_pass_for()
    await m.answer(f'🔑 Я згенерував для тебе пароль, тримай: `{passw}`\n\n*Згенерований пароль нікому не видно, можеш не турбуватися*', parse_mode='MarkdownV2')


@dp.message_handler(commands=['admin'])
async def adminstration(m: types.Message):
    if m.chat.id == admin:
        await m.answer('Ласкаво просимо до адмін панель.', reply_markup=kb.apanel)
    else:
        await m.answer('Чорт! Ти мене зламав :(')


@dp.message_handler(content_types=['text'])
async def texthandler(m: types.Message):
    q.execute(f"SELECT * FROM users WHERE user_id = {m.chat.id}")
    result = q.fetchall()
    if len(result) == 0:
        uid = 'user_id'
        sql = 'INSERT INTO users ({}) VALUES ({})'.format(uid, m.chat.id)
        q.execute(sql)
        connection.commit()
    await m.answer(f'Вітаю тебе, {m.from_user.mention}\nЦей бот створений для швидкого отримання тимчасової пошти.\nВикористовуйте кнопки нижче 👇', reply_markup=kb.menu)


@dp.callback_query_handler(text='stats')
async def statistics(call):
    row = q.execute('SELECT * FROM users').fetchall()
    lenght = len(row)
    await call.message.answer('Усього користувачів: {}'.format(lenght))


@dp.callback_query_handler(text='rass')
async def usender(call):
    await call.message.answer('Введіть текст для розсилки.\n\nЩоб скасувати, натисніть кнопку нижче 👇', reply_markup=kb.back)
    await sender.text.set()


@dp.message_handler(state=sender.text)
async def process_name(message: types.Message, state: FSMContext):
    info = q.execute('SELECT user_id FROM users').fetchall()
    if message.text == 'Відміна':
        await message.answer('Відміна! Повертаю до головного меню.', reply_markup=kb.menu)
        await state.finish()
    else:
        await message.answer('Починаю розсилку...', reply_markup=kb.menu)
        for i in range(len(info)):
            try:
                await bot.send_message(info[i][0], str(message.text))
            except:
                pass
        await message.answer('Розсилка завершена.')
        await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)  # Запуск
