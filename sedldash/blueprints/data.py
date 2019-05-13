from flask import Blueprint, render_template
from sqlalchemy.sql import text

from ..db import db

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/')
def index():

    select_statement = '''select {groupby},
	COUNT(*) as deals,
	SUM(deal_value) as deal_value,
	sum(case when share_offers > 0 then 1 else 0 end) as share_offers,
	sum(share_offers_investmentTarget) as share_offers_investmentTarget,
	sum(case when equity_count > 0 then 1 else 0 end) as count_with_equity,
	sum(equity_count) as equity_count,
	sum(equity_value) as equity_value,
	sum(case when grant_count > 0 then 1 else 0 end) as count_with_grant,
	sum(grant_count) as grant_count,
	sum(grant_value) as grant_value,
	sum(case when credit_count > 0 then 1 else 0 end) as count_with_credit,
	sum(credit_count) as credit_count,
	sum(credit_value) as credit_value,
    sum(case when (equity_count + grant_count + credit_count) > 1 then 1 else 0 end) as "2_or_more_elements"
from (
    select distinct on(deal.deal_id) deal.deal_id,
        "deal"->>'status' as deal_status,
        deal.collection,
        trim(classification) as classification,
        "LAD18NM" as "local_authority",
        "RGN18NM" as "region",
        ("deal"->>'value')::float as deal_value,
        extract (year from to_date("deal"->>'dealDate', 'YYYY-MM-DD'))::int as deal_date,
        share_offers,
        share_offers_investmentTarget,
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
                sum((offer->>'investmentTarget')::float) as share_offers_investmentTarget
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
                deal->'recipientOrganization'->'location'->(0)->>'geoCode' as "lsoa"
            from deal
        ) as "lsoa" on "deal".deal_id = "lsoa".deal_id
        left outer join "lsoa_lookup"
            on "lsoa"."lsoa" = "lsoa_lookup"."LSOA11CD"
    where deal.collection != 'key-fund-005'
) as deals
group by {groupby}
order by {groupby}'''
    q = text(select_statement.format(groupby="collection"))
    collections = db.engine.execute(q).fetchall()

    q = text(select_statement.format(groupby="collection, deal_date"))
    collections_by_year = db.engine.execute(q).fetchall()

    q = text(select_statement.format(groupby="collection, classification"))
    collections_by_classification = db.engine.execute(q).fetchall()

    q = text(select_statement.format(groupby="collection, region"))
    collections_by_region = db.engine.execute(q).fetchall()

    return render_template('data.html.j2',
                           collections=collections,
                           collections_by_year=collections_by_year,
                           collections_by_classification=collections_by_classification,
                           collections_by_region=collections_by_region
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

