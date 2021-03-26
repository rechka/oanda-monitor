
# Oanda-Monitor

## Introduction

* Small script to check Oanda balances & NAVs of hedging accounts and report to Discord
* Intended to be run regularly via cron
* Login / password / discord webhook are git secret hidden

## How to Use

* clone the repo
* make virtualenv
* install requirements
* edit config.ini
> python3 oanda-monitor.py

## Installation and Configuration

* clone the repo
```
cd ~
git clone https://github.com/rechka/oanda-monitor <cloned repo>
cd <cloned repo>
python3 -m venv .env
. .env/bin/activate
pip3 install -r requirements.txt
```
* edit `config.ini.example` and rename it to `config.ini`, following the syntax:
```
[oanda]
login = <email>
password = <password>
discord_url = https://<discord webhook url>
token = ; leave empty for now
```

* add to crontab (use `crontab -u <username> -e`)

```0 * * * * cd /home/<username>/<cloned repo> && /home/<username>/<cloned repo>/<virtualenv>/bin/python3 home/<username>/<cloned repo>/oanda-monitor.py >> home/<username>/oanda.log 2>&1```

## Further plans
* Add multiple personas support
* Async the monitor
* Add telegram informer

## Supporting
Express your thanks in donations:
BTC: 33yxi4U5qYrXHUE1DHFoQchGTecZJ4hA3W
ETH: 0x5f6Ee50bE65e143776ff6efB23bFedDF5c37b0B9
