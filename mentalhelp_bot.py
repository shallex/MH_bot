#!pip install aiogram

import csv
import logging

import nest_asyncio
nest_asyncio.apply()

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

API_TOKEN = '1997577729:AAFCu_AWn4b7QQbvHO2l5rWlphjL-V-7NyY'
PROXY_URL = 'http://proxy.server:3128'
headings = ["id", "username", "relation", "name", "gender"]

user_info = {}
result = {}
FILENAME = "user_info.csv"


#bot = Bot(token=API_TOKEN, proxy=PROXY_URL)
bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
HOST_ID = '540276455'

# States
class Form(StatesGroup):
    relation = State()
    name = State()  # Will be represented in storage as 'Form:name'
    gender = State()  # Will be represented in storage as 'Form:gender'
    test = State()
    questions_state = State()

@dp.message_handler(state='*', commands='debug')
async def debug(message: types.Message):
    if str(message.from_user.id) == HOST_ID:
        await message.answer("Количество участников: {}".format(len(user_info)))
        for i, chat_id in enumerate(user_info):
            if i == 6:
                break
            await message.answer("chat id: {}\nname: {}\nusername: {}\ngender: {}".format(chat_id, user_info[chat_id]['name'], user_info[chat_id]['username'], user_info[chat_id]['gender']))
    else:
        await message.answer("Incorrect")


@dp.message_handler(commands='start')
@dp.message_handler(Text(equals='start', ignore_case=True))
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.relation.set()
    
    question = "Привет! Меня зовут ... и я помогу преодолеть тебе психологические проблемы. Чтобы я могла лучше тебе помогать, нам для начала нужно немного познакомиться. Как будет комфортнее на \"ты\" или на \"вы\"?'"
    await message.answer(question, reply_markup=get_keyboard_relation())

@dp.message_handler(content_types=['text'])
async def speak(message: types.Message):
    await message.answer("Нажми /start если хочешь узнать себя", reply_markup=types.ReplyKeyboardRemove())


def get_keyboard_relation():
    # Генерация клавиатуры.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Ты", "Вы")
    return markup


@dp.message_handler(state=Form.relation)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['relation'] = message.text

    user_info[message.chat.id] = {"relation": message.text}
    user_info[message.chat.id]['id'] = message.from_user.id
    user_info[message.chat.id]['username'] = message.from_user.username

    await Form.next()
    if data['relation'] == 'Ты':
        await message.answer('Как я могу тебя называть?', reply_markup = types.ReplyKeyboardRemove())
    else:
        await message.answer('Как я могу к вам обращаться?', reply_markup = types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: message.text not in ["Ты", "Вы"], state=Form.relation)
async def process_relation_invalid(message: types.Message):
    return await message.reply("Ошибка. Выберите вариант ответа, используя кнопки на клавиатуре.")


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    text = ''
    async with state.proxy() as data:
        data['name'] = message.text
        user_info[message.chat.id]['name'] = message.text
        if data['relation'] == 'Ты':
            text = 'Какой у тебя пол?'
        else:
            text = 'Ваш пол?'

    # with open("user_info.csv", "w") as file:
    #   data_writer = csv.DictWriter(file, fieldnames=headings)
    #   data_writer.writeheader()
    #   data_writer.writerow({"name":  message.text})

    await Form.next()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("М", "Ж")
    markup.add("Другой")

    await message.answer(text, reply_markup=markup)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())



@dp.message_handler(lambda message: message.text not in ["М", "Ж", "Другой"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    return await message.reply("Неправильно выбран пол. Используйте кнопки на клавиатуре.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text
        user_info[message.chat.id]['gender'] = message.text

        # with open(FILENAME, "w", newline='') as csv_file:
        # writer = csv.writer(csv_file, delimiter=',')
        # for line in data:
        #     writer.writerow(line)

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()
        text = 'Напиши /test, когда будешь готов.' if data['relation'] == "Ты" else 'Напишите /test, когда будете готовы.'
        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Приятно познакомиться,', md.bold(data['name'])),
                md.text('Теперь мы можем приступить к тестированию.'),
                md.text(text),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    # Finish conversation
    # await state.finish()
    await Form.next()


def test_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Никогда")
    markup.add("Очень редко")
    markup.add("Редко")
    markup.add("Иногда")
    markup.add("Часто")
    markup.add("Очень часто")
    markup.add("Ежедневно")
    return markup
	

	
@dp.message_handler(state=Form.test, commands="test")
@dp.message_handler(Text(equals='test', ignore_case=True), state=Form.test)
async def start_test(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Ты", "Вы")

    async with state.proxy() as data:

        if data['relation'] == "Ты":
            text = 'Давай оценим твое эмоциональное состояние. Сейчас я покажу тебе 22 утверждения о чувствах и переживаниях, связанных с работой. Пожалуйста, прочитай внимательно каждое утверждение и реши, чувствуешь ли ты себя таким образом на своей работе. Если у тебя никогда не было такого чувства, выбирай ответ «никогда». Если у тебя было такое чувство, укажи, как часто ты его ощущал(а) в течение последних месяцев.'
        else:
            text = 'Давайте оценим ваше эмоциональное состояние. Сейчас я покажу вам 22 утверждения о чувствах и переживаниях, связанных с работой. Пожалуйста, прочитайте внимательно каждое утверждение и решите, чувствуете ли вы себя таким образом на своей работе. Если у вас никогда не было такого чувства, выбирайте ответ «никогда». Если у вас было такое чувство, укажите, как часто вы его ощущали в течение последних месяцев.'

    await bot.send_message(
            message.chat.id,
            md.text(
                md.text(text)
            )
        )
    user_info[message.chat.id]['counter'] = 1
    await bot.send_message(
            message.chat.id,
            md.text(
                md.text(user_info[message.chat.id]['counter'], ". ", questions[user_info[message.chat.id]['counter']])
            ),
            reply_markup=test_keyboard()
        )
    
    await Form.next()

@dp.message_handler(lambda message: message.text != "/test", state=Form.test)
async def wait_start_test(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        text = 'Чтобы начать, напиши /test.' if data['relation'] == "Ты" else 'Чтобы начать, напишите /test.'
    await message.answer(text)

@dp.message_handler(state=Form.questions_state)
async def testing(message: types.Message, state: FSMContext):

    if user_info[message.chat.id]['counter'] == 1:
        result[message.chat.id] = {}
        result[message.chat.id][1] = analyze(message)
        result[message.chat.id][2] = 0
        result[message.chat.id][3] = 0
        if (analyze(message) == -1):
            await message.reply("Некорректный ответ.")
            incorrect_answer(1, message)
    elif user_info[message.chat.id]['counter'] in [1, 2, 3, 8, 13, 14, 16, 2, 6]:
        if user_info[message.chat.id]['counter'] == 6:
            result[message.chat.id][1] +=  (6 - analyze(message))
        else:
            result[message.chat.id][1] += analyze(message)

        if (analyze(message) == -1):
            incorrect_answer(1, message)
            await message.reply("Некорректный ответ.")

    elif user_info[message.chat.id]['counter'] in [5, 10, 11, 15, 22]:
        result[message.chat.id][2] += analyze(message)
        if (analyze(message) == -1):
            incorrect_answer(2, message)
            await message.reply("Некорректный ответ.")
    else:
        result[message.chat.id][3] += analyze(message)
        if (analyze(message) == -1):
            incorrect_answer(3, message)
            await message.reply("Некорректный ответ.")


    user_info[message.chat.id]['counter'] += 1
    if user_info[message.chat.id]['counter'] == 23:
        if result[message.chat.id][1] < 16:
            text1 = "Низкий"
        elif result[message.chat.id][1] < 25:
            text1 = 'Средний'
        else:
            text1 = 'Высокий'

        if result[message.chat.id][1] < 6:
            text2 = "Низкий"
        elif result[message.chat.id][1] < 11:
            text2 = 'Средний'
        else:
            text2 = 'Высокий'

        if result[message.chat.id][1] > 36:
            text3 = "Низкий"
        elif result[message.chat.id][1] > 30:
            text3 = 'Средний'
        else:
            text3 = 'Высокий'

        p = (((result[message.chat.id][1]/54)**2 + (result[message.chat.id][2]/30)**2 + (result[message.chat.id][3]/48)**2 )/3) ** (0.5)

        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text('А вот и результаты'),
                    md.text('Уровень эмоционального истощения: ', md.bold(text1)),
                    md.text('Уровень деперсонализации: ', md.bold(text2)),
                    md.text('Уровень редукции профессионализма: ', md.bold(text3)),
                    md.text('Общий уровень эмоционального выгорания: ', md.bold(int(p*100), "/ 100")),
                    sep='\n',
                ),
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
            )
        await state.finish()

    else:
        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(user_info[message.chat.id]['counter'], ". ",questions[user_info[message.chat.id]['counter']])
                ),
                reply_markup=test_keyboard()
            )


def incorrect_answer(n, message):
    result[message.chat.id][n] += 1
    user_info[message.chat.id]['counter'] -= 1

def analyze(message):
    if message.text == "Никогда":
        return 0
    elif message.text == "Очень редко":
        return 1
    elif message.text == "Редко":
        return 2
    elif message.text == "Иногда":
        return 3
    elif message.text == "Часто":
        return 4
    elif message.text == "Очень часто":
        return 5
    elif message.text == "Ежедневно":
        return 6
    else:
        return -1
    

questions = {
    1 : 'Я чувствую себя эмоционально опустошенной/ым		',
			
2 : 'После работы я чувствую себя как «выжатый лимон»',

3 : 'Утром я чувствую усталость и нежелание идти на работу'	,

4 : "Я хорошо понимаю, что чувствуют мои подчиненные и коллеги, и стараюсь учитывать это в интересах дела",		

5 : "Я чувствую, что общаюсь с некоторыми подчиненными и коллегами как с предметами (без теплоты и расположения к ним)"	,	

6 : "Я чувствую себя энергичной/ым и эмоционально воодушевленной/ым"	,

7 : "Я умею находить правильное решение в конфликтных ситуациях, возникающих при общении с коллегами"		,
			
8 : 'Я чувствую угнетенность и апатию		',
	
9 : 'Я уверен/а, что моя работа нужна людям	'	,
	
10 : 'В последнее время я стал/а более «черствой» по отношению к тем, с кем работаю	'	,
	
11 : 'Я замечаю, что моя работа ожесточает меня		',
	
12 : 'У меня много планов на будущее, и я верю в их осуществление.		',
	
13 : 'Моя работа все больше меня разочаровывает	'	,
	
14 : 'Мне кажется, что я слишком много работаю		',
		
15 : 'Бывает, что мне действительно безразлично то, что происходит c некоторыми моими подчиненными и коллегами	'	,
	
16 : 'Мне хочется уединиться и отдохнуть от всего и всех		',
	
17 : 'Я легко могу создать атмосферу доброжелательности и сотрудничества в коллективе		',
	
18 : 'Во время работы я чувствую приятное оживление		',
				
19 : 'Благодаря своей работе я уже сделал/а в жизни много действительно ценного		',
	
20 : 'Я чувствую равнодушие и потерю интереса ко многому, что радовало меня в моей работе		',
		
21 : 'На работе я спокойно справляюсь с эмоциональными проблемами		',
	
22 : 'В последнее время мне кажется, что коллеги и подчиненные все чаще перекладывают на меня груз своих проблем и обязанностей		'

}





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
