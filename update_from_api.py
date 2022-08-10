import os
from datetime import datetime
import sqlalchemy.exc

from utilities import utils, database, text
from data.api import GoogleFitAPI


if os.environ.get("ENVIRONMENT") is None:
    import dotenv
    dotenv.load_dotenv()

# get environment variables
# database
HOST = os.environ.get("HOST")
DATABASE = os.environ.get("DATABASE")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")

# text notifications
EMAIL = os.environ.get("EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER")
PHONE_CARRIER = os.environ.get("PHONE_CARRIER")

# GoogleFit API
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TOKEN_URI = os.environ.get("TOKEN_URI")
SCOPE = os.environ.get("SCOPE")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")

# initialize API class and get oauth token
gfit = GoogleFitAPI(CLIENT_ID, CLIENT_SECRET, SCOPE, REFRESH_TOKEN, TOKEN_URI)
gfit.get_token()

# set date range for API data and build URL
start, end = utils.get_refresh_range()
start_time = gfit.date_to_nanoseconds(start)
end_time = gfit.date_to_nanoseconds(end)
dataset = f"{start_time}-{end_time}"

gfit.build_url(dataset=dataset)

# request data from API and parse response
response = gfit.request_data()
run_data = gfit.parse_response(response)

# find cutoff date for updates
db = database.Database(HOST, DATABASE, USER, PASSWORD)
cutoff = db.get_max_value(table="run_data", column="run_date")

if cutoff is None:
    cutoff = datetime(2022, 1, 1).date()

# update database and send text message notification of results
message = f"\n\n Results from RunTrekker batch update {datetime.today().date()}: "
try:
    db.update_run_table(table="run_data",
                        stage_table="run_data_stage",
                        stored_proc="update_run_data",
                        data=run_data,
                        cutoff_date=cutoff)
    last_update = db.get(table="run_data",
                         columns=["*"],
                         where={"CONVERT(updated_date, date)": f"'{db.get_max_value('run_data', 'CONVERT(updated_date, date)')}'"},
                         order_by=["run_date DESC LIMIT 1"])
    message += f"\n\n Date: {last_update.iloc[0, 1]}, Miles: {last_update.iloc[0, 2]}"
except sqlalchemy.exc.DatabaseError as e:
    message += f"\n\n Error updating database: {e}"


text_auth = text.authorize_email(email=EMAIL, app_password=APP_PASSWORD)
text.send_message(auth=text_auth, phone_number=PHONE_NUMBER, carrier=PHONE_CARRIER, message=message)
