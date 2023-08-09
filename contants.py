SESSION_NAME: str = "Bot"
# we might need to use emoji lib https://pypi.org/project/emoji/
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
# There should be your own link to a quiz
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
# Put there names of your google sheets files where you keep info about your
# potential clients (participants of the webinars you're going to hold)
WEBINARS = "Webinars dates"
USERS = "Пользователи"
# Your own file with google sheets credentials
# Look how to obtain one here https://docs.gspread.org/en/latest/oauth2.html
CREDS = "./service_account.json"
WORKING_SHEET = 0
WAIT_BEFORE_QUIZ = 5  # change to 5*60 or whatever
# Below is a telegram id
# (one can discover their id by contacting https://t.me/userinfobot)
# of a user the bot sends notifications about new subscriptions to
VORTEX_AUTHOR = 411347820  # client's telegram id
