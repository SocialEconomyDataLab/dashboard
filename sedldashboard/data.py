import os
import functools

import pandas as pd
from slugify import slugify

from .app import server

def get_deals():
    return pd.read_pickle(
        os.path.join(server.config['FILE_LOCATION'], 'deals.pkl')
    )


def get_groups():

    deals = get_deals()

    groups = {}

    groups["Region"] = deals["RGN18NM"].dropna(
    ).sort_values().unique().tolist()
    groups["Deprivation"] = sorted(
        deals["imd_decile"].dropna(
        ).unique().tolist(),
        key=lambda x: float(x.split(" ")[0])
    )

    groups["Sector"] = deals["classification"].apply(
        pd.Series).unstack().dropna().sort_values().unique().tolist()
    groups["Status"] = deals["status"].dropna().unique().tolist()
    groups["Year"] = deals.loc[deals["dealDate"].dt.year > 1980, "dealDate"].dt.year.dropna().sort_values().apply(
        "{:.0f}".format).unique().tolist()
    groups["Investment instrument"] = ["Credit", "Grant", "Equity"]
    groups["Partner"] = deals["meta/partner"].dropna().unique().tolist()

    return groups


def get_aggregates(deals):

    deals.loc[:, "deal_year"] = deals.loc[deals["dealDate"].dt.year >
                                          1980, "dealDate"].dt.year
    deals.loc[:, "deal_year_min"] = deals.loc[:, "deal_year"]
    deals.loc[:, "deal_year_max"] = deals.loc[:, "deal_year"]

    aggregates = {
        "deal_count": "sum",
        "deal_value": "sum",
        "recipient_id": "nunique",
        "deal_year_min": "min",
        "deal_year_max": "max",
        "count_with_equity": "sum",
        "equity_count": "sum",
        "equity_value": "sum",
        "count_with_grants": "sum",
        "grants_count": "sum",
        "grants_value": "sum",
        "count_with_credit": "sum",
        "credit_count": "sum",
        "credit_value": "sum",
        "2_or_more_elements": "sum",
    }

    by_class = deals["classification"].apply(pd.Series).unstack(level=0).dropna(
    ).reset_index().join(deals, on='id').set_index(
        ["id", "level_0"]
    ).drop(columns=['classification']).rename(
        columns={0: 'classification'})

    deals.loc[:, "components"] = pd.DataFrame([
        deals.loc[:, "count_with_equity"].replace(1, "Equity"),
        deals.loc[:, "count_with_credit"].replace(1, "Credit"),
        deals.loc[:, "count_with_grants"].replace(1, "Grants")
    ]).T.apply(lambda x: ', '.join([i for i in x if isinstance(i, str)]), axis=1)

    return dict(
        summary = deals.agg(aggregates),
        collections = deals.groupby(
            ["meta/partner"]).agg(aggregates),
        by_year = deals[deals["dealDate"].dt.year > 1980].groupby(
            ["meta/partner", 'deal_year']).agg(aggregates),
        by_classification=by_class.groupby(
            ["meta/partner", 'classification']).agg(aggregates),
        by_region = deals.groupby(
            ["meta/partner", 'RGN18NM']).agg(aggregates),
        by_deprivation = deals.groupby(
            ["meta/partner", 'imd_decile']).agg(aggregates),
        by_status = deals.groupby(
            ["meta/partner", 'status']).agg(aggregates),
        by_instrument = deals.groupby(
            ["meta/partner", 'components']).agg(aggregates),
    )


def get_filtered_df(filters):

    groups = get_groups()
    deals = get_deals()

    for k, v in filters.items():
        if not v:
            continue
        
        if k=="region":
            deals = deals[
                deals["RGN18NM"].fillna('None').apply(slugify).isin(v)
            ]
        elif k=="status":
            deals = deals[
                deals["status"].fillna('None').apply(slugify).isin(v)
            ]
        elif k == "deprivation":
            deals = deals[
                deals["imd_decile"].fillna('None').apply(slugify).isin(v)
            ]
        elif k=="sector":
            class_filter = deals["classification"].apply(
                pd.Series).unstack().dropna().apply(slugify)
            class_filter = class_filter[class_filter.isin(v)]
            deals = deals.loc[class_filter.index.get_level_values(1), :]
        elif k=="partner":
            deals = deals[
                deals["meta/partner"].fillna('None').apply(slugify).isin(v)
            ]
        elif k=="investment-instrument":
            CritList = []
            if "credit" in v:
                CritList.append(deals["credit_count"].gt(0))
            if "grant" in v:
                CritList.append(deals["grant_count"].gt(0))
            if "equity" in v:
                CritList.append(deals["equity_count"].gt(0))
            if CritList:
                AllCrit = functools.reduce(lambda x, y: x | y, CritList)
                deals = deals[AllCrit]

    return deals

def currency(v, currency='GBP', f='{:,.0f}'):
    if not isinstance(v, (int, float)):
        try:
            v = float(v)
        except:
            return v

    if currency == "GBP":
        return "£" + f.format(v)
    if currency == "USD":
        return "$" + f.format(v)
    if currency == "EUR":
        return "$" + f.format(v)
    return currency + f.format(v)
