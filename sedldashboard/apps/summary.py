import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from slugify import slugify

from ..app import app
from ..data import get_groups, get_aggregates, get_filtered_df, currency

groups = get_groups()

SEDL_COLOURS = [
    "#0E67AB",
    "#16C3D2",
    "#3689BF",
    "#333333",
]

def layout(url):
    filters = {}
    url = url[1:].split("/")
    if len(url)==2:
        filters[url[0]] = [url[1]]

    return [
        dcc.Store(id='url-filters', data=filters),
        dcc.Store(id='filters-used'),
        html.Div(className='fl w-100 w-25-l mb3', children=[
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
        html.Div(className='fl w-100 w-75-l pl3-l mv2 mv0-l flex flex-wrap', children=[
            html.Div(className='w-100 w-two-thirds-l pr3 mb3', id="data-summary"),
            # html.Div(className='w-50 pr3 mb3', id="word-cloud"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-year"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-sector"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="heat-map"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-status"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-region"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-deprivation"),
            html.Div(className='w-100 w-50-l pr3 mb3', id="deals-by-instrument"),
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
        html.Pre(id='filters-used-pre', className='w-100 fl dn',
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
               Output("deals-by-deprivation", 'children'),
               Output("deals-by-instrument", 'children')],
              [Input("filters-used", 'data')])
def output_charts(filters):
    deals = get_filtered_df(filters)
    agg = get_aggregates(deals)

    funds = deals["meta/partner"].unique().tolist()
    fund_colours = {
        f: SEDL_COLOURS[k % len(funds)]
        for k, f in enumerate(funds)
    }

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
            None,  # deals-by-instrument
        )

    return (
        data_summary(agg, fund_colours),  # data-summary
        None,  # word-cloud
        deals_by_year(agg, fund_colours),  # deals-by-year
        deals_by_sector(agg, fund_colours), # deals-by-sector
        heat_map(deals, fund_colours),  # heat-map
        deals_by_status(agg, fund_colours),  # deals-by-status
        deals_by_region(agg, fund_colours), # deals-by-region
        deals_by_deprivation(agg, fund_colours), # deals-by-deprivation
        deals_by_instrument(agg, fund_colours), # deals-by-instrument
    )


def data_summary(agg, fund_colours):
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
                html.Strong("{:.0f}".format(
                    agg['summary']['count_with_equity'])),
                ' deals involved equity, with ',
                html.Strong(currency(agg['summary']['equity_value'])),
                ' of equity arranged ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['equity_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["equity_value"] else None,
            html.Li(className='', children=[
                html.Strong("{:.0f}".format(
                    agg['summary']['count_with_credit'])),
                ' deals involved credit, worth ',
                html.Strong(currency(agg['summary']['credit_value'])),
                ' of credit ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['credit_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["credit_value"] else None,
            html.Li(className='', children=[
                html.Strong("{:.0f}".format(
                    agg['summary']['count_with_grants'])),
                ' deals involved grants, worth ',
                html.Strong(currency(agg['summary']['grants_value'])),
                ' ',
                '({:,.0%} of total social investment)'.format(
                    agg['summary']['grants_value'] /
                    agg['summary']['deal_value']
                )
            ]) if agg["summary"]["grants_value"] else None,
        ]) if (agg['summary']['deal_value'] > 0) else None,
        html.P(className='mt0 mb0 pa0', children=[
            '*Based on data from ',
        ] + [
            html.Span([
                (", " if k > 0 else None),
                html.Span(i, style={"color": fund_colours.get(i)}, className='b'),
            ])
            for k, i in enumerate(agg['collections'].index)
        ]),
    ]),


def deals_by_year(agg, fund_colours):
    data = agg["by_year"]["deal_count"].unstack()
    return [
        html.H2("Deals per year", className="pa0 ma0 f4"),
        html.P("Based on the effective date for the deal. {:,.0f} deals do not have a date value present.".format(
            agg['summary']['deal_count'] - agg["by_year"]["deal_count"].sum()
        )),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Scatter(
                        x=data.columns.tolist(),
                        y=d.tolist(),
                        name=fund,
                        line=dict(
                            color=fund_colours.get(fund),
                            width=3,
                        ),
                    ) for fund, d in data.iterrows()
                ],
                layout=go.Layout(
                    showlegend=True,
                    legend=go.layout.Legend(
                        orientation='h',
                    ),
                    xaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    font=dict(
                        size=14,
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='deals-by-year-fig'
        ),
    ]


def deals_by_sector(agg, fund_colours):
    data = agg["by_classification"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().tail(10).index
    data = data[column_order]

    return [
        html.H2("By sector", className="pa0 ma0 f4"),
        dcc.Markdown(
            "Based on the sector provided by the data publisher, or on the [SIC code](https://en.wikipedia.org/wiki/Standard_Industrial_Classification) of the deal recipient."),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        y=data.columns.tolist(),
                        x=d.tolist(),
                        name=fund,
                        orientation='h',
                        marker=dict(
                            color=fund_colours.get(fund),
                        ),
                    ) for fund, d in data.iterrows()
                ],
                layout=go.Layout(
                    showlegend=True,
                    legend=go.layout.Legend(
                        orientation='h',
                    ),
                    xaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    font=dict(
                        size=14,
                    ),
                    # margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='deals-by-sector-fig'
        )
    ]


def deals_by_status(agg, fund_colours):
    data = agg["by_status"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().index
    data = data[column_order]

    return [
        html.H2("Deal status", className="pa0 ma0 f4"),
        dcc.Markdown(
            """
            """
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        y=data.T.columns.tolist(),
                        x=d.tolist(),
                        name=fund,
                        orientation='h',
                    ) for fund, d in data.T.iterrows()
                ],
                layout=go.Layout(
                    showlegend=True,
                    legend=go.layout.Legend(
                        orientation='h',
                    ),
                    barmode='stack',
                    xaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    font=dict(
                        size=14,
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='deals-by-status-fig'
        )
    ]


def deals_by_instrument(agg, fund_colours):

    def display_name(labels):
        labels = [l for l in labels if not l.startswith("No ")]
        if not labels:
            return "No equity or credit"
        return " & ".join(labels)

    return [
        html.H2("Investment instruments", className="pa0 ma0 f4"),
        dcc.Markdown(
            """
Shows the combination of investment instruments used in each deal.
            """
        ),
    ] + [
        html.Div([
            html.H3(f, className="pa0 ma0 f5", style={
                "color": fund_colours.get(f)
            }),
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Heatmap(
                            z=[data[c].fillna(0).tolist() for c in data.columns],
                            x=[display_name(i) for i in data.index.tolist()],
                            y=data.columns.tolist(),
                            colorscale=[[0, '#fff'], [1, fund_colours.get(f)]],
                        )
                    ],
                    layout=go.Layout(
                        xaxis=dict(
                            automargin=True,
                            showgrid=False,
                        ),
                        yaxis=dict(
                            automargin=True,
                            showgrid=False,
                        ),
                        font=dict(
                            size=14,
                        ),
                        height=250,
                        margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                    )
                ),
                config=dict(
                    displayModeBar=False,
                ),
                id='deals-by-instrument-fig-{}'.format(f)
            )
        ]) for f, data in agg["by_instrument"].items()
    ]


def deals_by_region(agg, fund_colours):
    data = agg["by_region"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = data.sum().sort_values().index
    data = data[column_order]

    return [
        html.H2("Deal region", className="pa0 ma0 f4"),
        dcc.Markdown(
            """
Based on the registered office of the recipient organisation.
            """
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        x=data.columns.tolist(),
                        y=d.tolist(),
                        name=fund,
                        marker=dict(
                            color=fund_colours.get(fund),
                        ),
                    ) for fund, d in data.iterrows()
                ],
                layout=go.Layout(
                    showlegend=True,
                    xaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    font=dict(
                        size=14,
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='deals-by-region-fig'
        )
    ]


def deals_by_deprivation(agg, fund_colours):
    data = agg["by_deprivation"]["deal_count"].sort_values(
        ascending=False).unstack()
    column_order = sorted(
        data.columns.tolist(),
        key=lambda x: float(x.split(" ")[0])
    )
    data = data[column_order]

    return [
        html.H2("Deprivation decile", className="pa0 ma0 f4"),
        dcc.Markdown(
            """
Uses the rank of the index of multiple deprivation for the 
[Lower Super Output Area (LSOA)](https://www.datadictionary.nhs.uk/data_dictionary/nhs_business_definitions/l/lower_layer_super_output_area_de.asp?shownav=1)
in which the recipient organisation's registered office is based.
Only available for organisations based in England.
            """
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        x=data.columns.tolist(),
                        y=d.tolist(),
                        name=fund,
                        marker=dict(
                            color=fund_colours.get(fund),
                        ),
                    ) for fund, d in data.iterrows()
                ],
                layout=go.Layout(
                    showlegend=True,
                    xaxis=dict(
                        type='category',
                        automargin=True,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        automargin=True,
                        showgrid=False,
                    ),
                    font=dict(
                        size=14,
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='deals-by-deprivation-fig'
        )
    ]


def heat_map(deals, fund_colours):

    latlongs = deals.loc[deals['latitude'].apply(
        type) == float, ['meta/partner', 'latitude', 'longitude']].dropna(how='any')
    lats = latlongs.latitude.tolist()
    longs = latlongs.longitude.tolist()

    if not len(latlongs):
        return None

    return [
        html.H2("Deal location", className="pa0 ma0 f4"),
        dcc.Markdown(
            """
Based on location of the recipient organisation. For some
organisations this may represent their headquarters, rather than
where the activity takes place.
            """
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Scattermapbox(
                        lat=latlongs[latlongs["meta/partner"]
                                    ==f].latitude.tolist(),
                        lon=latlongs[latlongs["meta/partner"]
                                    == f].longitude.tolist(),
                        mode='markers',
                        name=f,
                        marker=go.scattermapbox.Marker(
                            size=9,
                            color=fund_colours.get(f),
                        ),
                        hoverinfo='none',
                    ) for f in latlongs['meta/partner'].unique()
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
                    showlegend=True,
                    legend=go.layout.Legend(
                        orientation='h',
                    ),
                    margin=go.layout.Margin(l=0, r=0, t=0, b=0)
                )
            ),
            config=dict(
                displayModeBar=False,
            ),
            style={'maxHeight': '450px'},
            id='heat-map-fig'
        )
    ]

