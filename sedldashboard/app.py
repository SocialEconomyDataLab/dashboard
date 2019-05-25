import os

import dash
import dash_auth
from flask import Flask

server = Flask(__name__)

# set up database
server.config.update(
    FILE_LOCATION=os.environ.get('FILE_LOCATION', 'data'),
    AUTH_USERNAME=os.environ.get('AUTH_USERNAME'),
    AUTH_PASSWORD=os.environ.get('AUTH_PASSWORD'),
)

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
