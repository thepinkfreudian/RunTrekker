import os
from datetime import datetime

from data import route, routemap, goals, sitepage, theme
from utilities import database, themes

import dash
from dash import dcc
from dash import html
from dash import dash_table

if os.environ.get("ENVIRONMENT") is None:
    import dotenv
    dotenv.load_dotenv()

HOST = os.environ.get("HOST")
DATABASE = os.environ.get("DATABASE")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")

MAPBOX_API_KEY = os.environ.get("MAPBOX_API_KEY")
MAPBOX_STYLE_URL = os.environ.get("MAPBOX_STYLE_URL")

db = database.Database(HOST, DATABASE, USER, PASSWORD)
theme = theme.Theme(themes.default)
route = route.Route(db)
goals = goals.Goals(route, db)
print(goals.weekly_on_track, goals.monthly_on_track)
routemap = routemap.RouteMap(route, theme, MAPBOX_API_KEY, MAPBOX_STYLE_URL)
routemap.get_mapbox(theme.colors["route_trace"], {"size": 16, "family": theme.fonts["paragraphs"], "color": theme.colors["run_trace_links_labels"]}, 5.25)
routemap.add_run_trace(theme.colors["run_trace_links_labels"])
routemap.add_milestones_trace(theme.colors["text"], 12, theme.colors["milestones"], theme.sizes["milestones"])
mapbox = routemap.mapbox

page = sitepage.SitePage(route, routemap, goals, theme)
main_bullet = page.make_main_bullet()
sub_bullets = page.make_sub_bullets()
route_tagline = page.get_route_tagline()
total_miles_annotation = page.get_total_miles_annotation()
milestones_reached = page.get_milestones_reached()
last_milestone = f"Last milestone reached: {page.last_milestone_reached.loc['milestone_label']} ({page.last_milestone_reached.loc['date_reached']})"
miles_to_next = round(page.next_milestone.loc["miles_from_origin"] - goals.total_miles_run, 2)
next_milestone = f"Next milestone: {page.next_milestone.loc['milestone_label']} in {miles_to_next} miles"

weekly_annotation = f"Weekly: {goals.weekly_miles_completed} of {round(goals.data['weekly_miles_goal'].iloc[0], 2)}"
monthly_annotation = f"Monthly: {goals.monthly_miles_completed} of {round(goals.data['monthly_miles_goal'].iloc[0], 2)}"

# determine default page for data table based on date
day = datetime.now().timetuple().tm_yday
page_current = int(day/10)

CSS = ["/assets/custom.css"]
app = dash.Dash(__name__,
                external_stylesheets=CSS,
                meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "og:title", "content": "RunTrekker"},
        {"name": "og:description", "content": "A route tracking app for runners."},
        {"name": "og:image", "content": "https://thepinkfreudian.com/site_thumbnail.png"}
    ])
app.title = "RunTrekker"
server = app.server


app.layout = html.Div(style={"backgroundColor": theme.colors["backgrounds"], "color": theme.colors["text"]}, children=[

    # title / tagline
    html.Div(children=[
        html.H1(children="RunTrekker", className="title", style={"color": theme.colors["headers"]}),
        html.H3(children=route_tagline),
        html.Span("A Python Dash app to track running mileage progress"),
        html.Br(),
        html.Span("on a chosen route between cities."),
        dcc.Graph(id="main-bullet",
                  figure=main_bullet,
                  config={"displayModeBar": False}),
        html.Div(children=total_miles_annotation),
        html.Div(children=last_milestone),
        html.Div(children=next_milestone),
        html.Div(id="links", children=[
            html.A("source code", href="https://www.github.com/thepinkfreudian/runtrekker", target="_blank",
                   className="inline-link", style={"color": theme.colors["run_trace_links_labels"]})
            ])
        ], className="over"),
    
    # first row
    html.Div(id="row-1", children=[

        
        html.Div(id="left-col-row-1", children=[
            dcc.Graph(
                id="map-fig",
                style={"height": "100%"},
                figure=mapbox,
                config={"responsive": True, "scrollZoom": False},
                )
            ])
        ], className="row"),

    # row 2
    html.Div(id="row-2", children=[

        html.Div(id="left-col-row2", children=[

            html.Div(children=[
                html.H3(children="Progress Towards Mileage Goals"),
                html.Div(id="bullet-wrapper", children=[
                    dcc.Graph(id="progress-rate",
                              figure=sub_bullets)
                    ])
                ], className="col-element"),

            html.Div(children=[
                html.Div(children=weekly_annotation),
                html.Div(children=monthly_annotation)
                ], className="col-element"),

            html.Div(children=[
                html.H3("Route Milestones Reached"),

                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in page.milestones_reached],
                    data=page.milestones_reached.to_dict("records"),
                    style_as_list_view=True,
                    style_header=page.table_styles["style_header"],
                    style_cell=page.table_styles["style_cell"],
                    style_data=page.table_styles["style_data"]
                    )
                ], className="col-element")
            
            ], className="dash-container two-col"),

        html.Div(id="right-col-r2", children=[
            html.H3(children="Run Data"),

            dash_table.DataTable(id="run-data-table",
                columns=[{"name": i, "id": i} for i in page.run_data.columns],
                data=page.run_data.to_dict("records"),
                page_action="native",
                page_current=page_current,
                page_size= 10,
                style_as_list_view=True,
                style_header=page.table_styles["style_header"],
                style_cell=page.table_styles["style_cell"],
                style_data=page.table_styles["style_data"]
                )
            ], className="dash-container two-col")
            
        ], className="row"),

    html.Div(id="footer", children=[
        html.Div("created by ", className="footer-text"),
        html.A(id="email-link", children=["thepinkfreudian"], href="mailto:pink@thepinkfreudian.com", target="_blank",
               className="footer-text"),
        html.Div(", 2022.", className="footer-text")
        ], className="row footer")
    
], className="container")

if __name__ == "__main__":
    app.run_server()
