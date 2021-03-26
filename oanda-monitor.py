import requests
import configparser
from discord_webhook import DiscordWebhook
import pandas

config = configparser.ConfigParser()
config.read("config.ini")
login = config["oanda"]["login"]
password = config["oanda"]["password"]
apikey = config["oanda"]["apikey"]
token = config["oanda"]["token"]
discord_url = config["oanda"]["discord_url"]

interest = ['id','alias','currency','balance','NAV','lastTxn']

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

with requests.Session() as s:
    data = {}
    # Need to add skipping login if token is present and valid (try with @/user first?)
    login = s.post('https://fxtrade-webapi.oanda.com/v1/user/login.json', data=data)
    if login.status_code == 200:
        config["oanda"]["token"] = login.json()['session_token']
       #print(config["oanda"]["token"])
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        headers = {'Authorization': f'Bearer {config["oanda"]["token"]}'}
        r1 = s.get('https://api-fxtrade.oanda.com/v3/users/@/accounts', headers=headers)
        if r1.status_code == 200:
            message = ''
            accounts = [account['id'] for account in r1.json()['accounts']]# if 'HEDGING' in account['tags']]
           #print(accounts)
            for account in accounts:
                print(account)
                r2 = s.get(f'https://api-fxtrade.oanda.com/v3/accounts/{account}/summary', headers=headers)
                if r2.status_code == 200:
                    summary = r2.json()
                    print("====",summary)
                    
                    summary['account']['lastTxn'] = summary['lastTransactionID']                    
                    data[summary['account']['id']] = summary['account']
                    print(data)
            #send_discord(message)
            print(data)
