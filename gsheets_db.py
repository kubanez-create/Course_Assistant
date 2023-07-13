# Refactor the whole thing from ground up bec it is too slow to load
# data from google spreadsheet
import datetime

import gspread
import pandas as pd
from gspread.exceptions import SpreadsheetNotFound

# I might need this in the future
# sh = gc.create('A new spreadsheet')
# sh.share('kubanez74@gmail.com', perm_type='user', role='writer')


class Wb:
    def __init__(self, name, creds, sheet_num, key=None):
        """Get google sheets workbook.

        name - name of a workbook (ex. "myworkbook");
        creds - path to a service_account.json credentials file;
        sheet - number of sheet we need;
        key - key (id) for a workbook.
        """
        gc = gspread.service_account(filename=creds)
        try:
            sheet = gc.open(name)
        except SpreadsheetNotFound:
            sheet = gc.open_by_key(key)
        self.sheet_instance = sheet.get_worksheet(sheet_num)
        df = pd.DataFrame.from_records(self.sheet_instance.get_all_values())
        df.columns = df.iloc[0]
        df.drop([0], inplace=True)
        # set format properly when it's consistent across the databases
        df["Дата"] = pd.to_datetime(
            df["Дата"], format='mixed', dayfirst=True).dt.to_pydatetime()
        self.dataframe = df

    def get_future_webs(self):
        """Get future events and return it in handy format, ex. - pandas df."""
        return self.dataframe.loc[
            self.dataframe["Дата"] >= datetime.datetime.today(), "Дата"]

    def get_web_link(self, web_time):
        """Get link to a webinar date/time."""
        return self.dataframe.loc[self.dataframe["Дата"] == web_time, "Ссылка"]

    def get_users_db(self):
        """Get all users subscribed to today's events."""
        self.dataframe.sort_values(by=["Дата"], inplace=True)
        return self.dataframe.loc[
            self.dataframe["Дата"].dt.date == datetime.date.today(),
            ["Никнейм", "ID", "Дата"]].to_records()

    def update(self, user):
        """Add new user to our users table.

        user - python list of a new user's related variables.
        """
        self.sheet_instance.append_row(user)
