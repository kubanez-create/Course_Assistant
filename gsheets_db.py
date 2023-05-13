import gspread

gc = gspread.service_account(
    filename="/home/kubanez/Dev/Course_Assistant/service_account.json")
# sh = gc.create('A new spreadsheet')
# sh.share('kubanez74@gmail.com', perm_type='user', role='writer')

# get the instance of the Spreadsheet
sheet = gc.open('A new spreadsheet')

# get the first sheet of the Spreadsheet
sheet_instance = sheet.get_worksheet(0)

# get all the records of the data
records_data = sheet_instance.get_all_records()
print(sheet_instance.get('A1'))
print(records_data)
