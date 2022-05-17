import requests
import random
import time
import os

cookie = os.environ['token']
refreshTime = 1 # time sniper waits to refresh selling price
threshold = 1000 # buy price <= to
id = 'item id' # enter id as integer
 
def get_proxies():
  # IMPORTANT, ADD YOUR OWN WEBSHARE KEY HERE!! -> os.environ['APIkey']
  request = requests.get('https://proxy.webshare.io/api/proxy/list/', headers={'Authorization': os.environ['APIkey']})
  results = request.json()['results']
  proxy  = random.choice(results)
  proxies = {
    'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["proxy_address"]}:{proxy["ports"]["http"]}'
  }  
  return [proxies, proxy["proxy_address"]]

def refresh_xcsrf():
  global cookie
  with requests.Session() as session:
    session.cookies['.ROBLOSECURITY'] = cookie
    response = session.post('https://auth.roblox.com/v1/login')
    if "X-CSRF-TOKEN" in response.headers:
      return response.headers["X-CSRF-TOKEN"]

def get_lowest(id: str):
  global cookie, xcsrf, proxies
  request = requests.get(f'https://economy.roblox.com/v1/assets/{id}/resellers', cookies={".ROBLOSECURITY": cookie}, headers={'x-csrf-token': xcsrf}, proxies=proxies[0])
  try:
    return [request.json()['data'][0]['price'], request.json()['data'][0]['seller']['id']]
  except KeyError: 
    xcsrf = refresh_xcsrf()
    proxies = get_proxies()
    time.sleep(1)
    return request.json()['errors'][0]['message']+' '+proxies[1]


if __name__ == '__main__':
  print('>> Bot starting')
  xcsrf = refresh_xcsrf()
  proxies = get_proxies()
  print('>> Finished setting cookies/tokens')
  while True:
    itemPrice = get_lowest(id)
    if not 'TooManyRequests' in itemPrice:
      if int(itemPrice[0]) <= threshold:
        data = {
          "expectedCurrency": 1,
          "expectedPrice": itemPrice[0],
          "expectedSellerId": itemPrice[1]
        }
        s = requests.post(f"https://economy.roblox.com/v1/purchases/products/{id}", 
                      data=data, 
                      cookies={'.ROBLOSECURITY': cookie}, 
                      headers={'x-csrf-token': xcsrf})
        if s.json()['purchased'] is True:
          requests.post(os.environ['webhookurl'], json={'content': f'Caught a snipe for {itemPrice[0]}, id: {id}'})
        else: requests.post(os.environ['webhookurl'], json={'content': f'{id} on sale for {itemPrice[0]}'}) # Unkown error occurred 
      else: time.sleep(refreshTime); print(itemPrice[0])
    else: time.sleep(1); print(itemPrice)
