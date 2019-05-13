import click
from flask import Flask, current_app
from flask.cli import AppGroup
import pandas as pd

from ..db import db

LSOA_LOOKUP = 'https://opendata.arcgis.com/datasets/8c05b84af48f4d25a2be35f1d984b883_0.csv'
LA_LOOKUP = 'https://opendata.arcgis.com/datasets/0c3a9643cc7c4015bb80751aad1d2594_0.csv'

geo_cli = AppGroup('geo')

@geo_cli.command('import_lsoa')
def import_lsoa():
    lsoas = pd.read_csv(LSOA_LOOKUP, index_col='LSOA11CD')
    lsoas = lsoas.join(
        pd.read_csv(LA_LOOKUP, index_col='LAD18CD')[["RGN18CD", "RGN18NM"]],
        on='LAD18CD'
    )
    lsoas.loc[lsoas["LAD18CD"].str.startswith("W"), "RGN18CD"] = "W92000004"
    lsoas.loc[lsoas["LAD18CD"].str.startswith("W"), "RGN18NM"] = "Wales"
    lsoas.loc[lsoas["LAD18CD"].str.startswith("S"), "RGN18CD"] = "S92000003"
    lsoas.loc[lsoas["LAD18CD"].str.startswith("S"), "RGN18NM"] = "Scotland"
    lsoas.loc[lsoas["LAD18CD"].str.startswith("N"), "RGN18CD"] = "N92000002"
    lsoas.loc[lsoas["LAD18CD"].str.startswith("N"), "RGN18NM"] = "Northern Ireland"
    lsoas.to_sql(
        'lsoa_lookup',
        con=current_app.config['SQLALCHEMY_DATABASE_URI'],
        if_exists='replace',
    )
    db.engine.execute(
        'ALTER TABLE "lsoa_lookup" ADD PRIMARY KEY ("LSOA11CD");')

    click.echo('%s LSOAs saved to database' % len(lsoas))
