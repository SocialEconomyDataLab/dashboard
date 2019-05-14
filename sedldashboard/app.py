import dash

external_stylesheets = [
    "https://unpkg.com/tachyons/css/tachyons.min.css",
    "https://fonts.googleapis.com/css?family=Questrial",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True
