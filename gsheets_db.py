from datetime import date, datetime, timedelta

import gspread
import pandas as pd
from gspread.exceptions import SpreadsheetNotFound


class Wb:
    def __init__(self, name, creds, sheet_num, key=None):
        """Get google sheets workbook.

        name - name of a workbook (ex. "myworkbook");
        creds - path to a service_account.json credentials file;
        sheet - number of sheet we need;
        key - key (id) for a workbook.
        """
        self._refresh_time = datetime.now()

        gc = gspread.service_account(filename=creds)
        try:
            sheet = gc.open(name)
        except SpreadsheetNotFound:
            sheet = gc.open_by_key(key)
        self.sheet_instance = sheet.get_worksheet(sheet_num)
        df = pd.DataFrame.from_records(self.sheet_instance.get_all_values())
        df.columns = df.iloc[0]
        df.drop([0], inplace=True)
        df["Дата"] = pd.to_datetime(
            df["Дата"], format="mixed", dayfirst=True
        ).dt.to_pydatetime()
        self.dataframe = df

    def refresh_df(self):
        """Check whether 3 hours have passed since last df update.

        If the answer yes, fetch info from gsheets, if no - do nothing.
        There's no point in webinar if it starts in just 3 hours time.
        Everyone should know all about it at least a day before.
        """
        if (self._refresh_time + timedelta(minutes=180)) < datetime.now():
            df = pd.DataFrame.from_records(self.sheet_instance.get_all_values())
            df.columns = df.iloc[0]
            df.drop([0], inplace=True)
            df["Дата"] = pd.to_datetime(
                df["Дата"], format="mixed", dayfirst=True
            ).dt.to_pydatetime()
            self.dataframe = df
            self._refresh_time = datetime.now()

    def get_future_webs(self):
        """Get future events and return it in handy format, ex. - pandas df."""
        self.refresh_df()
        return self.dataframe.loc[
            self.dataframe["Дата"] >= datetime.today(), "Дата"
        ]

    def get_web_link(self, web_time):
        """Get link to a webinar date/time."""
        self.refresh_df()
        return self.dataframe.loc[
            self.dataframe["Дата"] == web_time, "Ссылка"
        ].to_list()[0]

    def get_users_db(self):
        """Get all users subscribed to today's events."""
        self.refresh_df()
        self.dataframe.sort_values(by=["Дата"], inplace=True)
        return self.dataframe.loc[
            self.dataframe["Дата"].dt.date == date.today(),
            ["Никнейм", "ID", "Дата"],
        ].to_records()

    def update(self, user):
        """Add new user to our users table.

        user - python list of a new user's related variables.
        """
        self.sheet_instance.append_row(user)
