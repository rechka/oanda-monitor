import requests
import configparser
import sys
import ujson

config = configparser.ConfigParser(allow_no_value=True)
config.read("config.ini")
user = config["oanda"]["login"]
password = config["oanda"]["password"]
token = config["oanda"]["token"]
discord_url = config["oanda"]["discord_url"]

data = {
    'api_key': '0325ee6232373738',
    'password': password,
    'username': user
}


to_drop = ['id','guaranteedStopLossOrderMode','alias','createdTime',\
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

to_drop_opt = ['marginCallEnterTime']

to_rename = {'lastTransactionID':'txn#','balance':'bal$','NAV':'NAV$'}           



def send_discord(content):
    r3 = requests.post(url=discord_url, json={"content":content})
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
    stats = {}
    for k in to_rename.keys(): stats[k] = 0.0
    for account in accounts:
        r2 = session.get(f'https://api-fxtrade.oanda.com/v3/accounts/{account}/summary', headers=headers)
        if r2.status_code == 200:
            summary = ujson.loads(r2.text)['account']
            for key in to_drop: del summary[key]
            for k, v in summary.items(): 
                stats[k] += float(v)   
        else:
            sys.exit(f'{r2.status_code}, {r2.text}')

    return inform(stats)

def inform(stats):

    
    wcap = (stats['balance']-stats['NAV'])/stats['balance']

    message = f'{user[:5]} txn#: {stats["lastTransactionID"]:0.0f}, bal$: {stats["balance"]:0.0f}, NAV$: {stats["NAV"]:0.0f}, Wcap: {wcap:0.0%}'
    
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




