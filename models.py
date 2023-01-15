from tortoise import fields
from tortoise.models import Model


class EventModel(Model):
    id = fields.IntField(pk=True)
    event_id = fields.CharField(16)
    day = fields.IntField()
    month = fields.IntField()
    year = fields.IntField()
    start = fields.CharField(8)
    country = fields.CharField(128)
    tournament = fields.CharField(128)
    tour = fields.CharField(128)
    team_1 = fields.CharField(128)
    team_2 = fields.CharField(128)
    team_1_coefficient = fields.FloatField()
    draw_coefficient = fields.FloatField()
    team_2_coefficient = fields.FloatField()
    team_1_goals = fields.IntField()
    team_2_goals = fields.IntField()
    team_1_voices = fields.IntField()
    draw_voices = fields.IntField()
    team_2_voices = fields.IntField()
    team_1_voices_percent = fields.FloatField()
    draw_voices_percent = fields.FloatField()
    team_2_voices_percent = fields.FloatField()

