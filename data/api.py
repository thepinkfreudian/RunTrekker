import json
import pandas as pd
import requests
from datetime import datetime


class GoogleFitAPI:

    def __init__(self, client_id: str,
                 client_secret: str,
                 scope: str,
                 refresh_token: str,
                 token_uri: str):
        self.oauth_data = {"client_id": client_id,
                           "client_secret": client_secret,
                           "scope": scope,
                           "grant_type": "refresh_token",
                           "refresh_token": refresh_token}
        self.token_uri = token_uri
        self.api_url = "https://www.googleapis.com/fitness/v1/users/me/dataSources/"
        self.datasource = "derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta"
        self.token = None
        self.response = None

    @staticmethod
    def date_to_nanoseconds(date: datetime):
        date = datetime.combine(date, datetime.min.time())
        nanoseconds = date.timestamp() * 1000000000

        return int(nanoseconds)

    @staticmethod
    def nanoseconds_to_date(nanoseconds: int):
        date = datetime.fromtimestamp(nanoseconds // 1000000000)

        return date.date()

    def get_token(self):
        try:
            response = requests.post(self.token_uri, data=self.oauth_data)
            self.token = json.loads(response.text)["access_token"]
        except requests.HTTPError as e:
            print(f"Error generating access token: {e}")

    def build_url(self, dataset: str):

        self.api_url += f"{self.datasource}/datasets/{dataset}"

    def request_data(self):

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(self.api_url, headers=headers)
            return response.json()
        except requests.HTTPError as e:
            print(f"Error getting FIT data: {e}")

    def parse_response(self, response: requests.Response):
        run_data = pd.DataFrame(columns=["miles", "run_date"])

        points = response["point"]

        for i in range(0, len(points)):
            miles = int(points[i]['value'][0]['fpVal']) * 0.000621371  # m to mi
            date = self.nanoseconds_to_date(int(points[i]['startTimeNanos']))
            row = [miles, date]
            run_data.loc[len(run_data)] = row

        # each date can have several entries over the course of the day;
        # sum to get one entry per day (consistent with database)
        run_data = run_data.groupby(['run_date'], as_index=False)['miles'].sum()
        run_data['run_date'] = pd.to_datetime(run_data['run_date']).dt.date

        return run_data
