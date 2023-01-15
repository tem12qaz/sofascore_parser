import asyncio
import os
from datetime import datetime, timedelta

import xlsxwriter

from empty import Empty
from event import Event
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

    def set_football(self):
        self.request_init = Request.football
        self.sport = 'football'

    @classmethod
    def test(cls):
        return cls(last_day_str='11')

    def set_tennis(self):
        self.request_init = Request.tennis
        self.sport = 'tennis'

    def init_request(self):
        request: Request = self.request_init(self.datetime)
        return request

    def write_day(self, day: list[Event]):
        row_num = 1
        for event in day:
            print(self.log(str(list(event.__dict__.values()))))
            col_num = 0
            for col in tuple(event.__dict__.values()):
                if type(col) == Empty:
                    col = ''
                self.worksheet.write(row_num, col_num, col)
                col_num += 1
            row_num += 1

    async def parse_and_write_day(self, request: Request):
        if not await request.get():
            return
        self.write_day(await request.parse_json())

        self.last_recorded_day = Request.format_date(request.date)
        # print(self.last_recorded_day, ' RECORDED')
        self.days += 1

    def log(self, additional: str = ''):
        os.system('clear')
        print(
            f'''{Colors.OKGREEN}DAYS:{Colors.ENDC} {self.days}
{Colors.OKCYAN}EVENTS:{Colors.ENDC} {self.events}
              
{Colors.WARNING}NO_ODDS:{Colors.ENDC} {self.no_odds}
{Colors.WARNING}NO_VOICES:{Colors.ENDC} {self.no_voices} 
                
{Colors.FAIL}ERRORS:{Colors.ENDC} {self.errors}
{Colors.FAIL}REQUEST_ERRORS:{Colors.ENDC} {self.request_errors}
            
{self.last_recorded_day} RECORDED

LAST RECORDED INFO:    
{additional}
'''
)

    async def parse_loop(self):
        try:
            while self.last_recorded_day > self.last_day_str:
                for i in range(20):
                    request: Request = self.request_init(self, self.datetime)
                    self.loop.create_task(self.parse_and_write_day(request))
                    self.previous_day()
                    # await asyncio.sleep(0.1)

                while len(asyncio.all_tasks(self.loop)) > 1:
                    self.log()
                    await asyncio.sleep(1)
        except Exception:
            self.workbook.close()

    def previous_day(self):
        self.datetime -= timedelta(days=1)

    def run(self):
        self.loop.create_task(self.parse_loop())
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.workbook.close()
            self.loop.close()
            return

    def init_workbook(self):
        self.workbook = xlsxwriter.Workbook(f'{self.sport}.xlsx')
        self.worksheet = self.workbook.add_worksheet("Sheet")


