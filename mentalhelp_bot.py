import logging

import nest_asyncio

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InputFile

import asyncio
import time
import pandas as pd

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

API_TOKEN = ''
PROXY_URL = 'http://proxy.server:3128'

user_info = {}
result = {}

bot = Bot(token=API_TOKEN, proxy=PROXY_URL)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
HOST_ID = ''
DEL_KEYBOARD = types.ReplyKeyboardRemove()
list_for_columns = ['id', 'relation', 'username', 'name', 'gender', 'start_time', 'want_app', 'report', 'level_burnout', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20', 'q21', 'q22']


# States
class Form(StatesGroup):
    relation = State()
    name = State()  # Will be represented in storage as 'Form:name'
    gender = State()  # Will be represented in storage as 'Form:gender'
    job = State()
    test = State()
    questions_state = State()


class Report(StatesGroup):
    waiting = State()

class Result(StatesGroup):
    second_category = State()

@dp.message_handler(state='*', commands='debug')
async def debug(message: types.Message):
    if str(message.from_user.id) == HOST_ID:
        await message.answer("Количество участников: {}".format(len(user_info)))
        for i, chat_id in enumerate(user_info):
            if i == 6:
                break
            text = ''
            for inf in user_info[chat_id]:
                if inf != 'file':
                    text = text + str(inf) + ' : ' + str(user_info[chat_id][inf]) + '\n'
            await message.answer(text)
            # await message.answer("chat id: {}\nname: {}\nusername: {}\ngender: {}\nfullname: {}".format(chat_id,
            # user_info[chat_id]['name'], user_info[chat_id]['username'], user_info[chat_id]['gender'],
            # user_info[chat_id]['fullname']))
    else:
        await message.answer("Incorrect")

@dp.message_handler(state='*', commands='data')
async def exp_data(message: types.Message):
    if str(message.from_user.id) == HOST_ID:
        await message.answer_document(InputFile("user_info.csv"))

@dp.message_handler(commands='start')
@dp.message_handler(Text(equals='start', ignore_case=True))
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.relation.set()


    question = "Привет! Меня зовут Клио и я помогу преодолеть тебе психологические проблемы. Чтобы я могла лучше тебе " \
               "помогать, нам для начала нужно немного познакомиться. Как будет комфортнее на \"ты\" или на \"вы\"?' "
    await show_typing(message)
    await message.answer(question, reply_markup=get_keyboard_relation())


@dp.message_handler(content_types=['text'])
async def speak(message: types.Message):
    await show_typing(message)
    await message.answer("Нажми /start если хочешь узнать себя", reply_markup=types.ReplyKeyboardRemove())


def get_keyboard_relation():
    # Генерация клавиатуры.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Ты", "Вы")
    return markup


@dp.message_handler(state=Form.relation)
async def process_relation(message: types.Message, state: FSMContext):
    if message.text == 'Ты' or message.text == 'Вы':
        async with state.proxy() as data:
            data['relation'] = message.text

        user_info[message.chat.id] = {"relation": message.text}
        user_info[message.chat.id]['id'] = str(message.chat.id)
        user_info[message.chat.id]['username'] = message.from_user.username

        user_info[message.chat.id]['file'] = pd.DataFrame(columns = list_for_columns)
        user_info[message.chat.id]['file'] = user_info[message.chat.id]['file'].append(pd.DataFrame([[str(message.chat.id)]], columns=['id']), ignore_index=True)


        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'relation'] = message.text
        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'username'] = message.from_user.username


        await Form.next()
        await show_typing(message)
        if data['relation'] == 'Ты':
            await message.answer('Как я могу тебя называть?', reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer('Как я могу к вам обращаться?', reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.reply("Ошибка. Выберите вариант ответа, используя кнопки на клавиатуре Ты/Вы.")


@dp.message_handler(lambda message: message.text not in ["Ты", "Вы"], state=Form.relation)
async def process_relation_invalid(message: types.Message):
    await show_typing(message)
    return await message.reply("Ошибка. Выберите вариант ответа, используя кнопки на клавиатуре.")


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        user_info[message.chat.id]['name'] = message.text


        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'name'] = message.text


        if data['relation'] == 'Ты':
            text = 'Какой у тебя пол?'
        else:
            text = 'Ваш пол?'

    await Form.next()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("М", "Ж")
    markup.add("Другой")

    await show_typing(message)
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
    await show_typing(message)
    return await message.reply("Неправильно выбран пол. Используйте кнопки на клавиатуре.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['gender'] = message.text
        user_info[message.chat.id]['gender'] = message.text
        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'gender'] = message.text

        if data['relation'] == 'Ты':
            await message.answer('Какая у тебя профессия?', reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer('Какая у вас профессия?', reply_markup=types.ReplyKeyboardRemove())


    await Form.next()

@dp.message_handler(state=Form.job)
async def process_job(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardRemove()
    async with state.proxy() as data:
        data['gender'] = message.text
        user_info[message.chat.id]['job'] = message.text
        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'job'] = message.text

        if data['relation'] == "Ты":
            text = 'Давай оценим твое эмоциональное состояние. Сейчас я покажу тебе 22 утверждения о чувствах и ' \
                       'переживаниях, связанных с работой. Пожалуйста, прочитай внимательно каждое утверждение и реши, ' \
                       'чувствуешь ли ты себя таким образом на своей работе. Если у тебя никогда не было такого чувства, ' \
                       'выбирай ответ «никогда». Если у тебя было такое чувство, укажи, как часто ты его ощущал(а) в ' \
                       'течение последних месяцев. '
        else:
            text = 'Давайте оценим ваше эмоциональное состояние. Сейчас я покажу вам 22 утверждения о чувствах и ' \
                       'переживаниях, связанных с работой. Пожалуйста, прочитайте внимательно каждое утверждение и ' \
                       'решите, чувствуете ли вы себя таким образом на своей работе. Если у вас никогда не было такого ' \
                       'чувства, выбирайте ответ «никогда». Если у вас было такое чувство, укажите, как часто вы его ' \
                       'ощущали в течение последних месяцев. '
            # And send message
        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text('Приятно познакомиться,', md.bold(data['name'])),
                    md.text(text),
                    sep='\n',
                ),
                reply_markup=markup,
                parse_mode=ParseMode.MARKDOWN,
        )

        time.sleep(3)
        text = 'Нажми /test, когда будешь готов.' if data['relation'] == "Ты" else 'Нажмите /test, когда будете готовы.'
        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(text)
                )
            )
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

    user_info[message.chat.id]['counter'] = 1
    await bot.send_message(
            message.chat.id,
            md.text(
                md.text(str(user_info[message.chat.id]['counter']) + '. '+ questions[user_info[message.chat.id]['counter']])
            ),
            reply_markup=test_keyboard()
        )

    user_info[message.chat.id]['start_time'] = time.time()

    await Form.next()


@dp.message_handler(lambda message: message.text != "/test", state=Form.test)
async def wait_start_test(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        text = 'Чтобы начать, нажми /test.' if data['relation'] == "Ты" else 'Чтобы начать, нажмите /test.'
    await message.answer(text)


@dp.message_handler(state=Form.questions_state)
async def testing(message: types.Message, state: FSMContext):

    user_info[message.chat.id][f"q{user_info[message.chat.id]['counter']}"] = str(int(time.time() - user_info[message.chat.id]['start_time'])) + ' сек'

    user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], f"q{user_info[message.chat.id]['counter']}"] = str(int(time.time() - user_info[message.chat.id]['start_time'])) + ' сек'


    if user_info[message.chat.id]['counter'] == 1:
        result[message.chat.id] = {}
        result[message.chat.id][1] = analyze(message)
        result[message.chat.id][2] = 0
        result[message.chat.id][3] = 0
        if (analyze(message) == -1):
            await message.reply("Некорректный ответ.")
            incorrect_answer(1, message)

    elif user_info[message.chat.id]['counter'] in [2, 3, 8, 13, 14, 16, 2, 6]:
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

    #debug
    if message.text == 'Continue' and str(message.from_user.id) == HOST_ID:
      user_info[message.chat.id]['counter'] = 23

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

        user_info[message.chat.id]['start_time'] = time.ctime(user_info[message.chat.id]['start_time'])
        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'start_time'] = user_info[message.chat.id]['start_time']

        user_info[message.chat.id]['level_burnout'] = str(int(p*100))
        user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'level_burnout'] = str(int(p*100))

        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(user_info[message.chat.id]['name'] + ', а вот и результаты'),
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

        time.sleep(5)


        if int(p*100) < 46:
            await message.answer(relation_answer("У тебя низкий уровень выгорания("+ str(int(p*100)) + "/100), поэтому специальная помощь тебе не нужна. "\
                                                "Но ты можешь узнать себя лучше, для этого ниже будут три вопроса для самопознания. Можешь задавать их себе "\
                                                "каждый день перед сном или вставить в рабочий планер. Они помогут тебе осознать свои мысли, эмоции, а также "\
                                                "понять ценность себя.", "У вас низкий уровень выгорания("+ str(int(p*100)) + "/100), поэтому специальная помощь вам не нужна. Но вы можете "\
                                                "познакомиться с собой ближе, для этого ниже будут три вопроса для самопознания. Можете задавать их себе каждый "\
                                                "день перед сном или вставить в рабочий планер. Они помогут осознать свои мысли, эмоции, а также понять ценность себя.",message))
            await show_typing(message, 2)
            await message.answer("1) О чем я сегодня думал?\n2) Что я сегодня чувствовал?\n3) За что могу поблагодарить себя?")
            time.sleep(5)
            await suggest_app(message)
        elif int(p*100) < 66:
            await message.answer(relation_answer("У тебя средний уровень выгорания("+ str(int(p*100)) + "/100). Не бойся, ничего страшного не происходит, "\
            "но стоит обратить внимание на свои эмоции. Давай потренируемся вместе.\nНиже будут даны 3 пары эмоций. Тебе нужно "\
            "в каждой паре выбрать самую сильную эмоцию.", "У вас средний уровень выгорания("+ str(int(p*100)) + "/100). Не бойтесь, ничего страшного не "\
            "происходит, но стоит обратить внимание на свои эмоции. Давайте потренируемся вместе. Ниже будут даны 3 пары эмоций. "\
            "Вам нужно в каждой паре выбрать самую сильную эмоцию.", message))
            await show_typing(message, 2)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("Злость")
            markup.add("Ярость")
            await message.answer("Какая эмоция сильнее:\nзлость или ярость?", reply_markup = markup)
            await Result.second_category.set()
        else:

            await message.answer(relation_answer("У тебя высокий уровень выгорания("+ str(int(p*100)) + "/100). Не бойся, мы тебе поможем! " \
                                                "Ниже ты сможешь найти технику релаксации и контакты проверенного психолога",
                                                "У вас высокий уровень выгорания("+ str(int(p*100)) + "/100). Не переживайте, мы поможем! " \
                                                "Ниже вы сможете найти технику релаксации, контакты проверенного психолога и гайд.",
                                                message))

            await show_typing(message, 4)
            await message.answer(relation_answer("Теперь тебе нужно всего 5 минут времени.\nЛяг или выполняй упражнение сидя." \
                                                "\nЗакрой глаза, расслабь тело и не трогая, прочувствуй его от самых кончиков пальцев ног до макушки." \
                                                "\nМожешь включить музыку или представить себя в месте, где тебе тепло и уютно.",
                                                "Теперь вам нужно всего 5 минут времени. \nЛягте или выполняйте упражнение сидя." \
                                                "Закройте глаза, расслабьте тело и не трогая, прочувствуйте его от самых кончиков пальцев ног до макушки." \
                                                "\nМожете включить музыку или представить себя в месте, где тепло и уютно."
                                                ,message))

            await show_typing(message, 10)
            await message.answer("А еще мы предлагаем познакомиться с нашим проверенным психологом, "\
                                "она специализируется на когнитивно-поведенческой терапии."\
                                " Исследования показывают, что такой вид терапии самый эффективный.")

            await show_typing(message, 4)





            text = "Привет! Я Лера. \nЯ немного расскажу о себе: окончила факультет психологии МГПУ, "\
                                 "провела более 100 часов индивидуальной терапии. Еще во время обучения начала проходить "\
                                 "личную терапию, а сейчас у меня есть супервизор. Я могу помочь тебе справиться с этим состоянием, "\
                                 "напиши мне в телеграм, чтобы узнать подробнее.\nНаписать Лере - @ValeriaGorsh"

            # await message.answer("Привет! Я Лера. \nЯ немного расскажу о себе: окончила факультет психологии МГПУ, "\
            #                     "провела более 100 часов индивидуальной терапии. Еще во время обучения начала проходить "\
            #                     "личную терапию, а сейчас у меня есть супервизор. Я могу помочь тебе справиться с этим состоянием, "\
            #                     "напиши мне в телеграм, чтобы узнать подробнее.\nНаписать Лере - @ValeriaGorsh", )
            with open('photo_2021-08-26_13-11-39.jpg', 'rb') as photo:
                await message.answer_photo(photo, caption=text)

            time.sleep(5)
            await suggest_app(message)

    else:
        await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(str(user_info[message.chat.id]['counter']) + '. '+ questions[user_info[message.chat.id]['counter']])
                ),
                reply_markup=test_keyboard()
            )
        user_info[message.chat.id]['start_time'] = time.time()


@dp.message_handler(state=Result.second_category)
async def second_category_help(message: types.Message, state: FSMContext):

    if message.text == "Злость":
        await message.answer("Не совсем верно, ведь ярость это более сильная эмоция за счет потери контроля, в этом состоянии мы находимся в афекте", reply_markup=DEL_KEYBOARD)
        await show_typing(message, 2)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Тревога")
        markup.add("Опасение")
        await message.answer("Какая эмоция сильнее:\nтревога или опасение?", reply_markup = markup)
    elif message.text == "Ярость":
        await message.answer("Верно! Злость мы можем контролировать и можем подавить при желании",reply_markup=DEL_KEYBOARD)
        await show_typing(message, 2)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Тревога")
        markup.add("Опасение")
        await message.answer("Какая эмоция сильнее:\nтревога или опасение?", reply_markup = markup)

    elif message.text == "Тревога":
        await message.answer("Верно. Тревога сильная эмоция из-за того что мы не можем осознать ее причины",reply_markup=DEL_KEYBOARD)
        await show_typing(message, 2)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Счастье")
        markup.add("Восторг")
        await message.answer("Какая эмоция сильнее:\nсчастье или восторг?", reply_markup = markup)
    elif message.text == "Опасение":
        await message.answer("Не совсем. Опасения всегда предметны. Они возникают у нас из-за различных ситуаций и очень осознаются нами",reply_markup=DEL_KEYBOARD)
        await show_typing(message, 2)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Счастье")
        markup.add("Восторг")
        await message.answer("Какая эмоция сильнее:\nсчастье или восторг?", reply_markup = markup)

    elif message.text == "Счастье":
        await message.answer("Это здорово, что ты так понимаешь свои чувства",reply_markup=DEL_KEYBOARD)
        await state.finish()
        time.sleep(3)
        await suggest_app(message)


    elif message.text == "Восторг":
        await message.answer("Счастье - более долговременная и сильная эмоция",reply_markup=DEL_KEYBOARD)
        await state.finish()
        time.sleep(3)
        await suggest_app(message)



async def suggest_app(message):
    user_info[message.chat.id]['want_app'] = 'No'
    user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'want_app'] = 'No'
    await message.answer('Хочешь получить дополнительные материалы, упражнения и помощь экспертов?\n' + md.bold('Скачивай приложение') + ' ⬇',
                            reply_markup=app_moving_keyboard(),
                            parse_mode=ParseMode.MARKDOWN)
    time.sleep(1)
    loop = asyncio.get_event_loop()
    loop.create_task(alarm_report(message))
    loop.create_task(export_data(message))


async def export_data(message):
    await asyncio.sleep(120)
    df = pd.read_csv('user_info.csv')
    df = df.append(user_info[message.chat.id]['file'], ignore_index=True)
    df.to_csv('user_info.csv', index=False)

async def alarm_report(message):

    await asyncio.sleep(10)
    await message.answer(relation_answer("Ты можешь оставить", "Вы можете оставить",
                                             message) + " свой отзыв и получить гайд по эмоциональному выгоранию!",
                             reply_markup=report_keyboard())




def app_moving_keyboard():
    # Генерация клавиатуры.
    buttons = [
        types.InlineKeyboardButton(text="Приложение Mental Help", callback_data="cb_MH_app"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    return keyboard


def report_keyboard():
    buttons = [
        types.InlineKeyboardButton(text="Оставить отзыв и получить гайд", callback_data="cb_report"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    return keyboard


@dp.callback_query_handler(text='cb_MH_app')
async def callbacks_app_moving(call: types.CallbackQuery):
    if user_info.get(call.message.chat.id) != None:
        if user_info[call.message.chat.id].get('want_app') != None:
            user_info[call.message.chat.id]['want_app'] = 'Yes'
            user_info[call.message.chat.id]['file'].at[user_info[call.message.chat.id]['file'].loc[user_info[call.message.chat.id]['file']['id']==str(call.message.chat.id)].index[0], 'want_app'] = 'Yes'
            await call.answer(text="Приложение сейчас в разработке. \nМы обязательно оповестим " + (
                    'тебя' if user_info[call.message.chat.id]['relation'] == 'Ты' else 'вас') + ", когда оно будет готово!",
                                  show_alert=True)



@dp.callback_query_handler(text='cb_report')
async def callbacks_report(call: types.CallbackQuery):
    await Report.waiting.set()
    await call.message.answer(relation_answer("Твое", "Ваше",
                                              call.message) + " следующее сообщение будет автоматически считаться "
                                                              "отзывом. " + relation_answer(
        "Напиши", "Напишите", call.message) + " в нем все, что " + relation_answer("тебе", "вам",
                                                                                   call.message) + " понравилось и не "
                                                                                                   "понравилось.")
    await call.answer()


@dp.message_handler(state=Report.waiting)
async def report_recieve(message: types.Message, state: FSMContext):
    user_info[message.chat.id]['report'] = message.text
    user_info[message.chat.id]['file'].at[user_info[message.chat.id]['file'].loc[user_info[message.chat.id]['file']['id']==str(message.chat.id)].index[0], 'report'] = message.text

    await message.answer(
        "Спасибо за отзыв!\n" + relation_answer("Держи", "Держите", message) + " обещанный гайд" + ' ⬇')


    await message.answer_document(InputFile("Гайд.pdf"))
    await state.finish()


def relation_answer(str1, str2, message):
    if user_info[message.chat.id]['relation'] == 'Ты':
        return str1
    else:
        return str2


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


async def show_typing(message, wait=1):
    await bot.send_chat_action(message.chat.id, "typing")
    time.sleep(wait)


questions = {
    1: 'Я чувствую себя эмоционально опустошенной/ым		',

    2: 'После работы я чувствую себя как «выжатый лимон»',

    3: 'Утром я чувствую усталость и нежелание идти на работу',

    4: "Я хорошо понимаю, что чувствуют мои подчиненные и коллеги, и стараюсь учитывать это в интересах дела",

    5: "Я чувствую, что общаюсь с некоторыми подчиненными и коллегами как с предметами (без теплоты и расположения к "
       "ним)",

    6: "Я чувствую себя энергичной/ым и эмоционально воодушевленной/ым",

    7: "Я умею находить правильное решение в конфликтных ситуациях, возникающих при общении с коллегами",

    8: 'Я чувствую угнетенность и апатию		',

    9: 'Я уверен/а, что моя работа нужна людям	',

    10: 'В последнее время я чувствую свою чёрствость по отношению к тем, с кем работаю	',

    11: 'Я замечаю, что моя работа ожесточает меня		',

    12: 'У меня много планов на будущее, и я верю в их осуществление.		',

    13: 'Моя работа все больше меня разочаровывает	',

    14: 'Мне кажется, что я слишком много работаю		',

    15: 'Бывает, что мне действительно безразлично то, что происходит c некоторыми моими подчиненными и коллегами	',

    16: 'Мне хочется уединиться и отдохнуть от всего и всех		',

    17: 'Я легко могу создать атмосферу доброжелательности и сотрудничества в коллективе		',

    18: 'Во время работы я чувствую приятное оживление		',

    19: 'Благодаря своей работе я уже сделал/а в жизни много действительно ценного		',

    20: 'Я чувствую равнодушие и потерю интереса ко многому, что радовало меня в моей работе		',

    21: 'На работе я спокойно справляюсь с эмоциональными проблемами		',

    22: 'В последнее время мне кажется, что коллеги и подчиненные все чаще перекладывают на меня груз своих проблем и '
        'обязанностей '
}

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
