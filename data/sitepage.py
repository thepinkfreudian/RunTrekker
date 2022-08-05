import plotly.graph_objs as go
from data.route import Route
from data.routemap import RouteMap
from data.goals import Goals
from data.theme import Theme


class SitePage:

    def __init__(self, route: Route, routemap: RouteMap, goals: Goals, theme: Theme):
        self.theme = theme
        self.route = route
        self.routemap = routemap
        self.goals = goals
        self.run_data = self.get_run_data()
        self.milestones_reached = self.get_milestones_reached()
        self.last_milestone_reached = self.get_last_milestone()
        self.next_milestone = self.get_next_milestone()
        self.table_styles = self.get_table_styles()

    def get_route_tagline(self):
        origin = self.route.data.loc[0, "origin"]
        destination = self.route.data.loc[0, "destination"]

        return f"{origin} to {destination}"

    def get_total_miles_annotation(self):
        return f"Total miles completed: {self.goals.total_miles_run} of {self.route.miles}"

    def get_run_data(self):
        df = self.goals.run_data[["run_date", "miles", "total_miles"]]
        df.columns = ["Date", "Miles", "Total Miles"]
        df["Miles"] = df["Miles"].apply(lambda x: round(x, 2))
        df["Total Miles"] = df["Total Miles"].apply(lambda x: round(x, 2))
        return df

    def get_milestones_reached(self):
        df = self.goals.milestones_reached[["milestone_label", "date_reached"]]
        df.columns = ["Milestone", "Date Reached"]
        return df

    def get_last_milestone(self):
        return self.goals.milestones_reached.iloc[len(self.goals.milestones_reached) - 1]

    def get_next_milestone(self):
        return self.routemap.milestone_coordinates[self.routemap.milestone_coordinates["reached"] == 0].iloc[0]

    def make_main_bullet(self):
        main_bullet = go.Figure()
        fig = go.Indicator(
            mode="number+gauge",
            gauge={"shape": "bullet",
                   "axis": {"range": [0, 100],
                            "visible": False},
                   "bar": {"color": self.theme.colors["headers"],
                           "thickness": 1},
                   "bgcolor": self.theme.colors["bullet_backgrounds"]},
            value=(self.goals.total_miles_run / self.goals.data["total_miles"].iloc[0]) * 100,
            number={"suffix": "%", "font": {"color": self.theme.colors["run_trace_links_labels"]},
                    "valueformat": ".0f"},
            domain={"x": [.1, 1], "y": [0, 1]}
        )
        main_bullet.add_trace(fig)
        main_bullet.update_layout(height=25, margin={"t": 0, "b": 0, "l": 0, "r": 0},
                                  paper_bgcolor=self.theme.colors["backgrounds"])

        return main_bullet

    def make_sub_bullet(self, time_range: str, on_track: bool, actual_miles: float, expected_miles: float):
        if on_track:
            percentage_color = self.theme.colors["run_trace_links_labels"]
        else:
            percentage_color = self.theme.colors["off_track"]  # replace

        if time_range.lower() == "weekly":
            domain = {"x": [0.1, 1], "y": [0.7, 0.9]}
        elif time_range.lower() == "monthly":
            domain = {"x": [0.1, 1], "y": [0.4, 0.6]}

        sub_bullet = go.Indicator(
            mode="number+gauge",
            gauge={"shape": "bullet",
                   "axis": {"range": [0, 100],
                            "visible": False},
                   "bar": {"color": self.theme.colors["headers"],
                           "thickness": 1},
                   "bgcolor": self.theme.colors["bullet_backgrounds"]},
            value=(actual_miles / expected_miles) * 100,
            number={"suffix": "%", "font": {"color": percentage_color}},
            domain=domain,
            title={"text": time_range, "align": "left", "font": {"size": 14,
                                                                 "color": self.theme.colors["bullet_labels"]}}
        )

        return sub_bullet

    def make_sub_bullets(self):
        sub_bullets = go.Figure()
        weekly = self.make_sub_bullet("weekly",
                                      self.goals.weekly_on_track,
                                      self.goals.weekly_miles_completed,
                                      self.goals.data["weekly_miles_goal"].iloc[0])
        monthly = self.make_sub_bullet("monthly",
                                       self.goals.monthly_on_track,
                                       self.goals.monthly_miles_completed,
                                       self.goals.data["monthly_miles_goal"].iloc[0])
        sub_bullets.add_trace(weekly)
        sub_bullets.add_trace(monthly)

        sub_bullets.update_layout(height=150, margin={'t': 0, 'b': 0, 'l': 100},
                                  paper_bgcolor=self.theme.colors["backgrounds"])

        return sub_bullets

    def get_table_styles(self):
        return dict(style_header={"backgroundColor": self.theme.colors["backgrounds"],
                                  "font-family": self.theme.fonts["headings"],
                                  "fontSize": 16,
                                  "color": self.theme.colors["headers"]
                                  },
                    style_cell={"text-align": "left",
                                "backgroundColor": self.theme.colors["backgrounds"],
                                "font-family": self.theme.fonts["paragraphs"],
                                "fontSize": 14,
                                "color": self.theme.colors["text"]},
                    style_data={"width": "auto"})
