import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from slugify import slugify

from ..app import app
from ..data import get_groups, get_aggregates, get_filtered_df, currency

groups = get_groups()

def layout(url):
    filters = {}
    url = url[1:].split("/")
    if len(url)==2:
        filters[url[0]] = [url[1]]

    return [
        dcc.Store(id='url-filters', data=filters),
        dcc.Store(id='filters-used'),
        html.Div(className='fl w-25', children=[
            html.Div(className='', children=[
                html.H3(className='mt0 mb2 pa0', children='Filters'),
                dcc.Input(className='w-100 pa1 br2 ba bw1', type='text',
                          placeholder='Search', id='filter-search'),
            ] + [
                html.Div(className='mt3', children=[
                    html.Label(className='mv1 db b', htmlFor='filter-{}'.format(slugify(group)), children=group),
                    dcc.Dropdown(
                        options=[
                            {'label': i, 'value': slugify(i)}
                            for i in items
                        ],
                        multi=True,
                        id='filter-{}'.format(slugify(group)),
                        value=[url[1]] if url[0]==slugify(group) else None
                    )
                ]) for group, items in groups.items()
            ]),
        ]),
        html.Div(className='fl w-75 pl3 flex flex-wrap', children=[
            html.Div(className='w-two-thirds pr3 mb3', id="data-summary"),
            # html.Div(className='w-50 pr3 mb3', id="word-cloud"),
            html.Div(className='w-50 pr3 mb3', id="deals-by-year"),
            html.Div(className='w-50 pr3 mb3', id="deals-by-sector"),
            html.Div(className='w-50 pr3 mb3', id="heat-map"),
            html.Div(className='w-50 pr3 mb3', id="deals-by-status"),
            html.Div(className='w-50 pr3 mb3', id="deals-by-region"),
            html.Div(className='w-50 pr3 mb3', id="deals-by-deprivation"),
            html.Div(className='w-100', id="about-the-data", children=[
                html.H3(className='', children='About our data'),
                dcc.Markdown(className='', children='''
Varius consectetuer tempor nec penatibus tortor, dolor class aenean accumsan 
leo, a odio quam sociosqu duis, sociosqu ante iaculis vivamus sollicitudin 
habitant. Gravida auctor lorem hac adipiscing, porta blandit elit faucibus 
bibendum, elementum laoreet ligula enim sociosqu, fusce eu mattis lobortis 
varius, libero dapibus tincidunt. Congue phasellus ante facilisis hymenaeos 
torquent, mollis habitant dictum vehicula lacinia.

Nascetur arcu mi aptent gravida, metus scelerisque justo est velit arcu, 
parturient elit taciti quam eros, donec tempus aptent nec etiam. Ridiculus 
eget eleifend sodales nisi, ut nostra.

Euismod lectus velit integer elit habitasse, fusce urna tempor eget, ut 
rhoncus cum montes, tortor fusce luctus imperdiet lacus. Condimentum iaculis 
per eu tempus, netus etiam lacinia ac ridiculus aenean, velit vehicula 
tristique luctus accumsan phasellus gravida pharetra,. Mattis nam montes 
vestibulum dis, morbi parturient potenti mattis, nunc in enim ac curae, 
ultrices tempor cursus sit dis. Diam potenti maecenas habitant ornare sed, 
curae habitant consequat sagittis sem justo consequat, curae laoreet netus 
pretium. Per nibh pulvinar ligula, nulla ipsum felis.
                '''),
            ]),
        ]),
        html.Pre(id='filters-used-pre', className='w-100 fl',
                 children=json.dumps(filters)),
    ]


@app.callback([Output('filters-used', 'data'),
               Output('filters-used-pre', 'children')],
              [Input('filter-search', 'value')] + [
                  Input('filter-{}'.format(slugify(group)), 'value') for group in groups.keys()
              ],
              [State('url-filters', 'data')])
def update_filters(*args):
    args = list(args)
    existing_filters = args.pop()
    filters = existing_filters or {}

    filter_search = args.pop(0) or ""
    filters["search"] = filter_search

    args = dict(zip([
        'filter-{}'.format(slugify(group)) for group in groups.keys()
    ], args))

    for k, v in args.items():
        key = k.replace("filter-", "")
        if v:
            filters[key] = list(set(filters.get(key, []) + v))
    
    return (filters, json.dumps(filters),)

@app.callback([Output("data-summary", 'children'),
               Output("word-cloud", 'children'),
               Output("deals-by-year", 'children'),
               Output("deals-by-sector", 'children'),
               Output("heat-map", 'children'),
               Output("deals-by-status", 'children'),
               Output("deals-by-region", 'children'),
               Output("deals-by-deprivation", 'children')],
              [Input("filters-used", 'data')])
def output_charts(filters):
    deals = get_filtered_df(filters)
    agg = get_aggregates(deals)

    if len(deals)==0:
        return (
            html.Div(className='ba bw2 b--blue br3 pa2', children=[
                'No deals found that match criteria'
            ]),  # data-summary
            None,  # word-cloud
            None,  # deals-by-year
            None,  # deals-by-sector
            None,  # heat-map
            None,  # deals-by-status
            None,  # deals-by-region
        )

    return (
        data_summary(agg),  # data-summary
        None,  # word-cloud
        deals_by_year(agg),  # deals-by-year
        deals_by_sector(agg), # deals-by-sector
        heat_map(deals),  # heat-map
        deals_by_status(agg),  # deals-by-status
        deals_by_region(agg), # deals-by-region
        deals_by_deprivation(agg), # deals-by-deprivation
    )


def data_summary(agg):
    return html.Div(className='ba bw2 b--blue br3 pa2', children=[
        html.P(className='mt0 mb3 pa0', children=[
            html.Strong("{:,.0f}".format(agg['summary']['recipient_id'])),
            ' organisations received social investment in ',
            html.Strong("{:,.0f}".format(agg['summary']['deal_count'])),
            ' deals between ',
            "{:.0f}".format(agg['summary']['deal_year_min']),
            ' and ',
            "{:.0f}.".format(agg['summary']['deal_year_max']),
        ]),
        html.P(className='mt0 mb3 pa0', children=[
            html.Strong(currency(agg['summary']['deal_value'])),
            ' of social investment arranged',
        ]),
        html.Ul(className='', children=[
            html.Li(className='', children=[
                html.Strong(currency(agg['summary']['equity_value'])),
                ' of equity arranged ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['equity_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["equity_value"] else None,
            html.Li(className='', children=[
                html.Strong(currency(agg['summary']['credit_value'])),
                ' of credit ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['credit_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["credit_value"] else None,
            html.Li(className='', children=[
                html.Strong(currency(agg['summary']['grants_value'])),
                ' of grants ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['grants_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["grants_value"] else None,
        ]) if (agg['summary']['deal_value'] > 0) else None,
        html.P(className='mt0 mb0 pa0', children=[
            '*Based on data from ',
            ", ".join(agg['collections'].index),
        ]),
    ]),

def deals_by_year(agg):
    data = agg["by_year"]["deal_count"].unstack()
    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Scatter(
                    x=data.columns.tolist(),
                    y=d.tolist(),
                    name=fund,
                ) for fund, d in data.iterrows()
            ],
            layout=go.Layout(
                title='Deals by year',
                showlegend=True,
                legend=go.layout.Legend(
                    x=0,
                    y=1.0
                ),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30)
            )
        ),
        style={'maxHeight': '300px'},
        id='deals-by-year-fig'
    )

def deals_by_sector(agg):
    data = agg["by_classification"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().index
    data = data[column_order]

    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Bar(
                    y=data.columns.tolist(),
                    x=d.tolist(),
                    name=fund,
                    orientation='h',
                ) for fund, d in data.iterrows()
            ],
            layout=go.Layout(
                title='Deals by sector',
                showlegend=True,
                legend=go.layout.Legend(
                    x=0,
                    y=1.0
                ),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30)
            )
        ),
        style={'maxHeight': '300px'},
        id='deals-by-sector-fig'
    )

def deals_by_status(agg):
    data = agg["by_status"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().index
    data = data[column_order]

    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Bar(
                    y=data.columns.tolist(),
                    x=d.tolist(),
                    name=fund,
                    orientation='h',
                ) for fund, d in data.iterrows()
            ],
            layout=go.Layout(
                title='Deals by status',
                showlegend=True,
                legend=go.layout.Legend(
                    x=0,
                    y=1.0
                ),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30)
            )
        ),
        style={'maxHeight': '300px'},
        id='deals-by-status-fig'
    )

def deals_by_region(agg):
    data = agg["by_region"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().index
    data = data[column_order]

    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Bar(
                    x=data.columns.tolist(),
                    y=d.tolist(),
                    name=fund,
                ) for fund, d in data.iterrows()
            ],
            layout=go.Layout(
                title='Deals by region',
                showlegend=True,
                legend=go.layout.Legend(
                    x=0,
                    y=1.0
                ),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30)
            )
        ),
        style={'maxHeight': '300px'},
        id='deals-by-region-fig'
    )


def deals_by_deprivation(agg):
    data = agg["by_deprivation"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = sorted(
        data.columns.tolist(),
        key=lambda x: float(x.split(" ")[0])
    )
    data = data[column_order]

    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Bar(
                    x=data.columns.tolist(),
                    y=d.tolist(),
                    name=fund,
                ) for fund, d in data.iterrows()
            ],
            layout=go.Layout(
                title='Deals by deprivation decile',
                showlegend=True,
                legend=go.layout.Legend(
                    x=0,
                    y=1.0
                ),
                xaxis=dict(
                    type='category',
                ),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30)
            )
        ),
        style={'maxHeight': '300px'},
        id='deals-by-deprivation-fig'
    )


def heat_map(deals):

    latlongs = deals.loc[deals['latitude'].apply(
        type) == float, ['latitude', 'longitude']].dropna(how='any')
    lats = latlongs.latitude.tolist()
    longs = latlongs.longitude.tolist()

    if not lats:
        return None

    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Scattermapbox(
                    lat=lats,
                    lon=longs,
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=9
                    ),
                )
            ],
            layout=go.Layout(
                autosize=True,
                hovermode='closest',
                mapbox=go.layout.Mapbox(
                    accesstoken='pk.eyJ1IjoiZGF2aWRrYW5lIiwiYSI6ImNqdm5zb2ZveTB5M280MWxlejdxNHRscW4ifQ.iIc5s6Eq9D7xq9IFT39dlQ',
                    bearing=0,
                    center=go.layout.mapbox.Center(
                        lat=(sum(lats) / len(lats)),
                        lon=(sum(longs) / len(longs))
                    ),
                    pitch=0,
                    zoom=4
                ),
                margin=go.layout.Margin(l=0, r=0, t=0, b=0)
            )
        ),
        style={'maxHeight': '300px'},
        id='heat-map-fig'
    )

