import os
from datetime import datetime
from utilities import utils, database
from data.api import GoogleFitAPI

# database
HOST = os.environ.get("HOST")
DATABASE = os.environ.get("DATABASE")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")

# api oauth
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TOKEN_URI = os.environ.get("TOKEN_URI")
SCOPE = os.environ.get("SCOPE")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")

gfit = GoogleFitAPI(CLIENT_ID, CLIENT_SECRET, SCOPE, REFRESH_TOKEN, TOKEN_URI)
gfit.get_token()

start, end = utils.get_refresh_range()
start_time = gfit.date_to_nanoseconds(start)
end_time = gfit.date_to_nanoseconds(end)
dataset = f"{start_time}-{end_time}"

gfit.build_url(dataset)

response = gfit.request_data()
run_data = gfit.parse_response(response)

db = database.Database(HOST, DATABASE, USER, PASSWORD)
cutoff = db.get_max_value("run_data", "run_date")

if cutoff is None:
    cutoff = datetime(2022, 1, 1).date()

db.update_run_table("run_data", "run_data_stage", "update_run_data", run_data, cutoff)
