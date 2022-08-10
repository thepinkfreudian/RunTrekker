import os
from datetime import datetime
from utilities import utils, database, text
from data.api import GoogleFitAPI


if os.environ.get("ENVIRONMENT") is None:
    import dotenv
    dotenv.load_dotenv()

# get environment variables
HOST = os.environ.get("HOST")
DATABASE = os.environ.get("DATABASE")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")
EMAIL = os.environ.get("EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER")
CARRIER = os.environ.get("CARRIER")
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

gfit.build_url(dataset)

# request data from API and parse response
response = gfit.request_data()
run_data = gfit.parse_response(response)

# find cutoff date for updates and update
db = database.Database(HOST, DATABASE, USER, PASSWORD)
cutoff = db.get_max_value("run_data", "run_date")

if cutoff is None:
    cutoff = datetime(2022, 1, 1).date()

# send text message notification of results
message = f"\n\n Results from RunTrekker batch update {datetime.today().date()}: "
try:
    db.update_run_table("run_data", "run_data_stage", "update_run_data", run_data, cutoff)
    last_update = db.get(table="run_data",
                         columns=["*"],
                         where={"CONVERT(updated_date, date)": f"'{datetime.today().date()}'"},
                         order_by = ["run_date DESC LIMIT 1"])
    message += f"\n\n Date: {last_update.iloc[0, 1]}, Miles: {last_update.iloc[0, 2]}"
except Exception as e:
    message += f"\n\n Error updating database: {e}"


text_auth = text.authorize_email(EMAIL, EMAIL_PASSWORD)
text.send_message(text_auth, PHONE_NUMBER, CARRIER, message)
