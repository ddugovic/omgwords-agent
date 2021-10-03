import factory

from omgwords-agent.models import *


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

class DiscordUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DiscordUser
    discord_id = factory.Sequence(lambda n: str(n))
    username = factory.Sequence(lambda n: f"User {n}")
    discriminator = factory.Sequence(lambda n: f"{n:04}")

class TwitchUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TwitchUser
    twitch_id = factory.Sequence(lambda n: str(n))
    username = factory.Sequence(lambda n: f"user_{n}")
