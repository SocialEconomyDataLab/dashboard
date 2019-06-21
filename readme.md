

## Setup (using dokku)

### Create app

```
dokku apps:create sedldash
```

### Add persistent storage

[Persistant storage docs](https://github.com/dokku/dokku/blob/master/docs/advanced-usage/persistent-storage.md)

```
mkdir -p  /var/lib/dokku/data/storage/sedldash
chown -R dokku:dokku /var/lib/dokku/data/storage/sedldash
chown -R 32767:32767 /var/lib/dokku/data/storage/sedldash
dokku storage:mount sedldash /var/lib/dokku/data/storage/sedldash:/app/storage
```

### Add environmental variables

```
dokku config:set sedldash FLASK_APP=sedldashboard.app:server
dokku config:set sedldash FILE_LOCATION=/app/storage
dokku config:set sedldash AUTH_USERNAME=sedl AUTH_PASSWORD=[PUT PASSWORD HERE]
dokku config:set sedldash IMPORT_FILE=https://docs.google.com/spreadsheets/d/1WVnY5nK7ji5TaVZYcOTexuiekyFLyPfMvFC2kh2Ogp4/edit#gid=0
```

### Add domain name

```
dokku domains:enable sedldash
dokku domains:add sedldash sedldash.dkane.net
```

### Add [lets encrypt](https://github.com/dokku/dokku-letsencrypt) https

```
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
dokku config:set --no-restart --global DOKKU_LETSENCRYPT_EMAIL=your@email.tld
dokku letsencrypt sedldash
```

### Importing deals data

Copy the Google authentication keyfile to the server (this allows access to the Google drive files)

```
scp path/to/keyfile.json root@ip-address:/var/lib/dokku/data/storage/sedldash/keyfile.json
```

Run the import command

```
dokku run flask data import
```

## Other data sources

### SIC codes

From <https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/ukstandardindustrialclassificationofeconomicactivities/uksic2007/sic2007summaryofstructurtcm6.xls>.

### LSOA data

- [LSOA to Ward and Local Authority](https://geoportal.statistics.gov.uk/datasets/lower-layer-super-output-area-2011-to-ward-2018-lookup-in-england-and-wales-v3/data)
- [LA to Region](https://geoportal.statistics.gov.uk/datasets/local-authority-district-to-region-december-2018-lookup-in-england)
- [IMD deciles](http://opendatacommunities.org/slice?dataset=http%3A%2F%2Fopendatacommunities.org%2Fdata%2Fsocietal-wellbeing%2Fimd%2Findices&http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fontology%2Fcommunities%2Fsocietal_wellbeing%2Fimd%2Findices=http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fconcept%2Fgeneral-concepts%2Fimd%2Fcombineddeprivation&http%3A%2F%2Fpurl.org%2Flinked-data%2Fcube%23measureType=http%3A%2F%2Fopendatacommunities.org%2Fdef%2Fontology%2Fcommunities%2Fsocietal_wellbeing%2Fimd%2FdecObs) (England only)
