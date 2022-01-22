import dash
from dash import dcc
from dash import html
from dash import dash_table

import data.plotly_fig as figs
from data.api_data import api_data
from setup import config

run_df = figs.run_df[['run_date', 'miles']]
run_df.columns = ['Date', 'Miles']
run_df['Miles'] = run_df['Miles'].apply(lambda x: round(x, 2))
    
# div/page attributes
tagline = config['map']['start_point'] + ' to ' + config['map']['end_point']
annotation = 'Total miles completed: ' + str(figs.total_miles_run) + ' of ' + str(figs.route_distance)
last_poi_reached = figs.poi_reached.iloc[len(figs.poi_reached)-1]

# styles
table_styles = dict(style_header={'backgroundColor': '#171717',
                                  'font-family': 'Secular One',
                                  'fontSize': 16,
                                  'color': '#3396EA'
                                  },
                    style_cell={'text-align': 'left',
                                'backgroundColor': '#171717',
                                'font-family': 'Martel Sans',
                                'fontSize': 14,
                                'color': '#FFFFFF'},
                    style_data={'width': 'auto'})



CSS = ['/assets/custom.css']
app = dash.Dash(__name__,
                external_stylesheets=CSS,
                meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {'name': 'og:title', 'content': 'RunTrekker'},
        {'name': 'og:description', 'content': 'A route tracking app for runners.'},
        {'name': 'og:image', 'content': 'https://thepinkfreudian.com/site_thumbnail.png'}
    ])
server = app.server


app.layout = html.Div(children=[

##    # title / tagline
    #html.H1(children='RunTrekker', style={'z-index': '0'}, className='title'),

    html.Div(children=[
        html.H1(children='RunTrekker', className='title'),
        html.H3(children=tagline),
        dcc.Graph(id='main-bullet',
            figure=figs.main_bullet,
                  config={'displayModeBar': False}),
        html.Div(children=annotation),
        html.Div(children='Latest Milestone: ' + str(last_poi_reached['Route Milestone']) + ' (' + str(last_poi_reached['Date Reached']) + ')'),
        html.Div(id='links', children=[
            dcc.Link('about', href='https://www.thepinkfreudian.com/about.html', className='inline-link'),
            html.Span('  -  ', style={'display': 'inline-block'}),
            html.A('source code', href='https://www.github.com/thepinkfreudian/runtrekker', target="_blank", className='inline-link')
            ])
        ], className='over'),
    
    # first row
    html.Div(id='row-1', children=[

        
        html.Div(id='left-col-row-1', children=[
            dcc.Graph(
                id='map-fig',
                style={'height': '100%'},
                figure=figs.map_fig,
                config={'responsive': True},
                )
            ], style = {#'display': 'inline-block',
                'width': '100vw', 'height': '100vh', 'overflow': 'hidden', 'z-index': '-1', 'position': 'absolute'})

        

        ], style={'height': '100vh'},
             className='row'),

    # row 2
    html.Div(id='row-2', children=[

        html.Div(id='left-col-row2', children=[

            html.Div(children=[
                html.H3(children='Progress Towards Mileage Goals'),
                html.Div(id='bullet-wrapper', children=[
                    dcc.Graph(id='progress-rate',
                              figure=figs.bullets)
                    ])
                ], className='col-element'),

            html.Div(children=[
                html.H3("Route Milestones Reached"),

                dash_table.DataTable(
                    columns=[{'name': i, 'id': i} for i in figs.poi_reached.columns],
                    data=figs.poi_reached.to_dict('records'),
                    style_as_list_view=True,
                    style_header=table_styles['style_header'],
                    style_cell=table_styles['style_cell'],
                    style_data=table_styles['style_data']
                    )
                ], className='col-element')
            
            ], className='dash-container two-col'),

        html.Div(id='right-col-r2', children=[
            html.H3(children='Run Data'),

            dash_table.DataTable(id='run-data-table',
                columns=[{'name': i, 'id': i} for i in run_df.columns],
                data=run_df.to_dict('records'),
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_as_list_view=True,
                style_header=table_styles['style_header'],
                style_cell=table_styles['style_cell'],
                style_data=table_styles['style_data']
                )
            ], className='dash-container two-col')
            
        ], style={'width': '100%'}, className='row'),

    html.Div(id='footer', children=[
        html.Div('created by ', className='footer-text'),
        html.A(id='email-link', children=['thepinkfreudian'], href='mailto:pink@thepinkfreudian.com', target='_blank', className='footer-text'),
        html.Div(', 2022.', className='footer-text')
        ], className='row footer')
    
], className='container')

if __name__ == '__main__':
    app.run_server(debug=True)
