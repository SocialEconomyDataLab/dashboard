from .geodata import geo_cli
from .data import data_cli


def add_commands(app):
    app.cli.add_command(geo_cli)
    app.cli.add_command(data_cli)
