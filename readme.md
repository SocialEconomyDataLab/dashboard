# Social Economy Data Lab Dashboard

This dashboard is designed to display data published to the 
[Social Economy data specification](http://spec.socialeconomydatalab.org/en/latest/).

The dashboard imports data that meets the standard from Google sheets and displays
it in aggregated form to users. It is not designed to display deal-level data, but
instead provide an overview of the deals, which can be filtered using a number of 
different facets.

## How the app is set up

The app uses [Dash by Plotly](https://dash.plot.ly/), which is built on top of
[flask](http://flask.pocoo.org/) using [python](https://www.python.org/).
It has been developed & tested using python v3.7 - though it may work on other
3.X versions.

The dash app is contained in the `sedldashboard` folder. The app is split into
two parts - the homepage and the summary pages. Which part is loaded depends on the URL.

The file structure is as follows:

- `sedldashboard/app.py` - sets up the Flask server and Dash app. Includes useful
  settings based on environmental variables
- `sedldashboard/data.py` - utility functions for accessing and filtering the data
- `sedldashboard/index.py` - main app layout and router callback
- `sedldashboard/apps/home.py` - layout and callbacks for home page
- `sedldashboard/apps/summary.py` - layout and callbacks for summary dashboard page
- `sedldashboard/assets/style.css` - extra styles
- `sedldashboard/commandsdata.py` - functions for importing data, along with the [click](https://click.palletsprojects.com/en/7.x/) command.

CSS styles are based on the [tachyons CSS framework](http://tachyons.io/) with the
[Questrial font from Google fonts](https://fonts.google.com/specimen/Questrial).

## Data source

The source data is held in a set of Google spreadsheets. One Google sheet
([currently this one](https://docs.google.com/spreadsheets/d/1WVnY5nK7ji5TaVZYcOTexuiekyFLyPfMvFC2kh2Ogp4/edit#gid=0))
contains a table giving the links to the sheets containing the data. The table
looks something like this:

| Partner               | URL |
|-----------------------|-----|
| Community Shares Unit | <https://docs.google.com/spreadsheets/d/1S2x09U8Z9tWBXL9ceUbZ8S_1hO0xOI9pCJwfS4u8xiE/edit?usp=drive_web&ouid=116119705600712178023> |
| Key Fund              | <https://docs.google.com/spreadsheets/d/1VDOKOTfiKcmiUyPF3hRQn8Un0AYvzCBOI_GuX-Uz0Bg/edit#gid=1469958082> |

To be included in the dashboard, a link to the data spreadsheet needs to be added to this
file list sheet, alongside the name of the partner organisation. This partner name should
be how you want the name to be displayed in the dashboard.

### Google authentication

In order for the import script to access the file list and the associated sheets, it needs
to be authenticated with Google. For this to work you need to load a Google authentication
keyfile, in JSON format. This authentication keyfile should be associated with a service 
account that has read access to the file list spreadsheet and all the associated 
spreadsheets.

- [Google cloud documentation gives the process for generating this file](https://cloud.google.com/docs/authentication/production#obtaining_and_providing_service_account_credentials_manually)

Once you have created and downloaded your JSON keyfile, it needs to be uploaded to the
directory where the app will run from. If on a remote server, you could use something
like [scp](http://www.hypexr.org/linux_scp_help.php):

```sh
scp path/to/keyfile.json root@ip-address:/path/to/sedldashboard/data/keyfile.json
```

By default the import script will look for the key at `data/keyfile.json`, although you
can provide a different file name if needed.

### Importing data

Once you've got a keyfile set up, you can import the data. This step is assuming you
already have the app set up and running.

To do this, run the following command:

```sh
flask data import
```

If you have a keyfile in a location other than `data/keyfile.json`, then you can use
the `--keyfile` flag to specify the path.

```sh
flask data import --keyfile path/to/keyfile.json
```

You can also use the additional command flags:

- `--sheet https://docs.google.com/spreadsheets/d/1234567890abcde/edit#gid=0` to set the spreadsheet containing the file list
- `--output /path/to/folder` - folder where the output will be saved 

In the default setup this data import command is only run manually. However, it would be possible to [set up a cron job](https://askubuntu.com/questions/2368/how-do-i-set-up-a-cron-job) to run this command on the data on a nightly basis.

## Setup

How to get a development/live version of the tool up and running. See also the section below
on how to get the server running using [dokku](https://github.com/dokku/dokku).

These instructions assume that you have python 3.7.2 installed.

```sh
# clone the repository
git clone https://github.com/SocialEconomyDataLab/dashboard

# switch to the repository
cd dashboard
```

At this point you'll need to create a `data` folder under `dashboard`, and 
copy the authentication keyfile to it (it's best if this is named `keyfile.json`).

```sh
# start a virtual environment
python -m venv env

# switch to the virtual environment
env\Scripts\active # on windows
source env\bin\activate # on linux/mac

# install the requirements
pip install -r requirements.txt
```

Now you need to setup the environment variables. This can done by
creating a `.env` file in the `dashboard` folder, with the following contents:

```
FLASK_APP=sedldashboard.app:server
FILE_LOCATION=data
IMPORT_FILE=https://docs.google.com/spreadsheets/d/1WVnY5nK7ji5TaVZYcOTexuiekyFLyPfMvFC2kh2Ogp4/edit#gid=0
```

If you want to use basic HTTP authentication (which means that users would need a
password to access the site), then you need to add the following variables to `.env`:

```
AUTH_USERNAME=sedl
AUTH_PASSWORD=[PUT PASSWORD HERE]
```

If you're running the site locally for development purposes you can set the following
variable. This will ensure that the site reloads when changes are made. If it's not set
then the site will run in production mode:

```
FLASK_ENV=development
```

You can also manually set each of the environment variables, using the right method for
your operating system. Note that these might reset every time you use the virtual enviroment.

### Run data import

```
flask data import
```

This should create a file called `data/deals.pkl` as well as individual files for each of the
source spreadsheets.

### Start the app server

Run the command:

```
flask run
```

## Setup (using dokku)

You can also setup the app using [dokku](http://dokku.viewdocs.io/dokku/), which has a similar workflow to Heroku. To deploy using dokku you will usually have a local development version,
and then ssh access to a remote server which already has dokku installed and running.

Deployment is accomplished using `git push` to the remote server, but some processes do
need to be run on the server itself using SSH.

### 1. Create app (on server)

```
dokku apps:create sedldash
```

### 2. Add persistent storage (on server)

[Persistant storage docs](https://github.com/dokku/dokku/blob/master/docs/advanced-usage/persistent-storage.md)

The dokku app itself is not designed to be persistent between deploys, so you
need to create a folder outside app that is available to the app, but won't be deleted 
every time the app is deployed.

```
mkdir -p  /var/lib/dokku/data/storage/sedldash
chown -R dokku:dokku /var/lib/dokku/data/storage/sedldash
chown -R 32767:32767 /var/lib/dokku/data/storage/sedldash
dokku storage:mount sedldash /var/lib/dokku/data/storage/sedldash:/app/storage
```

### 3. Add environmental variables (on server)

```
dokku config:set sedldash FLASK_APP=sedldashboard.app:server
dokku config:set sedldash FILE_LOCATION=/app/storage
dokku config:set sedldash AUTH_USERNAME=sedl AUTH_PASSWORD=[PUT PASSWORD HERE]
dokku config:set sedldash IMPORT_FILE=https://docs.google.com/spreadsheets/d/1WVnY5nK7ji5TaVZYcOTexuiekyFLyPfMvFC2kh2Ogp4/edit#gid=0
```

### 4. Add domain name (on server)

```
dokku domains:enable sedldash
dokku domains:add sedldash sedldash.dkane.net
```

### 5. Add [lets encrypt](https://github.com/dokku/dokku-letsencrypt) https (on server)

```
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
dokku config:set --no-restart --global DOKKU_LETSENCRYPT_EMAIL=your@email.tld
dokku letsencrypt sedldash
```

### 6. Deploy the app (on local machine)

Make sure you replace `123.456.789.012` with the IP address of the remote server.

```
git remote add dokku dokku@123.456.789.012:sedldash
git push dokku master
```

### 7. Copy over google authentication keyfile (on local machine)

Copy the Google authentication keyfile to the server (this allows access to the Google drive files)

```
scp path/to/keyfile.json root@ip-address:/var/lib/dokku/data/storage/sedldash/keyfile.json
```

### 8. Importing deals data (on server)

Run the import command

```
dokku run sedldash flask data import
```

## Other data sources

These data sources are stored in the `external_data/` folder and are used in the
data import process.

### SIC codes

From <https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/ukstandardindustrialclassificationofeconomicactivities/uksic2007/sic2007summaryofstructurtcm6.xls>.

Some 

### LSOA data

- [LSOA to Ward and Local Authority](https://geoportal.statistics.gov.uk/datasets/lower-layer-super-output-area-2011-to-ward-2018-lookup-in-england-and-wales-v3/data)
- [LA to Region](https://geoportal.statistics.gov.uk/datasets/local-authority-district-to-region-december-2018-lookup-in-england)
- [IMD deciles](http://opendatacommunities.org/slice?dataset=http%3A%2F%2Fopendatacommunities.org%2Fdata%2Fsocietal-wellbeing%2Fimd%2Findices&http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fontology%2Fcommunities%2Fsocietal_wellbeing%2Fimd%2Findices=http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fconcept%2Fgeneral-concepts%2Fimd%2Fcombineddeprivation&http%3A%2F%2Fpurl.org%2Flinked-data%2Fcube%23measureType=http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fontology%2Fcommunities%2Fsocietal_wellbeing%2Fimd%2FdecObs) (England only)
