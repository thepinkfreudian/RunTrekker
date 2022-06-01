import os, sys

# add parent directory to PATH for imports
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import pandas as pd
import MySQLdb as sql
from datetime import datetime
import plotly.express as px
import plotly.graph_objs as go
import chart_studio.plotly as py
from data.api_data import api_data
import utils.database as db
import utils.utils as utils
from setup import config, environment, push


# function definitions
def get_goal_calendar(run_df, daily_goal):
    goal_calendar = pd.DataFrame(
        columns=['run_date', 'week_start', 'week_end', 'month_name', 'year', 'daily_goal', 'actual_miles'])

    for index, row in run_df.iterrows():
        date = str(row['run_date'])
        week_start, week_end = utils.get_weekdate_range(date)
        month_name = utils.get_month_name(date)
        year = utils.get_year(date)
        actual_miles = row['miles']

        new_row = [date, week_start, week_end, month_name, year, daily_goal, actual_miles]
        goal_calendar.loc[len(goal_calendar)] = new_row

    goal_calendar['actual_miles'] = goal_calendar['actual_miles'].apply(lambda x: round(x, 2))

    return goal_calendar


def get_midpoint_row(route_df):

    latitude = route_df['latitude'][int(round(len(route_df)/2, 0))]
    longitude = route_df['longitude'][int(round(len(route_df)/2, 0))]
    label = 'MIDPOINT'
    poi_type = 'route milestone'

    midpoint_row = [latitude, longitude, label, poi_type]

    return midpoint_row


def get_center_coords(poi_df):

    row = poi_df.loc[poi_df['label'] == 'MIDPOINT']
    center_lat = row['latitude'].values[0]
    center_lon = row['longitude'].values[0]

    return center_lat, center_lon


def get_goals(route_distance):

    goals = {}
    goals['daily'] = round(float(route_distance) / 365, 0)  # try to account for leap years
    goals['weekly'] = round(route_distance / 52, 0)
    goals['yearly'] = route_distance

    return goals


def make_bullets(actual_miles, expected_miles, on_track, time_range):
    
    if on_track:
        color = '#E12194'
    else:
        color = 'red'

    if time_range == 'Weekly':
        domain={'x': [0.1, 1], 'y': [0.7, 0.9]}
    elif time_range == 'Monthly':
        domain={'x': [0.1, 1], 'y': [0.4, 0.6]}
    #elif time_range == 'Yearly':
        #domain={'x': [0.1, 1], 'y': [0.1, 0.3]}

    

    

    fig = go.Indicator(
        mode="number+gauge",
        gauge={'shape': "bullet",
               'axis': {'range': [0, 100], 'visible': False},
               'bar': {'color': '#3396EA',
                       'thickness': 1
                       },
               'bgcolor': '#3C3541'
               },
        #delta={'reference': expected_miles},
        value=(actual_miles / expected_miles) * 100,
        number={'suffix': '%', 'font': {'color': color}},
        domain=domain,
        title={'text': time_range, 'align': 'left', 'font': {'size': 14, 'color': '#ACB7B5'}}
    )

    return fig

mapbox_api_key = config['map']['mapbox_api_key']
mapbox_style = config['map']['mapbox_style']
dashboard_name = config['map']['dashboard_name']
site_css = config['map']['site_css']
start_point = config['map']['start_point']
end_point = config['map']['end_point']

connection_config = config['mySQL']['connection_config']
insert_table = config['mySQL']['insert_tables'][environment]
data_tables = config['mySQL']['data_tables']

today = datetime.strftime(datetime.today(), '%Y-%m-%d')
current_week_start, current_week_end = utils.get_weekdate_range(today)
current_month_name = utils.get_month_name(today)
current_year = utils.get_year(today)

# connect to mySQL instance
conn = sql.connect(connection_config['hostname'],
                   connection_config['username'],
                   connection_config['password'],
                   connection_config['db'])

cursor = conn.cursor()

# update database with Google fit data
# db.update_database(conn, api_data, insert_table)
api_data = pd.read_sql('SELECT * FROM run_data_new', conn)
api_data.columns = ['ID', 'Date', 'Miles']

# bring mySQL data into DataFrames
route_df = db.get_data(conn, data_tables['map_data'])
run_df = db.get_data(conn, data_tables['run_data'])
poi_df = db.get_data(conn, data_tables['poi_data'])

# add start and end locations to poi labels
poi_df.loc[poi_df['label'] == 'START - ', 'label'] = 'START - ' + str(start_point)
poi_df.loc[poi_df['label'] == 'END - ', 'label'] = 'END - ' + str(end_point)

# get midpoint data
poi_id = len(poi_df)
midpoint_row = get_midpoint_row(route_df)
midpoint_row.insert(0, poi_id)
poi_df.loc[len(poi_df)] = midpoint_row

# calculate miles run and generate data frame of only reached coordinates
total_miles_run = round(sum(run_df['miles']), 2)
coordinates_run = route_df[route_df['distance_from_start_mi'] <= total_miles_run]

# define weekly, monthly, yearly mileage goals based on total route distance
route_distance = round(route_df.loc[len(route_df)-1]['distance_from_start_mi'], 2)
goals = get_goals(route_distance)

# get derived dfs
goal_calendar = get_goal_calendar(run_df, goals['daily'])

# actual vs expected / on track
actual_weekly = goal_calendar[goal_calendar['week_start'] == current_week_start]['actual_miles'].sum()
days_passed_in_week = len(goal_calendar[(goal_calendar['actual_miles'] != 0.00) & (goal_calendar['week_start'] == current_week_start)])
weekly_on_track = actual_weekly >= days_passed_in_week * goals['daily']

actual_monthly = float(goal_calendar[goal_calendar['month_name'] == current_month_name]['actual_miles'].sum())
days_in_month = len(goal_calendar[goal_calendar['month_name'] == current_month_name])
days_passed_in_month = len(goal_calendar[(goal_calendar['actual_miles'] != 0.00) & (goal_calendar['month_name'] == current_month_name)])
expected_monthly = goals['daily'] * days_in_month
monthly_on_track = actual_monthly >= days_passed_in_month * goals['daily']

total_days_passed = 365 - len(goal_calendar[goal_calendar['actual_miles'] == 0.00])
yearly_on_track = total_miles_run >= total_days_passed * goals['daily']

# merge dfs for easier Dash app parsing
master_df = coordinates_run.merge(poi_df, how='left', on=['latitude', 'longitude'])
api_data['total_miles'] = api_data['Miles'].cumsum()

master_df['date_reached'] = pd.Series('object')

for index, row in master_df.iterrows():
    if pd.notnull(row['label']):
        miles = row['distance_from_start_mi']
        reached = api_data[api_data['total_miles'] >= miles]
        master_df['date_reached'][index] = reached.iloc[0, 0]


# define custom dataframes for display
poi_reached = master_df[master_df['date_reached'].notna()][['label', 'date_reached']]
poi_reached.columns = ['Route Milestone', 'Date Reached']
last_poi = poi_reached.iloc[len(poi_reached)-1]['Route Milestone']
last_poi_index = poi_df.index[poi_df['label'] == last_poi]
next_poi_row = poi_df.loc[last_poi_index+1]
next_poi_df = route_df.merge(next_poi_row, how='inner', on=['latitude', 'longitude'])

# define layout css
base_font = dict(size=16, family=site_css['fonts']['headings'], color='#3396EA')
annotation_font = dict(color=site_css['colors']['pink'], size=24, family=site_css['fonts']['headings']) 
center_lat, center_lon = get_center_coords(poi_df)

base_map_config = dict(data_frame=route_df,
                       lat='latitude',
                       lon='longitude',
                       color_discrete_sequence=[site_css['colors']['lightgrey']])

base_layout = dict(font=base_font,
                   autosize=True,
                   margin=dict(b=0, l=0, r=0, t=0),
                   mapbox_accesstoken=mapbox_api_key,
                   mapbox_style='mapbox://styles/thepinkfreudian/ckxy1j35q179814ql82sa5sct',
                   #mapbox_style=mapbox_style,
                   showlegend=False,
                   mapbox=dict(zoom=5.25,
                               #center=dict(lat=center_lat,
                                #          lon=-72.0000#center_lon
                                 #          )
                               ),
                   )

coordinates_run_config = dict(name='coordinates run',
                              lat=coordinates_run['latitude'],
                              lon=coordinates_run['longitude'],
                              marker=dict(size=6, color=site_css['colors']['pink'])
                          )

colorsIdx = {'state border': '#3396EA', 'city': 'cyan', 'route milestone': '#FFFFFF'}
sizesIdx = {'state border': 10, 'city': 8, 'route milestone': 14}
colors = poi_df['poi_type'].map(colorsIdx)
sizes = poi_df['poi_type'].map(sizesIdx)
poi_config = dict(name='points of interest',
                  lat=poi_df['latitude'],
                  lon=poi_df['longitude'],
                  mode='markers+text',
                  text=poi_df['label'],
                  hoverinfo='text',
                  textfont=dict(color=site_css['colors']['white'], size=12),
                  textposition='top right',
                  #marker_size=12,
                  marker=dict(size=sizes, color=colors),
                  #marker_color=site_css['colors']['white']
                  )


# generate base tile map zoomed to route and set layout properties
map_fig = px.scatter_mapbox(**base_map_config)
map_fig.update_layout(base_layout)

# add trace for coordinates run
map_fig.add_scattermapbox(**coordinates_run_config)

# add trace for points of interest
map_fig.add_scattermapbox(**poi_config)

# create bullet charts to show progress over intervals
bullets = go.Figure()
weekly_bullet = make_bullets(actual_weekly, goals['weekly'], weekly_on_track, 'Weekly')
monthly_bullet = make_bullets(actual_monthly, expected_monthly, monthly_on_track, 'Monthly')
#yearly_bullet = make_bullets(total_miles_run, goals['yearly'], yearly_on_track, 'Yearly')
bullets.add_trace(weekly_bullet)
bullets.add_trace(monthly_bullet)
#bullets.add_trace(yearly_bullet)

bullets.update_layout(height = 150, margin = {'t': 0, 'b': 0, 'l': 100}, paper_bgcolor = '#171717')

main_bullet = go.Figure()
fig = go.Indicator(
    mode="number+gauge",
    gauge={'shape': "bullet",
           'axis': {'range': [0, 100], 'visible': False},
           'bar': {'color': '#3396EA',
                   'thickness': 1
                   },
           'bgcolor': '#3C3541'
           },
    #delta={'reference': expected_miles},
    value=(total_miles_run / goals['yearly']) * 100,
    number={'suffix': '%', 'font': {'color': '#E12194'}, 'valueformat': '.0f'},
    domain={'x': [.1, 1], 'y': [0, 1]}
    #title={'text': time_range, 'align': 'left', 'font': {'size': 14, 'color': '#ACB7B5'}}
    )
main_bullet.add_trace(fig)
main_bullet.update_layout(height = 25, margin = {'t': 0, 'b': 0, 'l': 0, 'r': 0}, paper_bgcolor = '#171717')

###########################################################################

### push to plotly or show map locally depending on value of 'push'
##if push:
##    py.plot(fig, filename = dashboard_name, auto_open=False)
##else:
##    # display final map
##    fig.show()
