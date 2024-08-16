import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '--'

# Создаем экземпляр бота
bot = Bot(token=API_TOKEN)

# Создаем диспетчер с хранилищем состояний в памяти
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Определяем группу состояний
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

# Создаем обычную клавиатуру
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Рассчитать'), KeyboardButton('Информация'))

# Создаем Inline клавиатуру
inline_kb = InlineKeyboardMarkup(row_width=1)
inline_kb.add(InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories'))
inline_kb.add(InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas'))

# Функция, обрабатывающая команду /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        'Привет! Я бот, помогающий твоему здоровью. Нажмите "Рассчитать", чтобы начать расчет нормы калорий.',
        reply_markup=keyboard
    )

# Функция для отображения Inline меню
@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.reply('Выберите опцию:', reply_markup=inline_kb)

# Функция для отображения формул
@dp.callback_query_handler(lambda c: c.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_text = ("Формула Миффлина-Сан Жеора для расчета нормы калорий:\n\n"
                    "Для мужчин: (10 * вес (кг)) + (6.25 * рост (см)) - (5 * возраст) + 5\n"
                    "Для женщин: (10 * вес (кг)) + (6.25 * рост (см)) - (5 * возраст) - 161")
    await call.message.answer(formula_text)
    await call.answer()

# Функция для установки возраста
@dp.callback_query_handler(lambda c: c.data == 'calories', state=None)
async def set_age(call: types.CallbackQuery):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()
    await call.answer()

# Функция для установки роста
@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply('Введите свой рост (в см):')
    await UserState.growth.set()

# Функция для установки веса
@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await message.reply('Введите свой вес (в кг):')
    await UserState.weight.set()

# Функция для расчета и отправки нормы калорий
@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)

    data = await state.get_data()

    # Добавлена обработка ошибок для случая, если пользователь введет некорректные данные.
    try:
        age = int(data['age'])
        growth = int(data['growth'])
        weight = int(data['weight'])

        # Расчет по формуле Миффлина-Сан Жеора для мужчин
        calories = int(10 * weight + 6.25 * growth - 5 * age + 5)

        await message.reply(f"Ваша норма калорий: {calories} ккал в день", reply_markup=keyboard)
    except ValueError:
        await message.reply("Ошибка в введенных данных. Пожалуйста, убедитесь, что вы ввели числовые значения.", reply_markup=keyboard)

    await state.finish()

# Функция, обрабатывающая все остальные сообщения
@dp.message_handler()
async def all_messages(message: types.Message):
    if message.text == 'Информация':
        await message.reply('Этот бот поможет вам рассчитать норму калорий. Нажмите "Рассчитать", чтобы начать.', reply_markup=keyboard)
    else:
        await message.reply('Введите команду /start, чтобы начать общение или нажмите "Рассчитать" для расчета нормы калорий.', reply_markup=keyboard)

if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)