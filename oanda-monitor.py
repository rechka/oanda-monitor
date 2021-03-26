import requests
import configparser
from discord_webhook import DiscordWebhook
import pandas as pd
import json

config = configparser.ConfigParser()
config.read("config.ini")
login = config["oanda"]["login"]
password = config["oanda"]["password"]
apikey = config["oanda"]["apikey"]
token = config["oanda"]["token"]
discord_url = config["oanda"]["discord_url"]

to_drop = ['guaranteedStopLossOrderMode','alias','createdTime',\
           'createdByUserID','hedgingEnabled','marginRate',\
           'marginCloseoutPercent','withdrawalLimit',\
           'marginCallMarginUsed','marginCallPercent',\
           'marginCloseoutPositionValue','marginCloseoutNAV',\
           'marginCloseoutMarginUsed','marginCloseoutUnrealizedPL',\
           'positionValue','marginAvailable','openTradeCount',\
           'openPositionCount','pendingOrderCount','marginUsed',\
           'dividendAdjustment','guaranteedExecutionFees',\
           'unrealizedPL','pl','resettablePL','resettablePLTime',\
           'financing','commission','currency']

to_rename = {'currency':'cur','lastTransactionID':'txn'}           

data = {
  'api_key': apikey,
  'api_sig': '',
  'client_type': 'MOBILE',
  'client_version': '5.7.1325',
  'device_type': 'iPad8,11',
  'device_version': 'iPad8,11',
  'operating_system': '14.4',
  'password': password,
  'username': login
}


def send_discord(content):
    webhook = DiscordWebhook(url=config["oanda"]["discord_url"], content=content)
    response = webhook.execute()

stats = []

with requests.Session() as s:
    # Need to add skipping login if token is present and valid (try with @/user first?)
    login = s.post('https://fxtrade-webapi.oanda.com/v1/user/login.json', data=data)
    if login.status_code == 200:
    
        config["oanda"]["token"] = login.json()['session_token']
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        headers = {'Authorization': f'Bearer {config["oanda"]["token"]}'}
        r1 = s.get('https://api-fxtrade.oanda.com/v3/users/@/accounts', headers=headers)
        if r1.status_code == 200:
            message = ''
            accounts = [account['id'] for account in r1.json()['accounts']]# if 'HEDGING' in account['tags']]
            for account in accounts:
                r2 = s.get(f'https://api-fxtrade.oanda.com/v3/accounts/{account}/summary', headers=headers)
                if r2.status_code == 200:
                    summary = r2.json()['account']
                    summary['id'] = summary['id'][-2:]
                    stats.append(summary)

df = pd.DataFrame.from_records(stats,exclude=to_drop,index='id')
df.rename(to_rename,axis=1,inplace=True)
df = df.astype({'balance':'float','NAV':'float','txn':'int'})
df = df.astype({'balance':'int','NAV':'int'})
df = df.append(df.sum(numeric_only=True).rename(u'\u03a3'))

df = df[(df.balance != 0) & (df.NAV != 0)]
send_discord("```"+df.to_markdown(tablefmt="github")+"```")

