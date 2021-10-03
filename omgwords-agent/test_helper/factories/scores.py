import factory

from omgwords-agent.models import *
from .users import *


class ScorePBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScorePB
    current = True
    score = 100000
    user = factory.SubFactory(UserFactory)
