# Telegram Bot for Movie Search

This project is a Telegram bot designed to help users find movies based on various criteria such as keywords, genres, and years. It also logs user requests for further analysis. The bot interacts with a MySQL database to fetch movie data and stores request histories.

## Features

- Search movies by keyword.
- Search movies by genre.
- Search movies by year.
- Search movies by genre and year.
- Display popular user requests (both textual and SQL).
- Pagination support for search results.
- Logging of all requests in the database.

## Requirements

- Python 3.7+
- `mysql-connector-python`
- `requests`
- `pyTelegramBotAPI`
- MySQL server

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/erema0324/telegram-movie-bot.git
    cd telegram-movie-bot
    ```

2. **Create and activate a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the bot and database:**

   - Open the `main.py` file.
   - Replace `ТУТ ВАШ API TELEGRAM` with your actual Telegram bot API token.
   - Replace `ВАШ ХОСТ`, `ЮЗЕР`, `ПАРОЛЬ`, and `БД` in `db_config_search` and `db_config_write` with your MySQL database configuration.

5. **Create the database tables:**
    ```sql
    CREATE TABLE `movies` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `title` VARCHAR(255) NOT NULL,
      `year` INT NOT NULL,
      `genres` VARCHAR(255) NOT NULL,
      `imdb.rating` FLOAT NOT NULL,
      `poster` VARCHAR(255),
      `plot` TEXT,
      PRIMARY KEY (`id`)
    );

    CREATE TABLE `history_of_data` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `commands_text` TEXT NOT NULL,
      `commands_datetime` DATETIME NOT NULL,
      `SQL_req_user` TEXT NOT NULL,
      PRIMARY KEY (`id`)
    );
    ```

## Running the Bot

To start the bot, run:
    ```bash
    python main.py
    ```
The bot will connect to the Telegram API and the MySQL database and start listening for user messages.

## Bot Commands and Handlers

- `/start`: Initializes the bot and displays the main menu.
- `Поиск фильмов по ключевому слову`: Prompts the user to enter a keyword for movie search.
- `Поиск фильмов по жанру и году`: Shows a submenu for genre/year-based searches.
  - `Поиск по жанру`: Prompts the user to enter a genre.
  - `Поиск по году`: Prompts the user to enter a year.
  - `Поиск по жанру и году`: Prompts the user to enter both a genre and a year.
- `Показать популярные запросы`: Displays the submenu for viewing popular requests.
  - `Запросы текстовые`: Shows the most frequent textual requests.
  - `Запросы SQL`: Shows the most frequent SQL requests.
- `Главное меню`: Returns to the main menu.

## Logging and Error Handling

- All database connections and queries are logged.
- Errors during database operations or bot polling are logged with appropriate messages.
- The bot will attempt to reconnect in case of polling errors, with a delay of 10 seconds.

## Contributing

Feel free to submit issues and pull requests. Contributions are welcome!

## License

This project is licensed under the MIT License.
