import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from app import app
from apps import home, summary


app.layout = html.Div(className='w-100 sans-serif', children=[
    dcc.Location(id='url', refresh=False),
    html.Header(className='w-100 pa3 ph5-ns bg-white cf', children=[
        html.H1(
            className='questrial',
            children=dcc.Link(
                'Social Economy Data Lab - Dashboard',
                href='/',
                className='black no-underline'
            )
        ),
        html.Hr(),
        html.P(children='The Social Economy Data Lab supports the use of data to create better conditions for social investment in the UK'),
    ]),
    html.Main(id='page-content', className='w-100 pa3 ph5-ns bg-white cf'),
    html.Footer(className='w-100 pa3 ph5-ns bg-white cf', children=[
        html.Hr(),
        html.P('Footer text and copyright'),
    ])
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        raise PreventUpdate
    if pathname == '/':
        return home.layout
    else:
        return summary.layout(pathname)


if __name__ == '__main__':
    app.run_server(debug=True)
