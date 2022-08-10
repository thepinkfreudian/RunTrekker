import pandas as pd
from utilities.database import Database


class Route:

    def __init__(self, database: Database):
        self.db = database
        self.id = self.get_id()
        self.data = self.get_data("route_data", order_by=["miles_from_origin ASC"])
        self.miles = float(round(self.data.loc[len(self.data)-1, "miles_from_origin"], 1))

    def get_id(self):
        row = self.db.get("route", ["route_id"], {"active": 1})
        return row.loc[0, "route_id"]

    def get_data(self, table: str, order_by=None):
        return self.db.get(table, ["*"], where={"route_id": self.id}, order_by=order_by)

    def activate_route(self, table: str):
        query = f"UPDATE {table} SET active = 1 WHERE route_id = {self.id}"
        self.db.query(query)

    def inactivate_route(self, table: str):
        query = f"UPDATE {table} SET active = 0 WHERE route_id = {self.id}"
        self.db.query(query)

    def add_milestone(self, label: str, milestone_type: str, latitude: float, longitude: float):
        """
        add a milestone to the route.
        :param label: Name of the milestone (as it should appear on the map)
        :param milestone_type: city, state border, etc.
        :param latitude: coordinate
        :param longitude: coordinate
        :return: None
        """
        df = pd.DataFrame(columns=["route_id", "label", "milestone_type", "latitude", "longitude"])
        df.loc[0] = [self.id, label, milestone_type, latitude, longitude]
        self.db.insert("route_milestone", df)


