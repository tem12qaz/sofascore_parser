import asyncio
import traceback
from datetime import datetime
# from typing import Self

import aiohttp

from config import HEADERS
from empty import Empty
from event import Event, EventVoices
from models import EventModel


class Request:
    def __init__(self, parser, info_url: str, odds_url: str, date: datetime):
        self.parser = parser
        self.info_url = info_url
        self.odds_url = odds_url
        self.date = date
        self.info = None
        self.odds = None

    @staticmethod
    def format_date(date: datetime) -> str:
        return date.strftime('%Y-%m-%d')

    @staticmethod
    def get_or_empty(data: dict, *keys: str) -> str | int | float | Empty:
        try:
            for key in keys:
                data = data[key]
        except KeyError:
            return Empty()
        else:
            return data

    @classmethod
    def football(cls, parser, date: datetime):
        return cls(
            parser=parser,
            info_url=f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{cls.format_date(date)}',
            odds_url=f'https://api.sofascore.com/api/v1/sport/football/odds/1/{cls.format_date(date)}',
            date=date
        )

    @classmethod
    def tennis(cls, parser, date: datetime):
        return cls(
            parser=parser,
            info_url=f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{cls.format_date(date)}',
            odds_url=f'https://api.sofascore.com/api/v1/sport/football/odds/1/{cls.format_date(date)}',
            date=date
        )

    async def make_request(self, url: str) -> dict:
        errors = 0
        while True:
            try:
                proxy, proxy_auth = self.parser.get_proxies()
                async with aiohttp.ClientSession() as session:
                    resp = await session.get(
                        url=url,
                        headers=HEADERS,
                        proxy=proxy,
                        proxy_auth=proxy_auth
                    )
                    resp = await resp.json()

            except Exception:
                if errors == 4:
                    self.parser.request_errors += 1
                    raise ConnectionError
                await asyncio.sleep(3)
                # print(traceback.format_exc())
                errors += 1
                continue
            else:
                return resp

    async def get_info(self) -> dict:
        return await self.make_request(self.info_url)

    async def get_odds(self) -> dict:
        return await self.make_request(self.odds_url)

    async def get_voices(self, event_id: int) -> dict:
        return await self.make_request(f'https://api.sofascore.com/api/v1/event/{event_id}/votes')

    async def get(self) -> bool:
        try:
            self.info = await self.get_info()
            self.odds = await self.get_odds()
        except ConnectionError:
            return False
        else:
            return True

    @staticmethod
    def parse_odds(odds: dict, index: int):
        coefficient = odds['choices'][index]['fractionalValue']
        a, b = map(int, coefficient.split('/'))
        return a/b

    async def parse_event(self, data: dict, odds: dict, voices: dict) -> bool:
        try:
            start_timestamp = self.get_or_empty(data, 'startTimestamp')
            date = datetime.fromtimestamp(start_timestamp)
        except (KeyError, ValueError):
            return False
        voices = EventVoices(
            self.get_or_empty(voices, 'vote', 'vote1'),
            self.get_or_empty(voices, 'vote', 'vote2'),
            self.get_or_empty(voices, 'vote', 'voteX')
        ).calculate_voices()
        event = await EventModel.create(
            event_id=str(data['id']),
            day=date.day,
            month=date.month,
            year=date.year,
            start=date.time().strftime('%H:%M'),
            country=self.get_or_empty(data, 'tournament', 'category', 'name'),
            tournament=self.get_or_empty(data, 'tournament', 'name'),
            tour=self.get_or_empty(data, 'roundInfo', 'round'),
            team_1=self.get_or_empty(data, 'homeTeam', 'name'),
            team_2=self.get_or_empty(data, 'awayTeam', 'name'),
            team_1_coefficient=self.parse_odds(odds, 0),
            draw_coefficient=self.parse_odds(odds, 1),
            team_2_coefficient=self.parse_odds(odds, 2),
            team_1_goals=self.get_or_empty(data, 'homeScore', 'current'),
            team_2_goals=self.get_or_empty(data, 'awayScore', 'current'),
            team_1_voices=voices.voice_1,
            draw_voices=voices.voice_x,
            team_2_voices=voices.voice_2,
            team_1_voices_percent=voices.voice_1_percent,
            draw_voices_percent=voices.voice_x_percent,
            team_2_voices_percent=voices.voice_2_percent,
        )
        return True

    async def parse_json(self) -> None:
        # events = []
        for data in self.info['events']:
            try:
                if await EventModel.get_or_none(event_id=str(data['id'])):
                    self.parser.events += 1
                    continue
                odds = self.odds['odds']

                odds = odds.get(str(data['id']))
                if not odds:
                    self.parser.no_odds += 1
                    continue
                voices = await self.get_voices(data['id'])
                if not voices:
                    self.parser.no_voices += 1
                    continue
                event = await self.parse_event(data, odds, voices)
                if event:
                    # events.append(event)
                    self.parser.events += 1
            except Exception:
                self.parser.errors += 1

        # return events
