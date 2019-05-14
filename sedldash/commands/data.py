import click
from flask import Flask, current_app
from flask.cli import AppGroup
from sqlalchemy.sql import text
import pandas as pd

from ..db import db

data_cli = AppGroup('data')


@data_cli.command('prepare')
def prepare_data():
    '''
    -- simple offers table
    CREATE TABLE public.offers (
        deal_id varchar NOT NULL,
        id varchar NOT NULL,
        offer json NOT NULL,
        CONSTRAINT offers_pk PRIMARY KEY (deal_id,id)
    );

    insert into offers
    select deal_id,
        coalesce("id", md5("offer"::text)) as "id",
        "offer"
    from (
        select deal_id,
            jsonb_array_elements("deal"->'offers')->>'id' as id,
            jsonb_array_elements("deal"->'offers') as "offer"
        from "deal"
    ) as a
    group by deal_id, id, offer;

    -- simple projects table
    CREATE TABLE public.projects (
        deal_id varchar NOT NULL,
        id varchar NOT NULL,
        project json NOT NULL,
        CONSTRAINT projects_pk PRIMARY KEY (deal_id,id)
    );

    insert into projects
    select deal_id,
        coalesce("id", md5("project"::text)) as "id",
        "project"
    from (
        select deal_id,
            jsonb_array_elements("deal"->'projects')->>'id' as id,
            jsonb_array_elements("deal"->'projects') as "project"
        from "deal"
    ) as a
    group by deal_id, id, project;

    -- simple investments table
    CREATE TABLE public.investments (
        deal_id varchar NOT NULL,
        id varchar NOT NULL,
        investment_type varchar NOT NULL,
        investment json NOT NULL,
        CONSTRAINT investments_pk PRIMARY KEY (deal_id,id)
    );

    insert into investments
    select DISTINCT on(coalesce("id", md5("investment"::text || "deal_id")), "deal_id")
        deal_id,
        coalesce("id", md5("investment"::text || "deal_id")) as "id",
        investment_type,
        investment
    from (
        select deal_id,
            json_array_elements(investment)->>'id' as "id",
            investment_type,
            json_array_elements(investment) as "investment"
        from (
            select "deal_id",
                row_to_json(jsonb_each("deal"->'investments'))->>'key' as investment_type,
                row_to_json(jsonb_each("deal"->'investments'))->'value' as investment
            from deal
        ) as investments
        where json_typeof(investment)::text = 'array'
    ) as a;
    '''    


@data_cli.command('generate_df')
def generate_df():

    select_statement = '''
    select distinct on(deal.deal_id) deal.deal_id,
        1 as deal_count,
        "deal"->>'status' as deal_status,
        "deal"->'recipientOrganization'->>'id' as recipient_id,
        deal.collection,
        trim(classification) as classification,
        "LAD18NM" as "local_authority",
        "RGN18NM" as "region",
        "latitude",
        "longitude",
        ("deal"->>'value')::float as deal_value,
        to_date("deal"->>'dealDate', 'YYYY-MM-DD') as deal_date,
        share_offers,
        "share_offers_investmentTarget",
        equity_count,
        equity_value,
        grant_count,
        grant_value,
        credit_count,
        credit_value
    from "deal"
        left outer join (
            select deal_id,
                count(*) as share_offers,
                sum((offer->>'investmentTarget')::float) as "share_offers_investmentTarget"
            from offers
            group by deal_id
        ) as "offers" on "deal".deal_id = "offers".deal_id
		left outer join (
			select distinct on(deal_id) deal_id,
				json_array_elements(project->'classification')->>'title' as classification
			from projects
		) as "projects" on "deal".deal_id = "projects".deal_id
        left outer join (
            select deal_id,
                count(*) as equity_count,
                sum((investment->>'value')::float) as equity_value
            from investments
            where investment_type = 'equity'
            group by deal_id
        ) as "equity" on "deal".deal_id = "equity".deal_id
        left outer join (
            select deal_id,
                count(*) as grant_count,
                sum(coalesce((investment->>'amountCommitted')::float, (investment->>'amountDisbursed')::float)) as grant_value
            from investments
            where investment_type = 'grants'
            group by deal_id
        ) as "grants" on "deal".deal_id = "grants".deal_id
        left outer join (
            select deal_id,
                count(*) as credit_count,
                sum((investment->>'value')::float) as credit_value
            from investments
            where investment_type = 'credit'
            group by deal_id
        ) as "credit" on "deal".deal_id = "credit".deal_id
        left outer join (
            select distinct on(deal_id) deal_id, 
                deal->'recipientOrganization'->'location'->(0)->>'geoCode' as "lsoa", 
                deal->'recipientOrganization'->'location'->(0)->>'latitude' as "latitude", 
                deal->'recipientOrganization'->'location'->(0)->>'longitude' as "longitude"
            from deal
        ) as "lsoa" on "deal".deal_id = "lsoa".deal_id
        left outer join "lsoa_lookup"
            on "lsoa"."lsoa" = "lsoa_lookup"."LSOA11CD"
    where deal.collection != 'key-fund-005'
    '''

    q = text(select_statement)
    deals = pd.read_sql(q, con=db.engine, index_col='deal_id')

    click.echo('%s rows extracted from database' % len(deals))

    # turn region into categories
    regions = pd.api.types.CategoricalDtype(categories=[
        "East Midlands",
        "East of England",
        "London",
        "North East",
        "North West",
        "South East",
        "South West",
        "West Midlands",
        "Yorkshire and The Humber",
        "Wales",
    ], ordered=True)
    deals.loc[:, "region"] = deals["region"].astype(regions)

    # turn status into categories
    statuses = pd.api.types.CategoricalDtype(categories=[
        "live",
        "closed",
        "didNotProceed",
        "pipeline",
    ], ordered=True)
    deals.loc[:, "deal_status"] = deals["deal_status"].astype(statuses)
    deals["deal_status"].cat.rename_categories({
        "live": "Live",
        "closed": "Closed",
        "didNotProceed": "Did not proceed",
        "pipeline": "In pipeline",
    }, inplace=True)

    # sort out date field
    deals.loc[:, "deal_date"] = pd.to_datetime(deals["deal_date"])
    deals.loc[:, "deal_year"] = deals["deal_date"].dt.year

    # add counts for aggregates
    deals.loc[:, "count_with_share_offers"] = deals["share_offers"] > 0
    deals.loc[:, "count_with_equity"] = deals["equity_count"] > 0
    deals.loc[:, "count_with_grant"] = deals["grant_count"] > 0
    deals.loc[:, "count_with_credit"] = deals["credit_count"] > 0
    deals.loc[:, "2_or_more_elements"] = deals[[
        "count_with_equity", "count_with_grant", "count_with_credit"]].sum(axis=1) > 1

    deals.to_pickle('deals.pkl')

    click.echo('%s rows saved to disk' % len(deals))
