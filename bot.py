"""Telegram bot-assistant for instagram expert page.

It is assumed the manager keeps webinar's dates (and specific time if needed)
in google sheets file "Webinars dates". Links for webinars also go into this
file.

User's info is accumulated in another google sheets file "Пользователи".
"""

import asyncio
import heapq
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from logging.handlers import RotatingFileHandler

# pip install telethon, apscheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telethon import Button, TelegramClient, events
from telethon.tl.types import ReplyInlineMarkup

from gsheets_db import Wb
from validators import validate_reason, validate_zoom

load_dotenv()

TELEGRAM_TOKEN: str = str(os.getenv("TELEGRAM_TOKEN"))
API_HASH: str = str(os.getenv("API_HASH"))
API_ID: int = int(os.getenv("API_ID"))

# we might need to use emoji lib https://pypi.org/project/emoji/
SESSION_NAME: str = "Bot"
WAVING_MAN = "\U0001F64B"
NUMBER_ONE = "1️⃣"
NUMBER_TWO = "2️⃣"
NUMBER_THREE = "3️⃣"
NUMBER_FOUR = "4️⃣"
NUMBER_FIVE = "5️⃣"
HOURGLASS = "\U000023F3"
WATCH = "\U0001F558"
STAR = "\U00002B50"
ZOOM_LINK = "https://zoom.us/download"
QUIZ_LINK = "https://www.cambridgeenglish.org/test-your-english/for-schools/"
LEVELS = {
    "Lev_0": "Beginner",
    "Lev_1": "Elementary",
    "Lev_2": "Pre-Intermediate",
    "Lev_3": "Intermediate",
    "Lev_4": "Upper-Intermediate",
    "Lev_5": "Advanced",
    "Lev_None": "Не знаю",
}
WEBINARS = "Webinars dates"
WEBINARS_KEY = os.getenv("WEBINARS_KEY")
USERS_KEY = os.getenv("USERS_KEY")
USERS = "Пользователи"
CREDS = "/home/kubanez/Dev/Course_Assistant/service_account.json"
WORKING_SHEET = 0
WAIT_BEFORE_QUIZ = 5  # change to 5*60
VORTEX_AUTHOR = 411347820  # client's telegram id
# The states in which different users are, {user_id: state}
conversation_state = {}
users_info = {}


# Start the Client and initiate databases (google spreadsheet files)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)
users = Wb(USERS, CREDS, WORKING_SHEET, key=USERS_KEY)
webinars = Wb(WEBINARS, CREDS, WORKING_SHEET, key=WEBINARS_KEY)


class State(Enum):
    """User' states."""

    START = auto()
    WAIT_CAUSE = auto()
    WAIT_INVITATION = auto()
    WAIT_DATE = auto()
    WAIT_ZOOM = auto()


def check_tokens() -> bool:
    """Check availability of global variables."""
    return all((TELEGRAM_TOKEN, API_HASH, API_ID))


def reminder(db):
    """Generate telethon.entities, time, text tuples to send a message pairs.

    Args:
        db (pandas.DataFrame): table which contains nicknames and dates
    for webinars users subscribed to

    Yields:
        (telethon.entity, datetime.datetime, string): tuples to send messages to
    """
    for _, nick, pers, time_point in db:
        link = webinars.get_web_link(time_point)
        two_hours = (
            f"Привет! Напоминаю, что сегодня в {time_point}"
            " пройдет наш урок, обязательно подключайся\n"
        )
        five_min = f"Мы стартуем, подключайся {link}\n"
        now = "Мы уже начали, подключайся скорее"
        time_point = datetime.utcfromtimestamp(int(time_point) / 1e9)
        pers = int(pers)
        yield pers, (time_point - timedelta(hours=2)), two_hours
        yield pers, (time_point - timedelta(minutes=5)), five_min
        yield pers, time_point, now


async def message_sender(addr, text):
    """Send text to a given user.

    Args:
        addr (int): user's id
        text (str): message text
    """
    await client.send_message(addr, text)
    logger.info(f"Successfully sent the message '{text}' to the user '{addr}'")


# Step 1 - initiation
@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    """Initialize the bot and show keyboard to a user.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    conversation_state[SENDER] = State.START

    markup = event.client.build_reply_markup(
        [
            [
                Button.inline("Beginner", data="Lev_0"),
                Button.inline("Elementary", data="Lev_1"),
            ],
            [
                Button.inline("Pre-Intermediate", data="Lev_2"),
                Button.inline("Intermediate", data="Lev_3"),
            ],
            [
                Button.inline("Upper-Intermediate", data="Lev_4"),
                Button.inline("Advanced", data="Lev_5"),
            ],
            [
                Button.inline("Не знаю", data="Lev_None"),
            ],
        ]
    )

    text = (
        f"{sender.first_name}, приветствую!\nЭто мой бот помощник, который поможет"
        " тебе записаться на пробный урок. Но перед этим предлагаю"
        f" познакомиться поближе {WAVING_MAN}.\n"
        " Выбери свой уровень английского:"
    )
    await client.send_message(SENDER, text, buttons=markup, parse_mode="html")
    logger.info("Looks like we have a new user!", exc_info=1)


# Step 2
@client.on(events.CallbackQuery(data=re.compile(r"Lev_")))
async def reason(event):
    """Query users level in English.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    users_info[SENDER] = [
        sender.username,
        SENDER,
        sender.first_name,
        LEVELS.get(event.data.decode("utf-8")),
    ]

    try:
        text = (
            "Выбери подходящий вариант.\nЯ хочу изучать английский язык для"
            f"...\n{NUMBER_ONE} Путешествий\n{NUMBER_TWO} Работы\n"
            f"{NUMBER_THREE} Уверенности в себе\n"
            f"{NUMBER_FOUR} Успешной сдачи экзамена\n"
            f"{NUMBER_FIVE} Переезда за границу\n"
        )
        await client.send_message(SENDER, text, parse_mode="html")
        conversation_state[SENDER] = State.WAIT_CAUSE
    except Exception as e:
        logger.error(
            "Something went wrong when asking about the reason for studying"
            f" English with an error: {e}"
        )
        return


# Step 4
@client.on(events.CallbackQuery(data=re.compile(r"Записаться на занятие")))
async def reason(event):
    """Join a webinar.

    It doesn't matter what state a client currently is in if they want to
    join a webinar we must direct them to a list of dates for webinars and
    continue from here.
    """
    sender = await event.get_sender()
    SENDER = sender.id
    df = webinars.get_future_webs()
    # handle the case if we genuinely haven't got any future webinars
    if df.empty:
        await client.send_message(
            SENDER,
            (
                "К сожалению, на текущий момент ни одного вебинара не"
                " запланировано. Попробуйте написать позже"
            ),
        )
    markup = event.client.build_reply_markup(
        [[Button.inline(f"{date}")] for date in df]
    )
    conversation_state[SENDER] = State.WAIT_DATE
    text = f"Для записи на занятие выбери удобную дату и время {WATCH}\n"
    try:
        await client.send_message(
            SENDER, text, buttons=markup, parse_mode="html")
    except Exception as e:
        logger.error(
            "Something went wrong when asking about the date for"
            f" a webinar with an error: {e}"
        )
    return


# Step 5
@client.on(events.CallbackQuery(
    data=re.compile(r"^\d+\-\d+\-\d+ \d+:\d+:\d+$")))
async def subscription(event):
    """Subscribe user for chosen webinar.

    If user is in some other than wait_date state ask them to redo
    everything from scratch.
    """
    sender = await event.get_sender()
    SENDER = sender.id
    mes = event.data.decode("utf-8")
    if conversation_state.get(SENDER) != State.WAIT_DATE:
        await client.send_message(
            SENDER,
            (
                "Что-то пошло не так, пожалуйста начните процесс записи на"
                " пробный урок отправив боту сообщение /start"
            ),
        )
    df = webinars.get_future_webs()
    try:
        if not (datetime.fromisoformat(mes) in df.dt.to_pydatetime()):
            await client.send_message(
                SENDER,
                "Для записи на пробное занятие нажми на кнопку!\n",
            )

        users_info[SENDER].append(mes)
        await client.send_message(
            SENDER, "Вы записаны на пробное занятие, спасибо!\n")
        conversation_state[SENDER] = State.WAIT_ZOOM

        markup = client.build_reply_markup(
            [
                [Button.inline("Да", data="yes_answer")],
                [Button.inline("Нет", data="no_answer")],
            ]
        )

        text = (
            f"Занятие будет проходить в Zoom.\n\nСейчас я тебе дам одно"
            " задание, которое надо выполнить до начала нашего урока:\n"
            f"{NUMBER_ONE} Тебе нужно скачать и установить zoom:"
            f" {STAR}{ZOOM_LINK}\n{NUMBER_TWO}\n Подготовить ручку, лист"
            " бумаги и спокойное место для проведения занятия.\n"
            "У тебя получилось?"
        )
        await client.send_message(
            SENDER, text, buttons=markup, parse_mode="html")

        # Send info about new subscription to the vortex's author
        await client.send_message(
            VORTEX_AUTHOR,
            (
                f"Новая запись на вебинар: {sender.first_name}."
                f" Время: {mes}"
            ),
            parse_mode="html",
        )

        # Add info about new user to the user's table
        users.update(users_info[SENDER])
    except ValueError:
        await client.send_message(
            SENDER,
            "Для записи на пробное занятие нажми на кнопку!",
        )
        logger.error(
            (
                "Someone tried to send smth which isn't a number"
                " between 1 and 5"
            )
        )


# Step 6
@client.on(events.CallbackQuery(data=re.compile("\w{1,3}_answer")))
async def quiz(event):
    """Send quiz to a user.

    If user is in some other than wait_date state ask them to redo
    everything from scratch.
    """
    sender = await event.get_sender()
    SENDER = sender.id
    mes = event.data.decode("utf-8")
    if conversation_state.get(SENDER) != State.WAIT_ZOOM:
        await client.send_message(
            SENDER,
            (
                "Что-то пошло не так, пожалуйста начните процесс записи на"
                " пробный урок отправив боту сообщение /start"
            ),
        )
    try:
        await asyncio.sleep(WAIT_BEFORE_QUIZ)
        await client.send_message(
            SENDER,
            (
                "Для того, чтобы наше взаимодействие было более продуктивным"
                " предлагаю тебе пройти тест, который проверит твой уровень"
                " английского"
            ),
        )
        await client.send_message(
            SENDER, f"Пройди тест: {QUIZ_LINK}", parse_mode="html"
        )
    except Exception as e:
        logger.error(
            "Something went wrong when sending a link to an english"
            f" test with an error: {e}"
        )
    # client isn't sure yet whether we need this info or not
    # if validate_zoom(mes):
    #     users_info[SENDER].append(mes)
    # else:
    #     users_info[SENDER].append("no")


# Step 3
@client.on(events.NewMessage())
async def start_dialog(event):
    """Initiate conversation.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    mes = event.message.raw_text

    if conversation_state.get(SENDER) == State.WAIT_CAUSE:
        try:
            if validate_reason(mes):
                users_info[SENDER].append(mes)
            else:
                await client.send_message(
                    SENDER,
                    "Отправь, пожалуйста, цифру в диапазоне от 1 до 5.\n",
                )
        except ValueError:
            await client.send_message(
                SENDER,
                (
                    "Отправь, пожалуйста, цифру в диапазоне от 1 до 5"
                    " без дополнительных слов, знаков препинания, либо чего бы"
                    " то ни было еще.\n"
                ),
            )
            logger.error(
                (
                    "We get smth which isn't a number asking about the"
                    " reason for studying English"
                )
            )

        conversation_state[SENDER] = State.WAIT_INVITATION

        markup = event.client.build_reply_markup(
            Button.inline("Записаться на занятие"))

        text = (
            f"Твой запрос принят, спасибо за уделенное время {HOURGLASS}.\n"
            "Мне очень понятно твое желание, оно реализуемо на все 100 %.\n"
            " Для записи на пробное занятие нажми на кнопку ниже"
        )
        await client.send_message(
            SENDER, text, buttons=markup, parse_mode="html")
        return


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filemode="w"
    )
    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler: RotatingFileHandler = RotatingFileHandler(
        "main.log", maxBytes=50000000, backupCount=5
    )
    logger.addHandler(handler)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler.setFormatter(formatter)

    scheduler = AsyncIOScheduler()
    for addr, time_point, text in reminder(users.get_users_db()):
        scheduler.add_job(
            message_sender,
            trigger="date",
            run_date=time_point,
            args=[addr, text]
        )
    scheduler.start()

    if not check_tokens():
        logger.critical("Bot stopped due some missing token", exc_info=1)
        sys.exit(2)

    logger.info("Bot Started...")
    client.run_until_disconnected()
