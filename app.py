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

# database
HOST = os.environ.get("HOST")
DATABASE = os.environ.get("DATABASE")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")

# mapbox
MAPBOX_API_KEY = os.environ.get("MAPBOX_API_KEY")
MAPBOX_STYLE_URL = os.environ.get("MAPBOX_STYLE_URL")

# initialize data objects
db = database.Database(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
theme = theme.Theme(theme_data=themes.default)
route = route.Route(database=db)
goals = goals.Goals(route=route, database=db)
routemap = routemap.RouteMap(route=route,
                             theme=theme,
                             mapbox_api_key=MAPBOX_API_KEY,
                             mapbox_style_url=MAPBOX_STYLE_URL)

# create map figure
routemap.get_mapbox(route_trace_color=theme.colors["route_trace"],
                    font={"size": 16,
                          "family": theme.fonts["paragraphs"],
                          "color": theme.colors["run_trace_links_labels"]},
                    zoom=5.25)

routemap.add_run_trace(run_trace_color=theme.colors["run_trace_links_labels"])
routemap.add_milestones_trace(font_color=theme.colors["text"],
                              font_size=12,
                              milestone_colors=theme.colors["milestones"],
                              milestone_sizes=theme.sizes["milestones"])
mapbox = routemap.mapbox

# initialize site object
page = sitepage.SitePage(route, routemap, goals, theme)

# get site graph / display elements
main_bullet = page.make_main_bullet()
sub_bullets = page.make_sub_bullets()
route_tagline = page.get_route_tagline()
total_miles_annotation = page.get_total_miles_annotation()
milestones_reached = page.get_milestones_reached()
last_milestone = f"Last milestone reached: {page.last_milestone_reached.loc['milestone_label']} " \
                 f"({page.last_milestone_reached.loc['date_reached']})"
miles_to_next = round(page.next_milestone.loc["miles_from_origin"] - goals.total_miles_run, 2)
next_milestone = f"Next milestone: {page.next_milestone.loc['milestone_label']} in {miles_to_next} miles"

weekly_annotation = f"Weekly: {goals.weekly_miles_completed} of {round(goals.data['weekly_miles_goal'].iloc[0], 2)}"
monthly_annotation = f"Monthly: {goals.monthly_miles_completed} of {round(goals.data['monthly_miles_goal'].iloc[0], 2)}"

# determine default page for data table based on date
day = datetime.now().timetuple().tm_yday
page_current = int(day/10)

# initiate app
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

# define app layout
app.layout = html.Div(style={"backgroundColor": theme.colors["backgrounds"], "color": theme.colors["text"]}, children=[

    # title / tagline
    html.Div(children=[
        html.H1(children="RunTrekker", className="title", style={"color": theme.colors["headers"]}),
        html.H3(children=route_tagline),
        html.Span("A Python Dash app to track running mileage progress"),
        html.Br(),
        html.Span("on a chosen route between cities."),

        # main progress bullet graph
        dcc.Graph(id="main-bullet",
                  figure=main_bullet,
                  config={"displayModeBar": False}),
        html.Div(children=total_miles_annotation),

        # milestones summary
        html.Div(children=last_milestone),
        html.Div(children=next_milestone),

        # source code link
        html.Div(id="links", children=[
            html.A("source code", href="https://www.github.com/thepinkfreudian/runtrekker", target="_blank",
                   className="inline-link", style={"color": theme.colors["run_trace_links_labels"]})
            ])
        ], className="over"),
    
    # row 1
    html.Div(id="row-1", children=[

        # map
        html.Div(id="left-col-row-1", children=[
            dcc.Graph(
                id="map-fig",
                style={"height": "100%"},
                figure=mapbox,
                config={"responsive": True, "scrollZoom": False, "staticPlot": True},
                )
            ])
        ], className="row"),

    # row 2
    html.Div(id="row-2", children=[

        # row 2 column 1
        html.Div(id="left-col-row2", children=[

            # sub-bullet progress graphs
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

            # milestones reached table
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

        # row 2 column 2
        html.Div(id="right-col-r2", children=[

            # run data table
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

    # footer
    html.Div(id="footer", children=[
        html.Div("created by ", className="footer-text"),
        html.A(id="email-link", children=["thepinkfreudian"], href="mailto:pink@thepinkfreudian.com", target="_blank",
               className="footer-text", style={"color": theme.colors["run_trace_links_labels"]}),
        html.Div(", 2022.", className="footer-text")
        ], className="row footer")
    
], className="container")

if __name__ == "__main__":
    app.run_server()
