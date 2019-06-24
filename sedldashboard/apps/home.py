import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from slugify import slugify

from ..app import app
from ..data import get_groups

groups = get_groups()

def menu_item(group, items):

    def get_url(group, item):
        if not group:
            return '/all'
        return '/{}/{}'.format(slugify(group), slugify(item))

    return html.Div(className='mv3 cf', children=[
        html.Div(className='fl w-third pr3', children=[
            html.H4(className='ma0 pa0 tr', children=group),
        ], style={'minHeight': '1px'}),
        html.Div(className='fl w-two-thirds', children=[
            dcc.Link(
                className='pr3 pb2 dib blue hover',
                children=i,
                href=get_url(group, i)
            ) for i in items
        ]),
    ])

layout = [
    html.Div(className='fl w-75 pr3', children=[
        html.H2(
            className='', children='Explore UK social investment insights from our partners'),
       menu_item('', ["All social investment"]),
    ] + [
        menu_item(group, items) for group, items in groups.items()
    ] + [
        html.Div(className='mt5 bw2 b--blue ba br3 pa2', children=[
            html.H3(className='mt0 mb2 pa0 blue', children=[
                'About this dashboard'
            ]),
            html.P(className='ma0 pa0', children=[
                'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. '
            ]),
        ]),
    ]),
    html.Div(className='fl w-25 pl3', children=[
        html.Div(className='ma2 bw2 b--blue ba br3 pa2', children=[
            html.H3(className='mt0 mb2 pa0 blue', children='Supported by'),
            html.Img(
                src='https://www.powertochange.org.uk/wp-content/themes/power-to-change/assets/svg/power-to-change.svg'),
        ]),
    ]),
]
