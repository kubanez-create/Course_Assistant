"""Telegram bot-assistant in instagram sales."""

import logging
import os
import re
import sys
import time
from datetime import datetime
from enum import Enum, auto
from itertools import chain
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

# pip install telethon
from telethon import Button, TelegramClient, events
from telethon.tl.types import ReplyInlineMarkup

from validators import validate_reason, validate_zoom
from gsheets_db import Wb

load_dotenv()

TELEGRAM_TOKEN: str = str(os.getenv("TELEGRAM_TOKEN"))
API_HASH: str = str(os.getenv("API_HASH"))
API_ID: int = int(os.getenv("API_ID"))

SESSION_NAME: str = "sessions/Bot"
CHUNK_SIZE: int = 10
COUNTER: int = None
TEXT: dict = {}
WAVING_MAN = "\U0001F64B"
NUMBER_ONE = "\U00000031"
NUMBER_TWO = "\U00000032"
NUMBER_THREE = "\U00000033"
NUMBER_FOUR = "\U00000034"
NUMBER_FIVE = "\U00000035"
HOURGLASS = "\U000023F3"
WATCH = "\U0001F558"
STAR = "\U00002B50"
ZOOM_LINK = "https://zoom.us/download"
QUIZ_LINK = ""
LEVELS = {
    "Lev_0": "Beginner",
    "Lev_1": "Elementary",
    "Lev_2": "Pre-Intermediate",
    "Lev_3": "Intermediate",
    "Lev_4": "Upper-Intermediate",
    "Lev_5": "Advanced",
    "Lev_None": "Не знаю"
}
WEBINARS = 'Webinars dates'
USERS = "Пользователи"
CREDS = "/home/kubanez/ma_sales/service_account.json"
WORKING_SHEET = 1
WAIT_BEFORE_QUIZ = 5 * 60
VORTEX_AUTHOR = ""  # client's telegram id
# The state in which different users are, {user_id: state}
conversation_state = {}
users_info = {}


# Start the Client (telethon)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH).start(
    bot_token=TELEGRAM_TOKEN)


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
                Button.inline("Pre-Intermediate", data="Lev_2"),
                Button.inline("Intermediate", data="Lev_3"),
                Button.inline("Upper-Intermediate", data="Lev_4"),
                Button.inline("Advanced", data="Lev_5"),
                Button.inline("Не знаю", data="Lev_None"),
            ],
        ]
    )

    text = (
        f"{sender.name}, приветствую!\nЭто мой бот помощник, который поможет"
        " тебе записаться на пробный урок. Но перед этим предлагаю"
        f" познакомиться поближе {WAVING_MAN}."
        " Выбери свой уровень английского:"
    )
    await client.send_message(SENDER, text, buttons=markup, parse_mode="html")
    logger.info("Looks like we have a new user!", exc_info=1)


@client.on(events.NewMessage(pattern="Lev_"))
async def reason(event):
    """Query users level in English.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    users_info[SENDER] = [LEVELS.get(event.message.raw_text),]

    try:
        text = (
            "Выбери подходящий вариант.\nЯ хочу изучать английский язык для...\n"
            f"{NUMBER_ONE} Путешествий\n{NUMBER_TWO} Работы\n"
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


@client.on(events.NewMessage())
async def main_handler(event):
    """Handle the biggest part of a conversation.

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
                    "Отправь, пожалуйста, цифру в диапазоне от 1 до 5.",
                    parse_mode="html")
        except ValueError:
            await client.send_message(
                    SENDER,
                    ("Отправь, пожалуйста, только цифру в диапазоне от 1 до 5"
                    " без дополнительных слов, знаков препинания, либо чего бы"
                    " то ни было еще."),
                    parse_mode="html")

        conversation_state[SENDER] = State.WAIT_INVITATION

        markup = event.client.build_reply_markup(
            Button.inline("Записаться на занятие")
        )

        text = (
            f"Твой запрос принят, спасибо за уделенное время {HOURGLASS}."
            "Мне очень понятно твое желание, оно реализуемо на все 100 %."
            "Для записи на пробное занятие нажми на кнопку ниже"
        )
        await client.send_message(SENDER, text, buttons=markup, parse_mode="html")

    if (
        conversation_state.get(SENDER) == State.WAIT_INVITATION
        and not re.match(r"Записаться на занятие", mes)
    ):
        await client.send_message(
                SENDER,
                "Для записи на пробное занятие просто нажми на кнопку!",
                parse_mode="html")

    if conversation_state.get(SENDER) == State.WAIT_INVITATION:
        workbook = Wb(WEBINARS, CREDS, WORKING_SHEET)
        df = workbook.get()
        markup = ReplyInlineMarkup([[date] for date in df])
        conversation_state[SENDER] = State.WAIT_DATE
        text = (
            f"Для записи на занятие выбери удобную дату и время {WATCH}"
        )
        await client.send_message(SENDER, text,
                                  buttons=markup, parse_mode="html")
    if conversation_state.get(SENDER) == State.WAIT_DATE:
        df = workbook.get()
        try:
            if (
                not df.loc[
                    df["Дата и время"] == datetime.datetime.fromisoformat(mes)
                ].empty
            ):
                users_info[SENDER].append(mes)
            else:
                await client.send_message(
                    SENDER,
                    "Для записи на пробное занятие просто нажми на кнопку!",
                    parse_mode="html")
        except ValueError:
            await client.send_message(
                SENDER,
                "Для записи на пробное занятие просто нажми на кнопку!",
                parse_mode="html")

        conversation_state[SENDER] = State.WAIT_ZOOM

        markup = ReplyInlineMarkup(
            [
                [Button.inline("Да", data="yes_answer")],
                [Button.inline("Нет", data="no_answer")]
            ]
        )

        text = (
            f"Занятие будет проходить в Zoom.\n\nСейчас я тебе дам очень"
            "задание, которое надо выполнить до начала нашего урока:\n"
            f"{NUMBER_ONE} Тебе нужно скачать и установить zoom {STAR}:"
            f"{ZOOM_LINK}\n{NUMBER_TWO} Подготовить ручку, лист бумаги"
            " и спокойное место для проведения занятия.\nУ тебя получилось?"
        )
        await client.send_message(SENDER, text, buttons=markup, parse_mode="html")

        # Send info about new subscription to the vortex author
        await client.send_message(
            VORTEX_AUTHOR,
            f"Новая запись на вебинар: {sender.name}. Время: {mes}",
            parse_mode="html")

        # Add info about new user to the user's table
        users = Wb(USERS, CREDS, WORKING_SHEET)
        users.update(users_info[SENDER])

    if conversation_state.get(SENDER) == State.WAIT_ZOOM:
        time.sleep(WAIT_BEFORE_QUIZ)
        await client.send_message(
            SENDER,
            (
                "Для того, чтобы наше взаимодействие было более продуктивным"
                " предлагаю тебе пройти тест, который проверит твой уровень"
                " английского"
            ),
            parse_mode="html")
        await client.send_message(
            SENDER,
            f"Пройди тест: {QUIZ_LINK}",
            parse_mode="html")
        if validate_zoom(mes):
            users_info[SENDER].append(mes)
        else:
            users_info[SENDER].append("no")


if __name__ == "__main__":
    try:
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

        if not check_tokens():
            logger.critical("Bot stopped due missing some token", exc_info=1)
            sys.exit(2)

        logger.info("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        client.send_message("me", "Bot isn't working!!")
        logger.fatal("Bot isn't working due to a %s", error, exc_info=1)