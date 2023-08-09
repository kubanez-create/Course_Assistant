# Telegram Bot for Blogger's Webinars

This Telegram bot is designed to help bloggers manage their webinars and interact with participants effectively. The bot allows users to sign up for upcoming webinars, receive reminders, and get important information about the events.

## Features

- Sign up for webinars.
- Choose the reason for learning English.
- Receive reminders for upcoming webinars.
- Get instructions for preparing for the webinar.
- Interact with the bot through intuitive inline buttons.

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/blogger-webinar-bot.git
cd blogger-webinar-bot
```
2. Create and activate a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
4. Set up your environment variables by creating a .env file and adding the following:
```bash
TELEGRAM_TOKEN=<your_telegram_bot_token>
API_HASH=<your_api_hash>
API_ID=<your_api_id>
WEBINARS_KEY=<your_gsheets_webinars_file_key>
USERS_KEY=<your_gsheets_users_file_key>
```
5. You might want to change some constants as well:
```bash
SESSION_NAME=<your_favorite_word>
QUIZ_LINK=<your_own_quiz>
WEBINARS=<name_of_webinars_file>
USERS=<name_of_users_file>
CREDS=<path_to_a_file_with_gsheets_credentials>
WORKING_SHEET=<number_of_main_working_sheet>
WAIT_BEFORE_QUIZ=<how_long_user_must_wait>
VORTEX_AUTHOR=<id_you_would_like_to_recieve_notifications>
```
6. Run the bot:
```bash
python bot.py
```

## Usage
1. Start a conversation with the bot by sending the command /start.

2. Choose your English proficiency level from the provided options.

3. Select the reason for learning English (travel, work, confidence, exam, relocation).

4. Sign up for an upcoming webinar by clicking the "Записаться на занятие" button.

5. Choose a convenient date and time for the webinar from the options provided.

6. Receive a confirmation and follow the instructions to prepare for the webinar.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request. Alternatively you might contact me through [kubanez74@google.com](mailto:kubanez74@google.com).