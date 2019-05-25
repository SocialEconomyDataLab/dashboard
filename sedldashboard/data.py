import os
import functools

import pandas as pd
from slugify import slugify

from app import server

def get_deals():
    return pd.read_pickle(
        os.path.join(server.config['FILE_LOCATION'], 'deals.pkl')
    )


def get_groups():

    deals = get_deals()

    groups = {}

    groups["Region"] = deals["region"].dropna().unique().tolist()
    groups["Sector"] = deals["classification"].dropna().unique().tolist()
    groups["Status"] = deals["deal_status"].dropna().unique().tolist()
    groups["Year"] = deals["deal_year"].dropna().sort_values().apply(
        "{:.0f}".format).unique().tolist()
    groups["Investment type"] = ["Credit", "Grant", "Equity", "Share Offers"]
    groups["Partner"] = deals["collection"].dropna().unique().tolist()

    return groups


def get_aggregates(deals):

    deals.loc[:, "deal_year_min"] = deals["deal_year"]
    deals.loc[:, "deal_year_max"] = deals["deal_year"]

    aggregates = {
        "deal_count": "sum",
        "deal_value": "sum",
        "recipient_id": "nunique",
        "deal_year_min": "min",
        "deal_year_max": "max",
        "count_with_share_offers": "sum",
        "share_offers": "sum",
        "share_offers_investmentTarget": "sum",
        "count_with_equity": "sum",
        "equity_count": "sum",
        "equity_value": "sum",
        "count_with_grant": "sum",
        "grant_count": "sum",
        "grant_value": "sum",
        "count_with_credit": "sum",
        "credit_count": "sum",
        "credit_value": "sum",
        "2_or_more_elements": "sum",
    }

    return dict(
        summary = deals.agg(aggregates),
        collections = deals.groupby(
            ['collection']).agg(aggregates),
        by_year = deals.groupby(
            ['collection', 'deal_year']).agg(aggregates),
        by_classification = deals.groupby(
            ['collection', 'classification']).agg(aggregates),
        by_region = deals.groupby(
            ['collection', 'region']).agg(aggregates),
        by_status = deals.groupby(
            ['collection', 'deal_status']).agg(aggregates),
    )


def get_filtered_df(filters):

    groups = get_groups()
    deals = get_deals()

    for k, v in filters.items():
        if not v:
            continue
        
        if k=="region":
            deals = deals[
                deals["region"].apply(slugify).isin(v)
            ]
        elif k=="status":
            deals = deals[
                deals["deal_status"].apply(slugify).isin(v)
            ]
        elif k=="sector":
            deals = deals[
                deals["classification"].fillna('None').apply(slugify).isin(v)
            ]
        elif k=="partner":
            deals = deals[
                deals["collection"].fillna('None').apply(slugify).isin(v)
            ]
        elif k=="investment-type":
            CritList = []
            if "credit" in v:
                CritList.append(deals["credit_count"].gt(0))
            if "grant" in v:
                CritList.append(deals["grant_count"].gt(0))
            if "equity" in v:
                CritList.append(deals["equity_count"].gt(0))
            if "share-offers" in v:
                CritList.append(deals["share_offers"].gt(0))
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
