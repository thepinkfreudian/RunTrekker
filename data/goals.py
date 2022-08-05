from utilities.database import Database
from data.route import Route
from datetime import datetime, timedelta
import pandas as pd


class Goals:

    def __init__(self, route: Route, database: Database):
        self.db = database
        self.route = route
        self.data = self.get_data("goal_data")
        self.run_data = self.get_run_data()
        self.milestones_reached = self.get_milestones_reached()
        self.weekdates = self.get_weekdates()
        self.total_miles_run = self.get_miles_completed()
        self.weekly_miles_completed = self.get_actual_miles("weekly")
        self.monthly_miles_completed = self.get_actual_miles("monthly")
        self.weekly_on_track = self.is_on_track("weekly")
        self.monthly_on_track = self.is_on_track("monthly")

    @staticmethod
    def get_weekdates() -> tuple:
        date = datetime.today()
        monday = date - timedelta(days=date.weekday())  # .weekday() returns integer, Monday is 1
        sunday = monday + timedelta(days=6)

        return monday.date(), sunday.date()

    @staticmethod
    def get_first_of_month():
        return datetime.today().replace(day=1).date()

    def get_data(self, table: str):
        return self.db.get(table, ["*"], where={"route_id": self.route.id})

    def get_miles_completed(self):
        miles = self.db.get_max_value("route_data", "miles_from_origin", where={"route_id": self.route.id,
                                                                               "reached": 1})
        return float(round(miles, 2))

    def get_run_data(self):
        run_data = self.db.get("run_data", ["*"])
        run_data["total_miles"] = run_data.miles.cumsum()

        return run_data

    def get_actual_miles(self, timeframe: str):

        query = f"SELECT SUM(miles) FROM run_data WHERE run_date BETWEEN "
        if timeframe.lower() == "weekly":
            query += f"'{self.weekdates[0]}' AND '{self.weekdates[1]}'"
        if timeframe.lower() == "monthly":
            query += f"'{self.get_first_of_month()}' AND '{datetime.today().date()}'"

        rows = self.db.query(query)
        return float(round(rows.first()[0], 2))

    def get_milestones_reached(self):

        reached = self.route.data[(self.route.data["reached"] == 1) & (self.route.data["milestone_label"] != "")]
        reached["date_reached"] = pd.Series('object')
        for index, row in reached.iterrows():
            miles = reached.loc[index, "miles_from_origin"]
            date_reached = self.run_data[self.run_data["total_miles"] >= miles]
            reached.loc[index, "date_reached"] = date_reached.iloc[0, 1]  # first date returned

        return reached

    def is_on_track(self, timeframe: str):
        if timeframe.lower() == "weekly":
            weekday = datetime.today().weekday()
            return self.weekly_miles_completed / weekday >= self.data["daily_miles_goal"].iloc[0] * weekday
        if timeframe.lower() == "monthly":
            day = datetime.today().day
            return self.monthly_miles_completed / day >= self.data["daily_miles_goal"].iloc[0] * day

    def get_percentages(self, timeframe: str):
        if timeframe.lower() == "weekly":
            return round(self.weekly_miles_completed / self.data["weekly_miles_goal"].iloc[0], 1)
        if timeframe.lower() == "monthly":
            return round(self.monthly_miles_completed / self.data["monthly_miles_goal"].iloc[0], 1)



