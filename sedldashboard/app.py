import os

import dash
import dash_auth
from flask import Flask

from .commands.data_import import data_cli

server = Flask(__name__)

# set up database
server.config.update(
    IMPORT_FILE=os.environ.get('IMPORT_FILE'), # Google spreadsheet which holds the data that needs to be imported
    FILE_LOCATION=os.environ.get('FILE_LOCATION', 'data'),
    AUTH_USERNAME=os.environ.get('AUTH_USERNAME'),
    AUTH_PASSWORD=os.environ.get('AUTH_PASSWORD'),
)

server.cli.add_command(data_cli)

external_stylesheets = [
    "https://unpkg.com/tachyons/css/tachyons.min.css",
    "https://fonts.googleapis.com/css?family=Questrial",
]

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=external_stylesheets
)
app.title = 'Social Economy Data Lab - Dashboard'
app.config.suppress_callback_exceptions = True
if server.config["AUTH_USERNAME"]:
    auth = dash_auth.BasicAuth(
        app,
        [[server.config['AUTH_USERNAME'], server.config['AUTH_PASSWORD']]]
    )
