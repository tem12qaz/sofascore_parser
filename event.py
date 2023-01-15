from dataclasses import dataclass
from typing import Optional

from empty import Empty


@dataclass
class EventVoices:
    voice_1: int
    voice_2: int
    voice_x: int
    voice_1_percent: Optional[float] = None
    voice_2_percent: Optional[float] = None
    voice_x_percent: Optional[float] = None

    def calculate_voices(self):
        all_voices = self.voice_x + self.voice_1 + self.voice_2
        percent = all_voices / 100
        self.voice_x_percent = round(self.voice_x / percent, 2)
        self.voice_1_percent = round(self.voice_1 / percent, 2)
        self.voice_2_percent = round(self.voice_2 / percent, 2)
        return self

@dataclass
class Event:
    day: int
    month: int
    year: int
    start: str | Empty
    country: str | Empty
    tournament: str | Empty
    tour: str | Empty
    team_1: str | Empty
    team_2: str | Empty
    team_1_coefficient: float | Empty
    draw_coefficient: float | Empty
    team_2_coefficient: float | Empty
    team_1_goals: int | Empty
    team_2_goals: int | Empty
    team_1_voices: int | Empty
    draw_voices: int | Empty
    team_2_voices: float | Empty
    team_1_voices_percent: float | Empty
    draw_voices_percent: float | Empty
    team_2_voices_percent: float | Empty
