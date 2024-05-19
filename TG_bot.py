import telebot
import mysql.connector
from mysql.connector import Error
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import time
import requests


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


bot = telebot.TeleBot("ТУТ ВАШ API TELEGRAM")


db_config_search = {
    'host': 'ВАШ ХОСТ',
    'user': 'ЮЗЕР',
    'password': 'ПАРОЛЬ',
    'database': 'БД'
}


db_config_write = {
    'host': 'ВАШ ХОСТ',
    'user': 'ЮЗЕР',
    'password': 'ПАРОЛЬ',
    'database': 'БД'
}


def db_connection(config):
    try:
        connection = mysql.connector.connect(**config)
        logging.info("Успешное подключение к базе данных")
        return connection
    except Error as db_error:
        logging.error(f"Ошибка при подключении к базе данных: {db_error}")
        return None


def execute_query(connection, query, data=None):
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, data)
            return cursor.fetchall()
        except Error as query_error:
            logging.error(f"Ошибка при выполнении SQL-запроса: {query_error}")
            return []


def log_request(commands_text, sql_req_user):
    query = """
    INSERT INTO history_of_data (commands_text, commands_datetime, SQL_req_user)
    VALUES (%s, NOW(), %s);
    """
    with db_connection(db_config_write) as connection:
        if connection:
            execute_query(connection, query, (commands_text, sql_req_user))
            connection.commit()
            logging.info("Запрос успешно сохранен в таблицу истории на сервере для записи")


def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error(f"Ошибка проверки URL: {e}")
        return False


def search_by_keyword(message, page=1):
    keyword = message.text.split('|')[0]
    page = int(message.text.split('|')[1]) if '|' in message.text else page
    page_size = 10
    offset = (page - 1) * page_size

    query = """
    SELECT title, year, genres, `imdb.rating`, poster
    FROM movies
    WHERE plot LIKE CONCAT('%', %s, '%')
    ORDER BY `imdb.rating` DESC
    LIMIT %s OFFSET %s;
    """
    with db_connection(db_config_search) as connection:
        results = execute_query(connection, query, (keyword, page_size, offset))

    sql_req_user = (
        f"SELECT title, year, genres, `imdb.rating`, poster FROM movies "
        f"WHERE plot LIKE '%{keyword}%' ORDER BY `imdb.rating` DESC "
        f"LIMIT {page_size} OFFSET {offset};"
    )
    log_request(f"Поиск фильмов по ключевому слову: {keyword}", sql_req_user)

    if results:
        logging.info(f"Найдено {len(results)} фильмов по ключевому слову: {keyword}")
        for title, year, genres, rating, poster in results:
            genres_str = ", ".join(genres) if isinstance(genres, (list, set)) else genres
            film_info = f"*Название:* {title}\n*Год:* {year}\n*Жанр:* {genres_str}\n*Рейтинг IMDB:* {rating}"

            if poster and is_valid_url(poster):
                bot.send_photo(
                    message.chat.id,
                    photo=poster,
                    caption=film_info,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    text=film_info,
                    parse_mode='Markdown'
                )
        show_pagination_buttons(message, keyword, page, len(results) == page_size)
    else:
        logging.info(f"Фильмы не найдены по запросу: {keyword}")
        bot.send_message(message.chat.id, "Ничего не найдено по данному запросу.")


def show_pagination_buttons(message, keyword, current_page, has_more):
    markup = InlineKeyboardMarkup()
    if current_page > 1:
        markup.add(InlineKeyboardButton(text="Предыдущая страница", callback_data=f"{keyword}|{current_page - 1}"))
    if has_more:
        markup.add(InlineKeyboardButton(text="Следующая страница", callback_data=f"{keyword}|{current_page + 1}"))
        bot.send_message(message.chat.id, "Выберите страницу:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Это все фильмы по вашему поиску.")


@bot.message_handler(func=lambda message: message.text == "Поиск фильмов по ключевому слову")
def keyword_search_handler(message):
    bot.send_message(message.chat.id, "Введите ключевое слово для поиска фильмов:")
    bot.register_next_step_handler(message, search_by_keyword)


@bot.callback_query_handler(func=lambda call: True)
def handle_pagination(call):
    keyword, page = call.data.split('|')
    message = call.message
    message.text = f"{keyword}|{page}"
    search_by_keyword(message)


@bot.message_handler(commands=['start'])
def start_command(message):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("Поиск фильмов по ключевому слову")
    button2 = KeyboardButton("Поиск фильмов по жанру и году")
    button3 = KeyboardButton("Показать популярные запросы")
    reply_keyboard.add(button1)
    reply_keyboard.add(button2)
    reply_keyboard.add(button3)

    bot.send_message(
        message.chat.id,
        "Привет! Что сегодня с тобой будем смотреть? Я очень хочу подобрать тебе афигенный фильм!)",
        reply_markup=reply_keyboard
    )
    logging.info("Отправлено приветственное сообщение и показано главное меню")


@bot.message_handler(func=lambda message: message.text == "Показать популярные запросы")
def popular_requests_handler(message):
    logging.info("Обработчик 'Показать популярные запросы' сработал")
    show_popular_requests(message)

@bot.message_handler(func=lambda message: message.text == "Запросы текстовые")
def text_requests_handler(message):
    show_text_requests(message)

@bot.message_handler(func=lambda message: message.text == "Запросы SQL")
def sql_requests_handler(message):
    show_sql_requests(message)

@bot.message_handler(func=lambda message: message.text == "Главное меню")
def main_menu_handler(message):
    start_command(message)


def show_genre_year_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Поиск по жанру"),
        KeyboardButton("Поиск по году"),
        KeyboardButton("Поиск по жанру и году"),
        KeyboardButton("Главное меню")
    )
    bot.send_message(message.chat.id, "Выберите тип поиска:", reply_markup=markup)
    logging.info("Отображено меню выбора поиска по жанру, году или и тому, и другому")


@bot.message_handler(func=lambda message: message.text == "Поиск фильмов по жанру и году")
def genre_year_search_handler(message):
    show_genre_year_menu(message)

@bot.message_handler(func=lambda message: message.text == "Поиск по жанру")
def genre_search_handler(message):
    bot.send_message(message.chat.id, "Введите жанр для поиска фильмов (например: Comedy):")
    bot.register_next_step_handler(message, search_by_genre)

@bot.message_handler(func=lambda message: message.text == "Поиск по году")
def year_search_handler(message):
    bot.send_message(message.chat.id, "Введите год для поиска фильмов (например: 2015):")
    bot.register_next_step_handler(message, search_by_year)

@bot.message_handler(func=lambda message: message.text == "Поиск по жанру и году")
def genre_year_handler(message):
    bot.send_message(message.chat.id, "Введите жанр и год для поиска фильмов (например: Comedy, 2015):")
    bot.register_next_step_handler(message, search_by_genre_year)


def search_by_genre(message, page=1):
    genre = message.text.split('|')[0].strip()
    page = int(message.text.split('|')[1]) if '|' in message.text else page
    page_size = 10
    offset = (page - 1) * page_size

    query = """
    SELECT title, year, genres, `imdb.rating`, poster
    FROM movies
    WHERE genres LIKE CONCAT('%', %s, '%')
    ORDER BY `imdb.rating` DESC
    LIMIT %s OFFSET %s;
    """
    with db_connection(db_config_search) as connection:
        results = execute_query(connection, query, (genre, page_size, offset))

    sql_req_user = (
        f"SELECT title, year, genres, `imdb.rating`, poster FROM movies "
        f"WHERE genres LIKE '%{genre}%' ORDER BY `imdb.rating` DESC LIMIT {page_size} OFFSET {offset};"
    )
    log_request(f"Поиск фильмов по жанру: {genre}", sql_req_user)

    if results:
        logging.info(f"Найдено {len(results)} фильмов по жанру: {genre}")
        for title, year, genres, rating, poster in results:
            genres_str = ", ".join(genres) if isinstance(genres, (list, set)) else genres
            film_info = f"*Название:* {title}\n*Год:* {year}\n*Жанр:* {genres_str}\n*Рейтинг IMDB:* {rating}"

            if poster and is_valid_url(poster):
                bot.send_photo(
                    message.chat.id,
                    photo=poster,
                    caption=film_info,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    text=film_info,
                    parse_mode='Markdown'
                )
        show_pagination_buttons(message, genre, page, len(results) == page_size)
    else:
        logging.info(f"Фильмы не найдены по запросу жанра: {genre}")
        bot.send_message(message.chat.id, "Ничего не найдено по данному запросу.")

def search_by_year(message, page=1):
    year = message.text.split('|')[0].strip()
    page = int(message.text.split('|')[1]) if '|' in message.text else page
    page_size = 10
    offset = (page - 1) * page_size

    query = """
    SELECT title, year, genres, `imdb.rating`, poster
    FROM movies
    WHERE year = %s
    ORDER BY `imdb.rating` DESC
    LIMIT %s OFFSET %s;
    """
    with db_connection(db_config_search) as connection:
        results = execute_query(connection, query, (year, page_size, offset))

    sql_req_user = (
        f"SELECT title, year, genres, `imdb.rating`, poster FROM movies "
        f"WHERE year = '{year}' ORDER BY `imdb.rating` DESC LIMIT {page_size} OFFSET {offset};"
    )
    log_request(f"Поиск фильмов по году: {year}", sql_req_user)

    if results:
        logging.info(f"Найдено {len(results)} фильмов по году: {year}")
        for title, year, genres, rating, poster in results:
            genres_str = ", ".join(genres) if isinstance(genres, (list, set)) else genres
            film_info = f"*Название:* {title}\n*Год:* {year}\n*Жанр:* {genres_str}\n*Рейтинг IMDB:* {rating}"

            if poster and is_valid_url(poster):
                bot.send_photo(
                    message.chat.id,
                    photo=poster,
                    caption=film_info,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    text=film_info,
                    parse_mode='Markdown'
                )
        show_pagination_buttons(message, year, page, len(results) == page_size)
    else:
        logging.info(f"Фильмы не найдены по запросу года: {year}")
        bot.send_message(message.chat.id, "Ничего не найдено по данному запросу.")

def search_by_genre_year(message, page=1):
    genre, year = message.text.split('|')[0].split(',')
    genre = genre.strip()
    year = year.strip()
    page = int(message.text.split('|')[1]) if '|' in message.text else page
    page_size = 10
    offset = (page - 1) * page_size

    query = """
    SELECT title, year, genres, `imdb.rating`, poster
    FROM movies
    WHERE genres LIKE CONCAT('%', %s, '%') AND year = %s
    ORDER BY `imdb.rating` DESC
    LIMIT %s OFFSET %s;
    """
    with db_connection(db_config_search) as connection:
        results = execute_query(connection, query, (genre, year, page_size, offset))

    sql_req_user = (
        f"SELECT title, year, genres, `imdb.rating`, poster FROM movies "
        f"WHERE genres LIKE '%{genre}%' AND year = '{year}' "
        f"ORDER BY `imdb.rating` DESC LIMIT {page_size} OFFSET {offset};"
    )
    log_request(f"Поиск фильмов по жанру и году: {genre}, {year}", sql_req_user)

    if results:
        logging.info(f"Найдено {len(results)} фильмов по жанру и году: {genre}, {year}")
        for title, year, genres, rating, poster in results:
            genres_str = ", ".join(genres) if isinstance(genres, (list, set)) else genres
            film_info = f"*Название:* {title}\n*Год:* {year}\n*Жанр:* {genres_str}\n*Рейтинг IMDB:* {rating}"

            if poster and is_valid_url(poster):
                bot.send_photo(
                    message.chat.id,
                    photo=poster,
                    caption=film_info,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    text=film_info,
                    parse_mode='Markdown'
                )
        show_pagination_buttons(message, f"{genre}, {year}", page, len(results) == page_size)
    else:
        logging.info(f"Фильмы не найдены по запросу жанра и года: {genre}, {year}")
        bot.send_message(message.chat.id, "Ничего не найдено по данному запросу.")


def show_text_requests(message):
    query = """
    SELECT commands_text, COUNT(*) AS request_count
    FROM history_of_data
    GROUP BY commands_text
    ORDER BY request_count DESC
    LIMIT 10;
    """
    with db_connection(db_config_write) as connection:
        results = execute_query(connection, query)

    if results:
        response = "*Популярные текстовые запросы:*\n"
        for index, (command_text, request_count) in enumerate(results, start=1):
            response += f"*{index}. Запрос:* `{command_text}`\n*Частота:* {request_count}\n"

        chunks = [response[i:i + 2000] for i in range(0, len(response), 2000)]
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk, parse_mode='Markdown')
        logging.info("Популярные текстовые запросы отображены")
    else:
        logging.info("Нет данных о популярных текстовых запросах")
        bot.send_message(message.chat.id, "Нет доступных данных о популярных текстовых запросах.")

def show_sql_requests(message):
    query = """
    SELECT SQL_req_user, COUNT(*) AS request_count
    FROM history_of_data
    GROUP BY SQL_req_user
    ORDER BY request_count DESC
    LIMIT 10;
    """
    with db_connection(db_config_write) as connection:
        results = execute_query(connection, query)

    if results:
        response = "*Популярные SQL-запросы:*\n"
        for index, (sql_requests, request_count) in enumerate(results, start=1):
            response += f"*{index}. SQL Запрос:* `{sql_requests}`\n*Частота:* {request_count}\n"

        chunks = [response[i:i + 2000] for i in range(0, len(response), 2000)]
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk, parse_mode='Markdown')
        logging.info("Популярные SQL-запросы отображены")
    else:
        logging.info("Нет данных о популярных SQL-запросах")
        bot.send_message(message.chat.id, "Нет доступных данных о популярных SQL-запросах.")

def show_popular_requests(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button_text = KeyboardButton("Запросы текстовые")
    button_sql = KeyboardButton("Запросы SQL")
    button_main_menu = KeyboardButton("Главное меню")
    markup.add(button_text)
    markup.add(button_sql)
    markup.add(button_main_menu)

    bot.send_message(message.chat.id, "Выберите тип запросов для просмотра:", reply_markup=markup)
    logging.info("Отображено меню выбора популярных запросов")


while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as polling_error:
        logging.error(f"Ошибка при запуске бота: {polling_error}. Повторная попытка через 10 секунд...")
        time.sleep(10)
