import asyncio
import time
from datetime import datetime, timedelta
from pprint import pprint

import aiohttp
import requests




headers = {
    'authority': 'api.sofascore.com',
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"19360fb909"',
    'origin': 'https://www.sofascore.com',
    'referer': 'https://www.sofascore.com/',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36',
}
async def parse():
    date = datetime(year=2023, month=1, day=9)

    while True:
        date_str = date.strftime("%Y-%m-%d")
        print(date_str)
        # response = requests.get(f'', headers=headers)
        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                url=f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}',
                headers=headers
            )
            resp = await resp.json()

        pprint(resp['events'][0])
        input()
        # time.sleep(0.1)
        date = date - timedelta(days=1)

asyncio.new_event_loop().run_until_complete(parse())
