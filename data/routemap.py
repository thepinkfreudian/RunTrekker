from data.route import Route
from data.theme import Theme
import plotly.express as px


class RouteMap:

    def __init__(self, route: Route, theme: Theme, mapbox_api_key: str, mapbox_style_url: str):
        self.route = route
        self.theme = theme
        self.run_coordinates = self.get_run_coordinates()
        self.milestone_coordinates = self.get_milestone_coordinates()
        self.route_trace = None
        self.run_trace = None
        self.milestone_trace = None
        self.mapbox = None
        self.mapbox_api_key = mapbox_api_key
        self.mapbox_style_url = mapbox_style_url

    def get_run_coordinates(self):

        return self.route.data[self.route.data["reached"] == 1]

    def get_milestone_coordinates(self):

        return self.route.data[self.route.data["milestone_label"] != ""]

    def get_map_style(self, font: dict, zoom: float):

        return dict(font=dict(size=16,
                              family=self.theme.fonts["headings"],
                              color=self.theme.colors["headers"]),
                    autosize=True,
                    margin=dict(b=0, l=0, r=0, t=0),
                    mapbox_accesstoken=self.mapbox_api_key,
                    mapbox_style=self.mapbox_style_url,
                    showlegend=False,
                    mapbox=dict(zoom=zoom))  # 5.25

    def get_route_trace(self, trace_color: str):

        self.route_trace = dict(data_frame=self.route.data,
                                lat="latitude",
                                lon="longitude",
                                color_discrete_sequence=[trace_color])  # light grey

    def get_run_trace(self, trace_color: str):

        self.run_trace = dict(name="coordinates run",
                              lat=self.run_coordinates["latitude"],
                              lon=self.run_coordinates["longitude"],
                              marker=dict(size=6, color=trace_color))  # pink

    def get_milestone_trace(self, font_color: str, font_size: int, milestone_colors: dict, milestone_sizes: dict):

        colors = self.milestone_coordinates["milestone_type"].map(milestone_colors)
        sizes = self.milestone_coordinates["milestone_type"].map(milestone_sizes)
        self.milestone_trace = dict(name="milestones",
                                    lat=self.milestone_coordinates["latitude"],
                                    lon=self.milestone_coordinates["longitude"],
                                    mode='markers+text',
                                    text=self.milestone_coordinates["milestone_label"],
                                    hoverinfo='text',
                                    textfont=dict(color=font_color, size=font_size),  # white, size 12
                                    textposition='top right',
                                    marker=dict(size=sizes, color=colors))

    def add_run_trace(self, run_trace_color: str):
        self.get_run_trace(run_trace_color)
        self.mapbox.add_scattermapbox(**self.run_trace)

    def add_milestones_trace(self, font_color: str, font_size: int, milestone_colors: dict, milestone_sizes: dict):
        self.get_milestone_trace(font_color, font_size, milestone_colors, milestone_sizes)
        self.mapbox.add_scattermapbox(**self.milestone_trace)

    def get_mapbox(self, route_trace_color: str, font: dict, zoom: float):
        self.get_route_trace(route_trace_color)
        mapbox = px.scatter_mapbox(**self.route_trace)
        mapbox.update_layout(self.get_map_style(font, zoom))

        self.mapbox = mapbox
