import os

from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
from utils import database, openai_agent
from attrs.converters import to_bool

HOSTNAME = os.getenv('HOST')
PORT = os.getenv('PORT')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')
DEBUG = os.getenv('DEBUG','False')

config = dict(host='dell2', port='5555', user='user', password='password', database='restaurants')

app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1('Michelin Star Restaurants'),
    html.Div(id='openai-init', children=[
        dcc.Input(id='openai-api-key-input',
                  type='text',
                  value=None,
                  placeholder='Provide OpenAI API key',
                  disabled=False,
                  persistence=False,
                  persistence_type='memory'),
        html.Button(id='openai-api-key-button', children='Submit', disabled=False)
    ]),
    html.Div(id='locations-select', children=[
        dcc.Dropdown(id='locations-sample', options=[
            dict(label='Country', value='country'),
            dict(label='City', value='city')
        ], value='city'),
        dcc.Dropdown(id='locations', options=[], value=None, searchable=True)
    ]),
    html.Div(id='restaurant-select', children=[
        dcc.Checklist(id='restaurant-select-price'),
        dcc.Checklist(id='restaurant-select-award'),
        dcc.Dropdown(id='scatter-map-style')
    ]),
    dcc.Store(id='mysql_statement'),
    html.Div(id='restaurant-display', children=[]),
    html.Div(id='openai-interact', children=[]),
    dcc.Loading(html.Div(id='openai-response', children=[])),
])


@app.callback(Output('openai-response','children', allow_duplicate=True),
              Input('mysql_statement', 'data'),
              Input('openai-api-key-input', 'value'),
              Input('openai-ask-button-submit','n_clicks'),
              State('openai-text-area-input', 'value'),
              prevent_initial_call=True)
def openai_agent_response(sql_statement, openai_api_key, n_clicks, value):
    print(f'openai_agent_response: openai_api_key = {openai_api_key} sql_statement = {sql_statement} n_clicks = {n_clicks} input = {value}')

    if value and sql_statement:
        agent_executor = openai_agent.get_agent_executor(database_config=config,OPENAI_API_KEY=openai_api_key)
        openai_query = f"""
        PROMPT: {value} 
        SQL_QUERY: {sql_statement}
        """
        try:

            result = agent_executor.invoke(
                {'messages': [('user', openai_query)]},
                debug=True
            )
            print(f'OpenAI agent response: {result}')

            content = result['messages'][-1].content
            return [dcc.Markdown(content)]
        except Exception as err:
            error_message = err.body['message']
            return [html.P(f'Unable to perform request to OpenAI: {error_message}')]
    return []


@app.callback(Output('openai-interact', 'children'),
              Output('openai-api-key-button', 'disabled'),
              Output('openai-api-key-input','disabled'),
              Output('openai-api-key-input', 'type'),
              Input('openai-api-key-button', 'n_clicks_timestamp'),
              Input('locations', 'value'),
              State('openai-api-key-input', 'value'))
def input_openai_key(n_clicks, location_value, button_value):
    print(f'n_clicks_timestamp={n_clicks} location_value={location_value} button_value={button_value}')
    try:
        button_value = str(button_value)
        openai_api_key_check = 'sk-' in button_value and len(button_value) == 51
        if openai_api_key_check and location_value is not None:
            return [
                html.H3(children='Chat-GPT is enabled'),
                dcc.Textarea(id='openai-text-area-input', style={'width': '800px', 'height': '200px'}),
                html.Button(id='openai-ask-button-submit', style={'width': '50px'}, children='Ask'),
            ], True, True, 'password'
        elif openai_api_key_check and location_value is None:
            return [
                html.H4(children='Select a location.'),
            ], True, True, 'password'
        else:
            return [
                html.H4(children='The OpenAI key provided is not valid.'),
            ], False, False, 'text'
    except Exception as err:
        print(f'method input_openai_key() = {err} because of button_value={button_value} type={type(button_value)}')
        return [dcc.Textarea(id='openai-text-area-input',disabled=True),html.Button(id='openai-ask-button-submit', children='Ask',disabled=True)], False, False,'text'


@app.callback(Output('locations','options'),
              Output('locations','value'),
              Output('openai-response','children'),
              Input('locations-sample', 'value'))
def get_locations(locations_sample_value):
    locations = database.get_locations(config=config, location_type=locations_sample_value)
    return locations, None, []


@app.callback(Output('restaurant-select','children'),
              Input('locations-sample', 'value'),
              Input('locations','value'))
def get_locations_filter(locations_sample_value, location_value):
    if location_value:
        price, award = database.get_restaurant_features(config=config,
                                                        location_type=locations_sample_value,
                                                        location_value=location_value)
        return [
            html.H3('Filter by Price:'),
            dcc.Checklist(id='restaurant-select-price', options=list(price), value=[], inline=True),
            html.H3('Filter by Restaurant Award:'),
            dcc.Checklist(id='restaurant-select-award', options=list(award), value=[], inline=True),
            html.H3('Change map style'),
            dcc.Dropdown(id='scatter-map-style', searchable=True, options=[
                'basic', 'carto-darkmatter', 'carto-darkmatter-nolabels', 'carto-positron', 'carto-positron-nolabels',
                'carto-voyager', 'carto-voyager-nolabels', 'dark', 'light', 'open-street-map', 'outdoors', 'satellite',
                'satellite-streets', 'streets', 'white-bg'
            ], value='basic')
        ]


@app.callback(Output('restaurant-display','children'),
              Output('mysql_statement','data'),
              Input('scatter-map-style', 'value'),
              Input('locations-sample', 'value'),
              Input('locations','value'),
              Input('restaurant-select-price','value'),
              Input('restaurant-select-award', 'value'))
def display_restaurants(map_style, locations_sample_value, locations_value, price_value, award_value):
    if locations_value:
        records, sql_statement = database.get_restaurants(config=config,
                                           location_type=locations_sample_value,
                                           locations_value=locations_value,
                                           prices=price_value,
                                           awards=award_value)
        # 'name,address,location,price,cuisine,longitude,latitude,phone_number,url,website_url,award,green_star,facilities_and_services,description'
        figure = px.scatter_map(data_frame=records,
                                lat='latitude',
                                lon='longitude',
                                color='award',
                                text='name',
                                zoom=6,
                                hover_data={
                                    'address': True,
                                    'cuisine': True,
                                    'price': True,
                                    'latitude': False,
                                    'longitude': False,
                                },
                                labels={
                                    'award': 'Award'
                                },
                                map_style=map_style,
                                title=f'Restaurants in {locations_value}')
        return [dcc.Graph(figure=figure)], sql_statement
    return [], None


if __name__ == '__main__':
    app.run(debug=to_bool(DEBUG), host='0.0.0.0', port='8080')
