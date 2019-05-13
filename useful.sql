


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



-- the following should transform deal json objects into the proper format
-- however because the data doesn't follow the standard they don't work

-- turn deal objects into a more useful format
insert into deal_main
select deal_id as id,
    coalesce("deal"->>'title', deal_id) as title,
    "deal"->>'status' as status,
    to_date("deal"->>'dealDate', 'YYYY-MM-DD') as "dealDate",
    "deal"->>'currency' as currency,
    ("deal"->>'estimatedValue')::float as "estimatedValue",
    ("deal"->>'value')::float as "value",
    "deal"->'investments'->>'summary' as "investments.summary",
    "deal"->'recipientOrganization' as "recipientOrganization",
    "deal"->'arrangingOrganization' as "arrangingOrganization",
    to_date("deal"->>'dateModified', 'YYYY-MM-DD') as "dateModified",
    "deal"->>'dataSource' as "dataSource"
from "deal"
where "collection" != 'key-fund-005'
ON CONFLICT (id)
DO NOTHING;

-- turn offer objects into a more useful format
insert into offers
select deal_id,
	jsonb_array_elements("deal"->'offers')->>'id' as id,
	jsonb_array_elements("deal"->'offers')->>'type' as "type",
	jsonb_array_elements("deal"->'offers')->>'url' as url,
	jsonb_array_elements("deal"->'offers')->>'offerDocumentUrl' as "offerDocumentUrl",
	to_date(jsonb_array_elements("deal"->'offers')->>'startDate', 'YYYY-MM-DD') as "startDate",
	jsonb_array_elements("deal"->'offers')->>'endDate' as "endDate",
	jsonb_array_elements("deal"->'offers')->>'extensionDate' as "extensionDate",
	(jsonb_array_elements("deal"->'offers')->>'minimumInvestmentTarget')::float as "minimumInvestmentTarget",
	(jsonb_array_elements("deal"->'offers')->>'investmentTarget')::float as "investmentTarget",
	(jsonb_array_elements("deal"->'offers')->>'maximumInvestmentTarget')::float as "maximumInvestmentTarget",
	(jsonb_array_elements("deal"->'offers')->>'minimumIndividualInvestment')::float as "minimumIndividualInvestment",
	(jsonb_array_elements("deal"->'offers')->>'maximumIndividualInvestment')::float as "maximumIndividualInvestment",
	jsonb_array_elements("deal"->'offers')->>'investmentFeatures' as "investmentFeatures",
	jsonb_array_elements("deal"->'offers')->'interestRates' as "interestRates",
	jsonb_array_elements("deal"->'offers')->'matchFunding' as "matchFunding",
	jsonb_array_elements("deal"->'offers')->'withdrawals' as "withdrawals",
	jsonb_array_elements("deal"->'offers')->'taxReliefs' as "taxReliefs",
	jsonb_array_elements("deal"->'offers')->'csuStandardMark' as "csuStandardMark",
	jsonb_array_elements("deal"->'offers')->'crowdfunding' as "crowdfunding"
from "deal";

-- turn project objects into a more useful format
select deal_id,
	jsonb_array_elements("deal"->'projects')->>'id' as id,
	jsonb_array_elements("deal"->'projects')->>'title' as "title",
	jsonb_array_elements("deal"->'projects')->>'description' as "description",
	jsonb_array_elements("deal"->'projects')->>'status' as status,
	to_date(jsonb_array_elements("deal"->'projects')->>'startDate', 'YYYY-MM-DD') as "startDate",
	to_date(jsonb_array_elements("deal"->'projects')->>'endDate', 'YYYY-MM-DD') as "endDate",
	to_date(jsonb_array_elements("deal"->'projects')->>'editionDate', 'YYYY-MM-DD') as "editionDate",
	(jsonb_array_elements("deal"->'projects')->>'estimatedValue')::float as "estimatedValue",
	(jsonb_array_elements("deal"->'projects')->>'raisedValue')::float as "raisedValue",
	(jsonb_array_elements("deal"->'projects')->>'achieved')::bool as "achieved",
	jsonb_array_elements("deal"->'projects')->'classification' as "classification",
	jsonb_array_elements("deal"->'projects')->>'purposeOfFinance' as "purposeOfFinance",
	jsonb_array_elements("deal"->'projects')->'assets' as "assets",
	jsonb_array_elements("deal"->'projects')->'locations' as "locations",
	jsonb_array_elements("deal"->'projects')->'notes' as "notes"
from "deal";

-- turn investment credit objects into rows
select deal_id,
	json_array_elements(investment)->>'id' as "id",
	json_array_elements(investment)->>'status' as "status",
	json_array_elements(investment)->>'purpose' as "purpose",
	json_array_elements(investment)->>'description' as "description",
	json_array_elements(investment)->>'currency' as "currency",
	(json_array_elements(investment)->>'estimatedValue')::float as "estimatedValue",
	to_date(json_array_elements(investment)->>'dateOffered', 'YYYY-MM-DD') as "dateOffered",
	to_date(json_array_elements(investment)->>'dateAgreed', 'YYYY-MM-DD') as "dateAgreed",
	(json_array_elements(investment)->>'value')::float as "value",
	(json_array_elements(investment)->>'durationInMonths')::float as "durationInMonths",
	(json_array_elements(investment)->>'initialRepaymentHoliday')::float as "initialRepaymentHoliday",
	json_array_elements(investment)->'interestRate' as "interestRate",
	(json_array_elements(investment)->>'interestPayable')::float as "interestPayable",
	json_array_elements(investment)->'fundingOrganization' as "fundingOrganization",
	json_array_elements(investment)->>'notes' as "notes"
from (
	select "deal_id",
		row_to_json(jsonb_each("deal"->'investments'))->>'key' as investment_type,
		row_to_json(jsonb_each("deal"->'investments'))->'value' as investment
	from deal
) as investments
where json_typeof(investment)::text = 'array'
	and investment_type = 'credit';

-- turn investment equity objects into rows
select deal_id,
	json_array_elements(investment)->>'id' as "id",
	json_array_elements(investment)->>'status' as "status",
	json_array_elements(investment)->>'purpose' as "purpose",
	json_array_elements(investment)->>'description' as "description",
	json_array_elements(investment)->>'type' as "type",
	json_array_elements(investment)->>'platform' as "platform",
	(json_array_elements(investment)->>'numberOfInvestors')::int as "numberOfInvestors",
	json_array_elements(investment)->>'currency' as "currency",
	json_array_elements(investment)->>'estimatedValue' as "estimatedValue",
	to_date(json_array_elements(investment)->>'dateOffered', 'YYYY-MM-DD') as "dateOffered",
	to_date(json_array_elements(investment)->>'dateAgreed', 'YYYY-MM-DD') as "dateAgreed",
	(json_array_elements(investment)->>'value')::float as "value",
	json_array_elements(investment)->>'shareClass' as "shareClass",
	(json_array_elements(investment)->>'shareCapitalIssued')::float as "shareCapitalIssued",
	json_array_elements(investment)->>'shareRights' as "shareRights",
	json_array_elements(investment)->'taxReliefs' as "taxReliefs",
	json_array_elements(investment)->'fundingOrganizations' as "fundingOrganizations",
	json_array_elements(investment)->'fund' as "fund",
	(json_array_elements(investment)->>'isMatchFunding')='True' as "isMatchFunding",
	json_array_elements(investment)->>'notes' as "notes"
from (
	select "deal_id",
		row_to_json(jsonb_each("deal"->'investments'))->>'key' as investment_type,
		row_to_json(jsonb_each("deal"->'investments'))->'value' as investment
	from deal
) as investments
where json_typeof(investment)::text = 'array'
	and investment_type = 'equity';

-- turn investment grant objects into rows
select deal_id,
	json_array_elements(investment)->>'id' as "id",
	json_array_elements(investment)->>'status' as "status",
	json_array_elements(investment)->>'purpose' as "purpose",
	json_array_elements(investment)->>'description' as "description",
	to_date(json_array_elements(investment)->>'dateOffered', 'YYYY-MM-DD') as "dateOffered",
	to_date(json_array_elements(investment)->>'dateAgreed', 'YYYY-MM-DD') as "dateAgreed",
	(json_array_elements(investment)->>'amountRequested')::float as "amountRequested",
	(json_array_elements(investment)->>'amountCommitted')::float as "amountCommitted",
	(json_array_elements(investment)->>'amountDisbursed')::float as "amountDisbursed",
	json_array_elements(investment)->'fundingOrganization' as "fundingOrganization",
	(json_array_elements(investment)->>'isMatchFunding')='True' as "isMatchFunding",
	json_array_elements(investment)->>'notes' as "notes"
from (
	select "deal_id",
		row_to_json(jsonb_each("deal"->'investments'))->>'key' as investment_type,
		row_to_json(jsonb_each("deal"->'investments'))->'value' as investment
	from deal
) as investments
where json_typeof(investment)::text = 'array'
	and investment_type = 'grants';