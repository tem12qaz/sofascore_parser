import asyncio
import traceback
from datetime import datetime
# from typing import Self

import aiohttp

from config import HEADERS
from empty import Empty
from event import Event, EventVoices
from models import EventModel, Tennis


class NoOdds(Exception):
    pass


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
    def football(cls, parser, date: datetime = None, datetime_str: str = ''):
        if date:
            datetime_str = cls.format_date(date)
        obj = cls(
            parser=parser,
            info_url=f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{datetime_str}',
            odds_url=f'https://api.sofascore.com/api/v1/sport/football/odds/1/{datetime_str}',
            date=date
        )
        obj.parse_event = obj.parse_event_football
        return obj

    @classmethod
    def tennis(cls, parser, date: datetime = None, datetime_str: str = ''):
        if date:
            datetime_str = cls.format_date(date)
        obj = cls(
            parser=parser,
            info_url=f'https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/{datetime_str}',
            odds_url=f'https://api.sofascore.com/api/v1/sport/tennis/odds/1/{datetime_str}',
            date=date
        )
        obj.parse_event = obj.parse_event_tennis
        return obj

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

    async def get_sets_times(self, event_id: int) -> dict:
        return await self.make_request(f'https://api.sofascore.com/api/v1/event/{event_id}')

    @staticmethod
    def format_time(timestamp):
        hour_str = ''
        minute_str = ''
        time = datetime.fromtimestamp(timestamp)
        if time.hour:
            hour_str = f'{time.hour - 3}h'

        if time.minute:
            minute_str = f'{time.minute}m'

        return hour_str + ' ' + minute_str

    async def get(self) -> bool:
        try:
            self.info = await self.get_info()
            self.odds = await self.get_odds()
        except ConnectionError:
            return False
        else:
            return True

    @classmethod
    def parse_sets_times(cls, data: dict):
        data = data['event']
        result = {}
        scores = {}
        times = {}
        ranks = {}
        set_score_label = 'team_{team}_set_{set}'
        team_score_key_in_dict = ('homeScore', 'awayScore')
        set_key_in_dict = 'period{set}'
        team_set_break_score_key_in_dict = 'period{set}TieBreak'
        set_break_score_label = 'team_{team}_set_{set}_break'
        set_time_label = 'set_{set}_time'
        full_time = 0

        try:
            team_1_rank = data['homeTeam']['ranking']
        except KeyError:
            pass
        else:
            ranks['team_1_rank'] = team_1_rank

        try:
            team_2_rank = data['awayTeam']['ranking']
        except KeyError:
            pass
        else:
            ranks['team_2_rank'] = team_2_rank

        try:
            status = data['status']['description'] + ' ' + data['status']['type']
        except KeyError:
            pass
        else:
            result['status'] = status

        for set_ in range(1, 6):
            try:
                set_time = data['time'][set_key_in_dict.format(set=set_)]
            except KeyError:
                break
            else:
                times[set_time_label.format(set=set_)] = cls.format_time(set_time)
                full_time += set_time
            for team in (1, 2):
                try:
                    team_set_score = data[team_score_key_in_dict[team-1]][set_key_in_dict.format(set=set_)]
                except KeyError:
                    break
                else:
                    scores[set_score_label.format(team=team, set=set_)] = team_set_score

                try:
                    team_set_score_break = \
                        data[team_score_key_in_dict[team - 1]][team_set_break_score_key_in_dict.format(set=set_)]
                except KeyError:
                    continue
                else:
                    scores[set_break_score_label.format(team=team, set=set_)] = team_set_score_break
        times['time'] = cls.format_time(full_time)
        result.update(scores)
        result.update(ranks)
        result.update(times)
        return result

    @staticmethod
    async def update_coefficients(event: Tennis | EventModel):
        event.team_1_coefficient += 1
        event.team_2_coefficient += 1
        if type(event) == EventModel:
            event.draw_coefficient += 1

        await event.save()

    async def update_tennis(self, event: Tennis):
        data = self.parse_sets_times(await self.get_sets_times(event.event_id))
        print(data)
        # await self.update_coefficients(event)
        await event.update_from_dict(data)
        await event.save()
        print(f'id{event.id} ok')

    @staticmethod
    def parse_odds(odds: dict, index: int):
        try:
            coefficient = odds['choices'][index]['fractionalValue']
            a, b = map(int, coefficient.split('/'))
            return a/b
        except ValueError:
            raise NoOdds

    async def parse_event_tennis(self, data: dict, odds: dict, voices: dict) -> bool:
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
        event = await Tennis.create(
            event_id=str(data['id']),
            day=date.day,
            month=date.month,
            year=date.year,
            start=date.time().strftime('%H:%M'),
            country=self.get_or_empty(data, 'tournament', 'category', 'name'),
            tournament=self.get_or_empty(data, 'tournament', 'name'),
            tour=self.get_or_empty(data, 'roundInfo', 'name'),
            team_1=self.get_or_empty(data, 'homeTeam', 'name'),
            team_2=self.get_or_empty(data, 'awayTeam', 'name'),
            team_1_coefficient=self.parse_odds(odds, 0),
            team_2_coefficient=self.parse_odds(odds, 1),
            team_1_goals=self.get_or_empty(data, 'homeScore', 'current'),
            team_2_goals=self.get_or_empty(data, 'awayScore', 'current'),
            team_1_voices=voices.voice_1,
            team_2_voices=voices.voice_2,
            team_1_voices_percent=voices.voice_1_percent,
            team_2_voices_percent=voices.voice_2_percent,
        )
        return True

    async def parse_event_football(self, data: dict, odds: dict, voices: dict) -> bool:
        try:
            start_timestamp = self.get_or_empty(data, 'startTimestamp')
            date = datetime.fromtimestamp(start_timestamp)
        except (KeyError, ValueError):
            return False
        voices = EventVoices(
            self.get_or_empty(voices, 'vote', 'vote1'),
            self.get_or_empty(voices, 'vote', 'vote2'),
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
            except NoOdds:
                self.parser.no_odds += 1
                continue
            except Exception:
                print(traceback.format_exc())
                self.parser.errors += 1

        # return events
