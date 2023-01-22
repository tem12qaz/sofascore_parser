import asyncio
import os
import traceback
from datetime import datetime, timedelta
from typing import Callable, Coroutine

import aiohttp
import xlsxwriter
from tortoise.exceptions import DoesNotExist

from db import db_init
from empty import Empty
from event import Event
from models import EventModel, Tennis
from request import Request


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Parser:
    def __init__(self, last_day_str: str = '2015-06-01'):
        self.datetime = datetime.now()
        self.request_init = None
        self.sport = None
        self.last_day_str = last_day_str
        self.last_recorded_day = Request.format_date(self.datetime)
        self.workbook = None
        self.worksheet = None
        self.loop = asyncio.new_event_loop()
        self.errors = 0
        self.events = 0
        self.request_errors = 0
        self.no_odds = 0
        self.no_voices = 0
        self.days = 0
        self.event_id = 0
        self.model = None

        self.proxies = [
            ("168.196.237.191", "9800", "bBDYwg", "5RCpe2"),
            ("168.196.239.186", "9195", "bBDYwg", "5RCpe2"),
            ("168.196.238.70", "9970", "bBDYwg", "5RCpe2"),
        ]

    def get_proxies(self) -> tuple[str, aiohttp.BasicAuth]:
        proxy_tuple = self.proxies[0]
        proxy = f'http://{proxy_tuple[0]}:{proxy_tuple[1]}'
        proxy_auth = aiohttp.BasicAuth(proxy_tuple[2], proxy_tuple[3])
        self.shift_proxy()
        return proxy, proxy_auth

    def shift_proxy(self):
        proxy = self.proxies.pop(0)
        self.proxies.append(proxy)

    def set_football(self):
        self.request_init = Request.football
        self.sport = 'football'
        self.model = EventModel


    def set_tennis(self):
        self.request_init = Request.tennis
        self.sport = 'tennis'
        self.model = Tennis

    def init_request(self):
        request: Request = self.request_init(self.datetime)
        return request

    async def update_info_tennis(self):
        while True:
            self.event_id += 1
            try:
                event = await self.model.get(id=self.event_id)
            except DoesNotExist:
                print(f'{self.event_id} not_exist')
                if self.event_id > 65800:
                    break
                self.event_id += 1
                continue
            request: Request = self.request_init(self)
            self.loop.create_task(request.update_tennis(event))

            while len(asyncio.all_tasks(self.loop)) > 30:
                await asyncio.sleep(0.2)

    async def write(self):
        row_num = 1
        while True:
            try:
                event = await self.model.get(id=self.event_id)
            except DoesNotExist:
                print(f'{self.event_id} not_exist')
                if self.event_id > 65800:
                    break
                self.event_id += 1
                continue
            col_num = 0
            if self.sport == 'tennis':
                row = (event.day, event.month, event.year, event.start, event.country,
                       event.tournament, event.tour, event.team_1, event.team_2,
                       event.team_1_coefficient,
                       event.team_2_coefficient, event.team_1_goals, event.team_2_goals,
                       event.team_1_voices, event.team_2_voices,
                       event.team_1_voices_percent,
                       event.team_2_voices_percent)
            elif self.sport == 'football':
                row = (event.day, event.month, event.year, event.start, event.country,
                       event.tournament, event.tour, event.team_1, event.team_2,
                       event.team_1_coefficient, event.draw_coefficient,
                       event.team_2_coefficient, event.team_1_goals, event.team_2_goals,
                       event.team_1_voices, event.draw_voices, event.team_2_voices,
                       event.team_1_voices_percent, event.draw_voices_percent,
                       event.team_2_voices_percent)
            else:
                raise ValueError('only tennis or football')
            for col in row:
                self.worksheet.write(row_num, col_num, col)
                col_num += 1
            row_num += 1
            print(self.event_id)
            self.event_id += 1

        self.workbook.close()
        self.loop.close()

    async def refresh_coefficients(self, last_id: int = 400):
        for i in range(1, last_id):
            try:
                event = await Tennis.get(id=i)
            except DoesNotExist:
                continue
            request: Request = self.request_init(datetime_str=f'{event.year}-{event.month}-{event.day}')
            odds = await request.get_odds()
            event.team_1_coefficient = request.parse_odds(odds, 0)
            event.team_2_coefficient = request.parse_odds(odds, 1)
            await event.save()
            print(i, event.team_1_coefficient, event.team_2_coefficient)



    async def parse_and_write_day(self, request: Request):
        if not await request.get():
            return
        await request.parse_json()
        self.last_recorded_day = Request.format_date(request.date)
        # print(self.last_recorded_day, ' RECORDED')
        self.days += 1

    async def log(self):
        os.system('clear')
        print(
            f'''{Colors.OKGREEN}DAYS:{Colors.ENDC} {self.days}
{Colors.OKCYAN}EVENTS:{Colors.ENDC} {self.events}
{Colors.OKCYAN}EVENTS IN BASE:{Colors.ENDC} {await self.model.all().count()}
              
{Colors.WARNING}NO_ODDS:{Colors.ENDC} {self.no_odds}
{Colors.WARNING}NO_VOICES:{Colors.ENDC} {self.no_voices} 
                
{Colors.FAIL}ERRORS:{Colors.ENDC} {self.errors}
{Colors.FAIL}REQUEST_ERRORS:{Colors.ENDC} {self.request_errors}
            
{self.last_recorded_day} RECORDED
'''
)

    async def parse_loop(self):
        try:
            while self.last_recorded_day > self.last_day_str:
                for i in range(15):
                    # print('---')
                    request: Request = self.request_init(self, self.datetime)
                    self.loop.create_task(self.parse_and_write_day(request))
                    self.previous_day()
                    # await asyncio.sleep(0.1)

                while len(asyncio.all_tasks(self.loop)) > 1:
                    await self.log()
                    await asyncio.sleep(1)
        except Exception:
            print(traceback.format_exc())
            self.workbook.close()

    def previous_day(self):
        self.datetime -= timedelta(days=1)

    def run_main(self):
        self.loop.create_task(db_init())
        self.loop.create_task(self.parse_loop())
        try:
            print('RUN')
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.workbook.close()
            self.loop.close()
            return

    def init_workbook(self):
        self.workbook = xlsxwriter.Workbook(f'{self.sport}.xlsx')
        self.worksheet = self.workbook.add_worksheet("Sheet")

    def run_write(self):
        self.loop.create_task(db_init())
        self.loop.create_task(self.write())
        self.loop.run_forever()
        return

    def run_update_tennis(self):
        self.loop.create_task(db_init())
        self.loop.create_task(self.update_info_tennis())
        self.loop.run_forever()

    def run(self, task: Coroutine):
        self.init_workbook()
        self.loop.create_task(db_init())
        self.loop.create_task(task)
        self.loop.run_forever()






