import datetime

import gspread
import pandas as pd

# I might need this in the future
# sh = gc.create('A new spreadsheet')
# sh.share('kubanez74@gmail.com', perm_type='user', role='writer')

# To Do:
# Make a class
# methods: search,
class Wb():
    def __init__(self, name, creds, sheet_num):
        """Get google sheets workbook.

        name - name of a workbook (ex. "myworkbook");
        creds - path to a service_account.json credentials file;
        sheet - number of sheet we need.
        """
        gc = gspread.service_account(
            filename=creds)
        sheet = gc.open(name)
        self.sheet_instance = sheet.get_worksheet(sheet_num)

    def get(self):
        """Get data and return it in handy format, ex. - pandas df."""
        df = pd.DataFrame.from_records(self.sheet_instance.get_all_values())
        df.columns = df.iloc[0]
        df.drop([0], inplace=True)
        df["Дата и время"] = pd.to_datetime(
            df["Дата и время"],
            infer_datetime_format=True, dayfirst=True).dt.to_pydatetime()
        return df.loc[df["Дата и время"] >= datetime.datetime.today(), "Дата и время"]

    def update(self, user):
        """Add new user to our users table.

        user - python list of a new user's related variables.
        """
        self.sheet_instance.append(user)
