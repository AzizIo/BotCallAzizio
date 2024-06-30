import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException

# Замените 'YOUR_TOKEN' на токен вашего бота
TOKEN = '6792587986:AAE25IiNYBeej9bqGEvfluS_dp0RGoI0dRA'

# Замените 'YOUR_CHAT_ID' на ID вашего чата
YOUR_CHAT_ID = '6106008654'

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения заблокированных пользователей
blocked_users = set()

# Словарь для хранения всех пользователей
all_users = {}

# Функция для проверки является ли пользователь администратором
def is_admin(user_id):
    return str(user_id) == YOUR_CHAT_ID


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! напиши сообщение чтобы я передал его администратору " )
# Обработчик всех сообщений от пользователей
@bot.message_handler(func=lambda message: message.chat.id != int(YOUR_CHAT_ID))
def handle_message(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "🚫 Вы были заблокированы")
        return

    all_users[user_id] = {'username': message.from_user.username, 'blocked': False}
    bot.send_message(YOUR_CHAT_ID, f"💬 Новое сообщение \n\nName:{message.from_user.first_name}\ntg:@{all_users[user_id]['username']} \n\n➖➖➖\n{message.text}\n➖➖➖", reply_markup=create_reply_keyboard(user_id))
    bot.send_message(message.chat.id, "⏳ Ваше сообщение успешно отправлено! Пожалуйста, ожидайте")

# Обработчик команд от администратора
@bot.message_handler(commands=['admin'])
def handle_admin_commands(message):
    if is_admin(message.chat.id):
        bot.send_message(message.chat.id, "💎 Админ панель", reply_markup=create_admin_panel())
    else:
        bot.send_message(message.chat.id, "😔 Вы не являетесь администратором")

# Обработчик инлайн-кнопок "Ответить", "Заблокировать" и "Разблокировать"
@bot.callback_query_handler(func=lambda call: call.message and call.message.chat.id == int(YOUR_CHAT_ID))
def callback_handler(call):
    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])

    if action == 'reply':
        bot.send_message(call.message.chat.id, "👌 Введите ответ на сообщение:")
        bot.register_next_step_handler(call.message, lambda message: send_reply(user_id, message, call.message.chat.id))
    elif action == 'block':
        blocked_users.add(user_id)
        if user_id in all_users:
            all_users[user_id]['blocked'] = True
        else:
            all_users[user_id] = {'username': None, 'blocked': True}
        try:
            bot.send_message(user_id, "🚫 Вы были заблокированы")
        except ApiTelegramException:
            bot.send_message(call.message.chat.id, f"💔 Ошибка: Пользователь {all_users[user_id]['username']} заблокировал бота")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_reply_keyboard(user_id, blocked=True))
    elif action == 'unblock':
        blocked_users.remove(user_id)
        if user_id in all_users:
            all_users[user_id]['blocked'] = False
        try:
            bot.send_message(user_id, "❤️‍🩹 Вы были разблокированы")
        except ApiTelegramException:
            bot.send_message(call.message.chat.id, f"💔Ошибка: Пользователь {all_users[user_id]['username']} заблокировал бота")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_reply_keyboard(user_id, blocked=False))
    elif action == 'listusers':
        send_user_list(call.message.chat.id)
    elif action == 'broadcast':
        bot.send_message(call.message.chat.id, "✍️ Введите сообщение для рассылки:")
        bot.register_next_step_handler(call.message, send_broadcast)

# Функция для отправки ответа пользователю
def send_reply(user_id, message, chat_id):
    try:
        bot.send_message(user_id, f"⭕️ Вам пришел ответ:\n\n➖➖➖\n{message.text}\n➖➖➖")
        bot.send_message(chat_id, "✅ Ваш ответ успешно отправлен!")
    except ApiTelegramException:
        bot.send_message(chat_id, f"💔 Ошибка: Пользователь @{all_users[user_id]['username']} заблокировал бота")

# Функция для отправки списка пользователей администратору
def send_user_list(chat_id):
    if all_users:
        user_list = "\n".join([f"@{user_info['username']} - {'🔴 Заблокирован' if user_info['blocked'] else ' 🟢 В доступе'}" for user_id, user_info in all_users.items()])
        bot.send_message(chat_id, f"📄 Список пользователей:\n{user_list}")
    else:
        bot.send_message(chat_id, "Список пользователей пуст")

# Функция для отправки рассылки всем пользователям
def send_broadcast(message):
    total_users = len(all_users)
    success_count = 0

    for user_id in all_users:
        try:
            bot.send_message(user_id, message.text)
            success_count += 1
        except ApiTelegramException:
            bot.send_message(YOUR_CHAT_ID, f"Ошибка: Пользователь {all_users[user_id]['username']} заблокировал бота")
        bot.send_message(YOUR_CHAT_ID, f"✅ Рассылка успешно отправлена: \n {success_count} из {total_users} пользователей получили сообщение")

# Создаем клавиатуру с кнопками "Ответить" и "Заблокировать"
def create_reply_keyboard(user_id, blocked=False):
    reply_keyboard = InlineKeyboardMarkup()
    if blocked:
        reply_keyboard.row(
            InlineKeyboardButton("🥶 Разблокировать", callback_data=f'unblock_{user_id}')
        )
    else:
        reply_keyboard.row(
            InlineKeyboardButton("♻️ Ответить", callback_data=f'reply_{user_id}'),
            InlineKeyboardButton("🖕 Заблокировать", callback_data=f'block_{user_id}')
        )
    return reply_keyboard

# Создаем клавиатуру админ-панели
def create_admin_panel():
    admin_keyboard = InlineKeyboardMarkup()
    admin_keyboard.row(
        InlineKeyboardButton("📋 Список пользователей", callback_data='listusers_0'),
        InlineKeyboardButton("📝 Рассылка", callback_data='broadcast_0')
    )
    return admin_keyboard

# Запускаем бота
bot.polling()
