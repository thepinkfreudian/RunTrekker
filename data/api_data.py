import os
import pandas as pd
from datetime import datetime
from setup import config, start_date, end_date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

secrets = config['google_fit_api']['secrets_file']
token_file = config['google_fit_api']['token_file']

scopes = ['https://www.googleapis.com/auth/fitness.location.read']
datasource = 'derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta'
dataset = ''  # set after function defs

# Google API 'dataset' requires time range expressed in nanoseconds
def date_to_nanoseconds(date):
    dt = datetime.strptime(date + ' 00:00:00,76', '%Y-%m-%d %H:%M:%S,%f')
    nano_dt = dt.timestamp() * 1000000000

    return int(nano_dt)


def nanoseconds_to_date(ns):
    dt = datetime.fromtimestamp(ns // 1000000000)

    return dt.strftime('%Y-%m-%d')

# largely taken from Google's Python API docs
def get_credentials(token_file, secrets, scopes):
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                secrets, scopes)
            credentials = flow.run_local_server(port = 0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(credentials.to_json())

    return credentials


def get_api_data(credentials, dataset, datasource):
    try:
        service = build('fitness', 'v1', credentials=credentials)
        response = service.users().dataSources().datasets().get(userId='me',
                                                                dataSourceId=datasource,
                                                                datasetId=dataset).execute()

    except HttpError as err:
        print(err)

    return response


start_date_ns = date_to_nanoseconds(start_date)
end_date_ns = date_to_nanoseconds(end_date)
dataset = str(start_date_ns) + '-' + str(end_date_ns)

credentials = get_credentials(token_file, secrets, scopes)
response = get_api_data(credentials, dataset, datasource)

# isolate time and distance data from the API response
points = response['point']
data = pd.DataFrame(columns=['Date', 'Miles'])

# create data frame of start date, end date, and mileage recorded
for i in range(0, len(points)):
    date = nanoseconds_to_date(int(points[i]['startTimeNanos']))
    #end_date = nanoseconds_to_date(int(points[i]['endTimeNanos']))
    miles = int(points[i]['value'][0]['fpVal']) * 0.000621371  # m to mi
    row = [date, miles]
    data.loc[len(data)] = row

# each date can have several entries over the course of the day; sum to get one entry per day (consistent with database)
api_data = data.groupby(['Date'], as_index=False)['Miles'].sum()
api_data['ID'] = pd.Series('int')

ID = 1
for i in range(0, len(api_data)):
    api_data['ID'][i] = ID
    ID += 1
