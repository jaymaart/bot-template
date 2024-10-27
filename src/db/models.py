from tortoise import fields
from tortoise.models import Model


class Payment(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    url = fields.CharField(max_length=255)
    image = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)


class Queue(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    user_id = fields.IntField()
    position = fields.IntField()
    product = fields.CharField(max_length=255)

class QueueConfig(Model):
    id = fields.IntField(pk=True)
    channel_id = fields.IntField()
    message_id = fields.IntField()

class Vouch(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    vouch = fields.TextField()
    rating = fields.IntField()
    timestamp = fields.DatetimeField(auto_now_add=True)
