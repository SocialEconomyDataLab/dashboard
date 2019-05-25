

## Setup (using dokku)

### Create app

```
dokku apps:create sedldash
```

### Add persistent storage for sqlite db

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

Move files to server

```
scp source_data/deals.pkl root@ip-address:/var/lib/dokku/data/storage/sedldash/deals.pkl
```
