import factory

from omgwords-agent.models import *


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page
