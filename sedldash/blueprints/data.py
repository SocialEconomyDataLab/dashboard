from flask import Blueprint, render_template
from sqlalchemy.sql import text
import pandas as pd

from ..db import db

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/')
def index():

    deals = pd.read_pickle('deals.pkl')

    aggregates = {
        "deal_count": "sum",
        "deal_value": "sum",
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

    collections = deals.groupby(['collection']).agg(aggregates)
    collections_by_year = deals.groupby(
        ['collection', pd.Grouper(key='deal_date', freq='Y')]).agg(aggregates)
    collections_by_classification = deals.groupby(
        ['collection', 'classification']).agg(aggregates)
    collections_by_region = deals.groupby(
        ['collection', 'region']).agg(aggregates)
    collections_by_status = deals.groupby(
        ['collection', 'deal_status']).agg(aggregates)

    return render_template('data.html.j2',
                           collections=collections,
                           collections_by_year=collections_by_year,
                           collections_by_classification=collections_by_classification,
                           collections_by_region=collections_by_region,
                           collections_by_status=collections_by_status,
                          )



@bp.route('/deal/<dealid>')
def deal(dealid):

    q = text('''select * from "deal" where deal_id = :dealid''')
    deal = db.engine.execute(q, dealid=dealid).fetchone()
    
    return render_template('deal.html.j2', dealid=dealid, deal=dict(deal))


@bp.route('/recipient/<orgid>')
def recipient(orgid):
    d = orgdata(orgid, 'recipient')
    return render_template('organisation.html.j2', **d)


@bp.route('/arrangingorg/<orgid>')
def arrangingorg(orgid):
    d = orgdata(orgid, 'arrangingorg')
    return render_template('organisation.html.j2', **d)


@bp.route('/fundingorg/<orgid>')
def fundingorg(orgid):
    d = orgdata(orgid, 'fundingorg')
    return render_template('organisation.html.j2', **d)


def orgdata(orgid, orgtype='recipient'):
    q = text('''select *
        from organization
        where "org_id" = :orgid''')
    org = db.engine.execute(q, orgid=orgid).fetchone()
    org = dict(org) if org else None

    if orgtype == 'arrangingorg':
        q = text('''select  DISTINCT ON (deal_id) *
            from deal
            where "deal"->'arrangingOrganization'->>'id' = :orgid''')
    elif orgtype == 'fundingorg':
        q = text('''select  DISTINCT ON (deal_id) deal_id,
	"deal" 
from (
	select deal_id,
		"deal",
		json_array_elements(investment)->'fundingOrganization'->>'id' as fundingorgid
	from (
		select "deal_id", 
			"deal",
			row_to_json(json_each(("deal"->'investments')::json))->>'key' as investment_type,
			row_to_json(json_each(("deal"->'investments')::json))->'value' as investment
		from deal
	) as a
	where a.investment_type in ('grants', 'credit', 'equity')
) as b
where fundingorgid = :orgid
group by deal_id, "deal"''')
    else:
        q = text('''select  DISTINCT ON (deal_id) *
            from deal
            where "deal"->'recipientOrganization'->>'id' = :orgid''')
    deals = db.engine.execute(q, orgid=orgid).fetchall()
    deals = [dict(d) for d in deals]

    stats = {
        "count": len(deals),
        "value": sum([d.get("deal", {}).get("value", 0) for d in deals])
    }

    sources = {
        d.get("metadata", {}).get("identifier"): d.get("metadata")
        for d in deals
    }

    if not org and deals:
        if orgtype == "arrangingorg":
            org = {
                "organization": deals[0]["deal"]["arrangingOrganization"],
                "org_id": orgid
            }
        else:
            org = {
                "organization": deals[0]["deal"]["recipientOrganization"],
                "org_id": orgid
            }

    return dict(orgid=orgid, orgtype=orgtype, org=org, deals=deals, stats=stats, sources=sources)

