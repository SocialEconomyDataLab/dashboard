import os
import datetime

from flask import Flask

from .db import db
from .blueprints import add_blueprints

def create_app(test_config=None):
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", 'sqlite:////tmp/test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    add_blueprints(app)
    add_template_filters(app)

    return app


def add_template_filters(app):
    # register template filters

    @app.template_filter('todate')
    def template_todate(s, output_format="%Y-%m-%d", input_format="%Y-%m-%dT%H:%M:%S%z"):
        if not s:
            return s
        if not isinstance(s, (datetime.datetime, datetime.date)):
            s = datetime.datetime.strptime(s, input_format)
        return s.strftime(output_format)

    @app.template_filter('currency')
    def template_currency(v, currency='GBP', f='{:,.0f}'):
        if not isinstance(v, (int, float)):
            try:
                v = float(v)
            except:
                return v

        if currency=="GBP":
            return "£" + f.format(v)
        if currency=="USD":
            return "$" + f.format(v)
        if currency=="EUR":
            return "$" + f.format(v)
        return currency + f.format(v)
