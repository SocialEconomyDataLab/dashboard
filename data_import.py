import json
import argparse
import io
import os
import hashlib

import gspread  # To access the google configuration sheet and raw data files
import pandas as pd  # To load and change data tables
# To connect to google drive
from oauth2client.service_account import ServiceAccountCredentials
import requests

import requests_cache
requests_cache.install_cache()

# Limits the services that our service account can access
GOOGLE_SCOPE = ['https://spreadsheets.google.com/feeds',
               'https://www.googleapis.com/auth/drive']

def getGoogleSheets(keyfile):
    # Logging into Google Drive and Google Sheets
    googleCredentials = ServiceAccountCredentials. from_json_keyfile_name(
        keyfile, GOOGLE_SCOPE)
    return gspread.authorize(googleCredentials)  # Authorise Google credentials


def loadGoogleSheets(gc, googleSheet, sheetName, columnList=None):
    """
    Loads a dataframe from google sheets document
    columnList restricts the number of columns returned
    rowFilter restricts the rows returned
    sortBy sorts by the specified columns
    """

    df = None
    try:
        spreadsheet = gc.open_by_url(googleSheet)
        sheet = spreadsheet.worksheet(sheetName)
        df = pd.DataFrame(sheet.get_all_records())
        if columnList is not None:
            df = df[columnList]
    except Exception as errorMessage:
        errorMessage = 'Error - loadGSDataFrame:' + str(errorMessage)
        print(errorMessage)
    return df


def processDataframe(df, sedlPartner):
    newdf = pd.DataFrame()
    if df is None:
        return

    # remove first five lines of the data
    df = df.drop(df.index[0:5])

    # remove any blank columns
    if '' in list(df):
        df = df.drop('', axis=1)

    # remove lines with no ID
    df = df[df["id"].notnull() & (df["id"] != '')]

    # Get info for dashboard
    df.loc[:, 'meta/partner'] = sedlPartner
    columnList = [
        'id', # Deal - One per deal
        'status', # Deal - One per deal
        'value', # Deal - One per deal
        'estimatedValue', # Deal - One per deal
        'dealDate', # Deal - One per deal
        'meta/partner', # Deal - One per deal

        # Project
        'projects/0/classification/0/title',  # May be many per deal

        # Recipient
        'recipientOrganization/industryClassifications', # May be one per deal but may contain a list
        'recipientOrganization/id', # Deal - One per deal
        'recipientOrganization/name', # Deal - One per deal
        'recipientOrganization/location/0/postCode', # Deal - One per deal
        'recipientOrganization/location/0/geoCode', # Deal - One per deal
        'recipientOrganization/location/0/latitude', # Deal - One per deal
        'recipientOrganization/location/0/longitude', # Deal - One per deal

        # Arranging organisation
        'arrangingOrganization/id', # Deal - One per deal
        'arrangingOrganization/name',  # Deal - One per deal

        # Credit: May be none or many per deal
        'investments/credit/0/fundingOrganization/id',
        'investments/credit/0/fundingOrganization/name',
        'investments/credit/0/id',
        'investments/credit/0/status',
        'investments/credit/0/currency',
        'investments/credit/0/value',
                  
        # Equity: May be none or many per deal
        'investments/equity/0/fundingOrganization/id',
        'investments/equity/0/fundingOrganization/name',
        'investments/equity/0/id',
        'investments/equity/0/status',
        'investments/equity/0/currency',
        'investments/equity/0/value',

        # Grants: May be none or many per deal
        'investments/grants/0/fundingOrganization/id',
        'investments/grants/0/fundingOrganization/name',
        'investments/grants/0/id',
        'investments/grants/0/status',
        'investments/grants/0/currency',
        'investments/grants/0/amountDisbursed',
        'investments/grants/0/amountCommitted'
    ]
    for columnName in columnList:
        if columnName in list(df):
            newdf[columnName] = df[columnName].replace('', pd.np.NaN)
        else:
            newdf[columnName] = None

    # sort out numbers in value fields
    num_fields = ["value", "estimatedValue",
                  'investments/credit/0/value',
                  'investments/equity/0/value',
                  'investments/grants/0/amountDisbursed',
                  'investments/grants/0/amountCommitted']
    for f in num_fields:
        newdf.loc[:, f] = newdf[f].apply(
            lambda x: float(str(x).replace(',', '')) if x is not None and x != '' else None
        ).astype(float)

    # add a new grants value field
    newdf.loc[:, 'investments/grants/0/value'] = newdf['investments/grants/0/amountDisbursed'].fillna(
        newdf['investments/grants/0/amountCommitted']
    )
    newdf = newdf.drop(columns=[
                       'investments/grants/0/amountDisbursed',
                       'investments/grants/0/amountCommitted'
                       ])

    # sort out dates in a date field
    date_fields = ["dealDate"]
    for f in date_fields:
        newdf.loc[:, f] = pd.to_datetime(newdf[f].apply(
            lambda x: "{}-01".format(x) if isinstance(x, str) and len(x)==7 else x 
        ))

    return newdf

def createDealDataframe(df, siccodes, lsoa):
    # Create deal dataframe by taking one value for each deal ID
    # Take into account status but dont sum the value
    dealdf = df[(df['status'].notnull())].groupby(['id']).last()[[
        'meta/partner', 'status', 'value', 'estimatedValue', 'dealDate',
        'recipientOrganization/id', 'recipientOrganization/name', 
        'recipientOrganization/location/0/postCode',
        'recipientOrganization/location/0/geoCode',
        'recipientOrganization/location/0/latitude',
        'recipientOrganization/location/0/longitude',
        'recipientOrganization/industryClassifications',
        'arrangingOrganization/id', 'arrangingOrganization/name',
    ]]  

    # A live deal must have a value. Set live deals with no value to pipeline
    dealdf.loc[
        (dealdf.status == 'live') & (dealdf.value.isnull()),
        'status'] = 'pipeline'

    # Using the value for estimate value
    dealdf.loc[:, 'estimatedValue'] = dealdf['estimatedValue'].fillna(dealdf['value'])  

    # A closed deal must not have a value. Set closed deals with a value to "unknown"
    dealdf.loc[
        (dealdf.status == 'closed') & (dealdf.value.isnull()),
        ('status', 'value')] = ('unknown', None)

    # A didNotProceed deal must have not have a value.
    dealdf.loc[(dealdf.status == 'didNotProceed') &
            (dealdf.value.notnull()), 'value'] = None

    # add industrial classification
    dealdf.loc[:,
               'recipientOrganization/industryClassifications'
               ] = dealdf['recipientOrganization/industryClassifications'].apply(lambda x: fixSic(x, siccodes))

    # add other classifications
    prjclassdf = df[['id', 'projects/0/classification/0/title']
                    ].drop_duplicates(keep='first').groupby("id")['projects/0/classification/0/title'].apply(list).apply(lambda x: [i for i in x if isinstance(i, str)])
    dealdf = dealdf.join(prjclassdf)

    # merge the classifications
    dealdf.loc[:, "classification"] = dealdf[
        ["recipientOrganization/industryClassifications",
            "projects/0/classification/0/title"]
    ].apply(lambda x: x["recipientOrganization/industryClassifications"] + x["projects/0/classification/0/title"], axis=1)
    dealdf = dealdf.drop(columns=["recipientOrganization/industryClassifications",
                                  "projects/0/classification/0/title"])

    # add counts for credit equity and grants
    elements = ['credit', 'equity', 'grants']
    for i in elements:
        prefix = 'investments/{}/0/'.format(i)
        invdf = df[df[prefix + 'id'].notnull()].groupby(
            ['id', prefix + 'id']
        ).last()[[
            prefix + 'fundingOrganization/id',
            prefix + 'fundingOrganization/name',
            prefix + 'status',
            prefix + 'currency',
            prefix + 'value'
        ]]
        invgb = invdf.reset_index().groupby("id").agg({
            prefix + 'id': 'count',
            prefix + 'value': 'sum'
        }).rename(columns={
            prefix + 'id': '{}_count'.format(i),
            prefix + 'value': '{}_value'.format(i)
        })
        invgb.loc[:, "count_with_{}".format(i)] = 0
        invgb.loc[invgb['{}_count'.format(i)]>0, "count_with_{}".format(i)] = 1
        dealdf = dealdf.join(invgb)

    dealdf.loc[:, "2_or_more_elements"] = dealdf[[
        "count_with_{}".format(i) for i in elements]].fillna(0).sum(axis=1) > 1

    # add geodata from lsoas
    dealdf = dealdf.join(lsoa, on='recipientOrganization/location/0/geoCode')

    return dealdf


def getSicIndex():
    sic = pd.read_csv("sic_corrected.csv", dtype=str).set_index('siccode')
    return sic

# SIC_URL = "https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/ukstandardindustrialclassificationofeconomicactivities/uksic2007/sic2007summaryofstructurtcm6.xls"
# def getSicIndex(url):
#     r = requests.get(url)
#     r.raise_for_status()
#     sic = pd.read_excel(
#         io.BytesIO(r.content),
#         header=1,
#         dtype=str
#     )
#     sic.columns = [
#         "section_code", "section_name",
#         "division_code", "division_name",
#         "group_code", "group_name",
#         "class_code", "class_name",
#         "subclass_code", "subclass_name",
#     ]
#     sic = sic.dropna(how='all')
#     for i in [
#         "section_code", "section_name",
#         "division_code", "division_name",
#         "group_code", "group_name",
#         #     "class_code", "class_name",
#     ]:
#         sic.loc[:, i] = sic[i].ffill()
#     sic = sic[sic.class_code.notnull() | sic.subclass_code.notnull()]
#     for i in ["class_code", "class_name"]:
#         sic.loc[:, i] = sic[i].ffill()
#     sic.loc[:, "siccode"] = sic.subclass_code.str.replace("[^0-9]", "").fillna(
#         sic.class_code.str.replace("[^0-9]", "").apply("{}0".format)
#     )
#     sic = sic.set_index("siccode")
#     return sic

 
def fixSic(siccodes, siccodeslookup):
    if not siccodes or (isinstance(siccodes, float) and pd.np.isnan(siccodes)):
        return []
    siccodes = str(siccodes).split(",")
    to_return = set()
    for s in siccodes:
        s = s.strip()
        if "/" not in s:
            s = s + "/0"
        s = s.replace(".", '').replace("/", "").zfill(5)
        if s in siccodeslookup.index:
            s = siccodeslookup.loc[s, "name"]
            to_return.add(s)
    return list(to_return)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Import data from a google spreadsheet in the SEDL data format')
    parser.add_argument('keyfile', help='Location of JSON keyfile containing credentials to access the spreadsheet')
    parser.add_argument('--sheet',
        default='https://docs.google.com/spreadsheets/d/1WVnY5nK7ji5TaVZYcOTexuiekyFLyPfMvFC2kh2Ogp4/edit#gid=0',
        help='URL of google sheet containing a list of files to include'
    )
    parser.add_argument('--output', default=os.environ.get('FILE_LOCATION',
                                                           'data'), help='Location where the files will be stored')
    parser.add_argument('--partner', help='Name of the SEDL publisher')

    args = parser.parse_args()

    sic = getSicIndex()
    lsoa = pd.read_csv("lsoa.csv", index_col='LSOA11CD',
                       dtype={"imd_decile": str})
    gc = getGoogleSheets(args.keyfile)

    spreadsheet = gc.open_by_url(args.sheet)
    sheet = spreadsheet.get_worksheet(0)
    files = sheet.get_all_records()

    deals = []

    for f in files:
        filename = hashlib.sha256(f['URL'].encode('utf-8')).hexdigest()[0:10]
        df = loadGoogleSheets(gc, f['URL'], 'Deals', columnList=None)
        df = processDataframe(df, f['Partner'])
        df = createDealDataframe(df, sic, lsoa)
        df.to_pickle(os.path.join(args.output, "{}.pkl").format(filename))
        deals.append(df)

    deals = pd.concat(deals)

    deals.loc[:, "deal_count"] = 1
    deals.loc[:, "recipientOrganization/id"] = deals["recipientOrganization/id"].fillna(
        deals["recipientOrganization/name"])
    deals = deals.rename(columns={
        "value": "deal_value",
        "recipientOrganization/id": "recipient_id",
        'recipientOrganization/location/0/latitude': 'latitude',
        'recipientOrganization/location/0/longitude': 'longitude',
    })

    deals.to_pickle(os.path.join(args.output, "deals.pkl"))
