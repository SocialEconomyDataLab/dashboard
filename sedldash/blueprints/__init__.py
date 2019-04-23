from .home import bp as home
from .data import bp as data

def add_blueprints(app):
    app.register_blueprint(home)
    app.register_blueprint(data)
