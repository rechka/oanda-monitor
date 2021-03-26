import requests
import configparser
from discord_webhook import DiscordWebhook
import pandas as pd
import json

config = configparser.ConfigParser(allow_no_value=True)
config.read("config.ini")
login = config["oanda"]["login"]
password = config["oanda"]["password"]
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

to_rename = {'lastTransactionID':'tx#','balance':'bal$','NAV':'NAV$'}           

data = {
  'api_key': '0325ee6232373738',
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
        #print(r1.status_code, r1.text)

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
df = df.astype(float)
df = df.append(df.sum(numeric_only=True).rename('totals'))

df = df[(df.balance != 0) | (df.NAV != 0)]
df.rename(to_rename,axis=1,inplace=True)

send_discord(config["oanda"]["login"][:5] + " " + ", ".join(f'{column}: {df.loc["totals", column]:0.0f}' for column in df.columns))
