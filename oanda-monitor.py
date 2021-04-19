import os
from twilio.rest import Client
import requests
import configparser
from discord_webhook import DiscordWebhook
import pandas as pd
import sys

config = configparser.ConfigParser(allow_no_value=True)
config.read("config.ini")
user = config["oanda"]["login"]
password = config["oanda"]["password"]
token = config["oanda"]["token"]
discord_url = config["oanda"]["discord_url"]
account_sid = config["oanda"]["account_sid"]
auth_token = config["oanda"]["auth_token"]
recipient = config["oanda"]["to"]
sender = config["oanda"]["from"]

data = {
    'api_key': '0325ee6232373738',
    'password': password,
    'username': user
}


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
           'financing','commission','currency']#,'lastTransactionID']

to_rename = {'lastTransactionID':'txn#','balance':'bal$','NAV':'NAV$'}           



def send_discord(content):
    webhook = DiscordWebhook(url=config["oanda"]["discord_url"], content=content)
    r3 = webhook.execute()
    if r3.status_code in [200, 204]:
        return True
    else:
        sys.exit(f'{r3.status_code}, {r3.text}')


def get_accounts(session, token):
    accounts = []
    headers = {'Authorization': f'Bearer {token}'}
    r1 = session.get('https://api-fxtrade.oanda.com/v3/users/@/accounts', headers=headers)
    if r1.status_code == 200:
        accounts = [account['id'] for account in r1.json()['accounts']]
        return parse_accounts(session, accounts, headers)
    else:
        return False
        
def login(session, cfg):
    r0 = session.post('https://fxtrade-webapi.oanda.com/v1/user/login.json', data=data)
    if r0.status_code == 200:
        #update token in config
        cfg["oanda"]["token"] = r0.json()['session_token']
        with open('config.ini', 'w') as configfile:
            cfg.write(configfile)
        return True
    else:
        sys.exit(f'{r0.status_code}, {r0.text}')

def parse_accounts(session,accounts,headers):
    stats = []
    for account in accounts:
        r2 = session.get(f'https://api-fxtrade.oanda.com/v3/accounts/{account}/summary', headers=headers)
        if r2.status_code == 200:
            summary = r2.json()['account']
            summary['id'] = summary['id'][-2:]
            stats.append(summary)
        else:
            sys.exit(f'{r2.status_code}, {r2.text}')
    

    return inform(stats)

def send_text(content):

    client = Client(account_sid, auth_token)

    message = client.messages \
      .create(
             from_=f'whatsapp:{sender}',
             body=content,
             to=f'whatsapp:{recipient}')
            

def inform(stats):
    df = pd.DataFrame.from_records(stats,exclude=to_drop,index='id')
    df = df.astype(float)
    df = df.append(df.sum(numeric_only=True).rename('totals'))

    df = df[(df.balance != 0) | (df.NAV != 0)]
    df.rename(to_rename,axis=1,inplace=True)

    txntot = df.loc["totals", "txn#"]
    baltot = df.loc["totals", "bal$"]
    navtot = df.loc["totals", "NAV$"]
    wcap = (baltot-navtot)/baltot

    message = f'{user[:5]} txn#: {txntot:0.0f}, bal$: {baltot:0.0f}, NAV$: {navtot:0.0f}, Wcap: {wcap:0.0%}'
    
    send_text(message)
    return send_discord(message)


def main():
    with requests.Session() as s:
        token = config["oanda"]["token"]

        if get_accounts(s, token):
            sys.exit(0)
        else: 
            if login(s, config):
                config.read("config.ini")
                token = config["oanda"]["token"]
                if get_accounts(s,token):
                    sys.exit(0)

if __name__ == "__main__":
    main()




