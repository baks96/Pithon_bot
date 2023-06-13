import logging
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram.utils.request import Request

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния диалога с пользователем
LOGIN, PASSWORD, ORDERS = range(3)


# Функция для выполнения входа на сайт
def login(username, password):
    login_url = 'https://dev-piton.aup.kg/login'
    session = requests.Session()
    login_data = {
        'username': username,
        'password': password
    }
    session.post(login_url, data=login_data)
    return session


# Функция для получения заказов
def get_orders(session):
    orders_url = 'https://dev-piton.aup.kg/deals/orders/sell'
    response = session.get(orders_url)
    soup = BeautifulSoup(response.content, 'html.parser')


    orders = soup.find_all('div', class_='order')
    order_info = []
    for order in orders:
        # Извлекаем необходимую информацию о заявке
        order_info.append(order.text.strip())
    return order_info


# Обработчик команды /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет! Я телеграм-бот для выполнения входа на веб-сайт.")


# Обработчик команды /loginrequest
def login_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите ваш логин:")
    return LOGIN


# Обработчик ввода логина
def handle_login(update, context):
    context.user_data['login'] = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите ваш пароль:")
    return PASSWORD


# Обработчик ввода пароля
def handle_password(update, context):
    username = context.user_data.get('login')
    password = update.message.text
    session = login(username, password)

    if session:
        context.user_data['session'] = session
        orders = get_orders(session)

        if orders:
            message = '\n'.join(orders)
        else:
            message = 'Нет доступных заявок'

        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return ORDERS
    else:
        message = 'Ошибка при выполнении входа'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return ConversationHandler.END


# Обработчик команды /orders
def orders_command(update, context):
    session = context.user_data.get('session')
    if session:
        orders = get_orders(session)

        if orders:
            message = '\n'.join(orders)
        else:
            message = 'Нет доступных заявок'
    else:
        message = 'Выполните вход с помощью команды /login'

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


# Функция для запуска бота
def main():
    # Создаем объект Request с установкой размера пула соединений
    request = Request(con_pool_size=8)

    # Создаем объект Bot и передаем ему токен вашего бота и объект Request
    bot = Bot(token='6013445400:AAGxXN9oMk_YgOkNAEeONKfnfacanoV5n3Y', request=request)

    #  объект Updater и передаем ему объект Bot
    updater = Updater(bot=bot)

    #  регистратор обработчиков из объекта Updater
    dispatcher = updater.dispatcher

    #  обработчики команд
    dispatcher.add_handler(CommandHandler('loginrequest', login_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [CommandHandler('login', login_command)],
            PASSWORD: [MessageHandler(Filters.text, handle_password)],
            ORDERS: [CommandHandler('orders', orders_command)]
        },
        fallbacks=[],
    )
    dispatcher.add_handler(conv_handler)

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота
    updater.idle()


if __name__ == '__main__':
    main()
