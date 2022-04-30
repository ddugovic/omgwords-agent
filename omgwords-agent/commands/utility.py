import random
from django.core.cache import cache
from discord import Embed
from datetime import datetime

from .command import Command, CommandException
from ..models import Side, TwitchChannel
from ..util import Platform
from ..discord import GUILD_ID, client as discord_client
from..util.fieldgen.hz_simulation import HzSimulation
from ..words import Words


COIN_FLIP_TIMEOUT = 10

HEADS = 0
TAILS = 1
SIDE = 2
COIN_MESSAGES = {
    HEADS: "Heads!",
    TAILS: "Tails!",
    SIDE: "Side o.O"
}

@Command.register_discord("hz", "hydrant", usage="hz <level> <height> <taps>")
class HzCommand(Command):

    def execute(self, level, height, taps):
        try:
            level = int(level)
            height = int(height)
            taps = int(taps)
        except ValueError:
            raise CommandException(send_usage = True)
        
        try:
            hz = HzSimulation(level,height,taps)
        except ValueError as e:
            raise CommandException(str(e))
                 
        rate = hz.hertz()
        msg = "{tps} taps {hght} high on level {lvl}:\n{mini} - {maxi} Hz\n".format(
            tps=hz.taps,
            hght=hz.height,
            lvl=hz.level,
            mini=rate[0],
            maxi=rate[1]
            )

        # Eagerly cache the image instead of letting the web server handle it lazily
        hz.cache_image()

        printable_sequence = hz.printable_sequence()
        if len(printable_sequence) <= 49:
            msg += "Sample input sequence: {seq}".format(seq=printable_sequence)
        else:
            msg += "Sample sequence too long. (GIF will not animate)"

        msg = "```"+msg+"```"

        embed = Embed().set_image(url=hz.image_url)
        self.send_message_full(self.context.channel.id, msg, embed=embed)

@Command.register("seed", "hex", usage="seed")
class SeedGenerationCommand(Command):
    def execute(self, *args):
        seed = 0
        while (seed % 0x100 < 0x3):
            seed = random.randint(0x200, 0xffffff)
        self.send_message(("RANDOM SEED: [%06x]" % seed))


@Command.register("coin", "flip", "coinflip", usage="flip")
class CoinFlipCommand(Command):

    def execute(self, *args):
        if self.context.platform == Platform.TWITCH:
            self.check_moderator()
        elif (self.context.message.guild and self.context.message.guild.id == GUILD_ID):
            self.context.platform_user.send_message("Due to abuse, `!flip` has been disabled in the CTM Discord server.")

            self.context.delete_message(self.context.message)
            return

        if cache.get(f"flip.{self.context.user.id}"):
            return
        cache.set(f"flip.{self.context.user.id}", True, timeout=COIN_FLIP_TIMEOUT)

        o = [HEADS, TAILS, SIDE]
        w = [0.4995, 0.4995, 0.001]
        choice = random.choices(o, weights=w, k=1)[0]

        self.send_message(COIN_MESSAGES[choice])
        if choice == SIDE:
            Side.log(self.context.user)


@Command.register_discord("utc", "time", usage="utc")
class UTCCommand(Command):
    def execute(self, *args):
        t = datetime.utcnow()
        l1 = t.strftime("%A, %b %d")
        l2 = t.strftime("%H:%M (%I:%M %p)")
        self.send_message(f"Current date/time in UTC:\n**{l1}**\n**{l2}**")


@Command.register_discord("stats", usage="stats")
class StatsCommand(Command):
    def execute(self, *args):
        self.check_moderator()

        guilds = len(discord_client.guilds)
        channels = TwitchChannel.objects.filter(connected=True).count()

        self.send_message(f"I'm in {guilds} Discord servers and {channels} Twitch channels.")

@Command.register_twitch("authword", usage="authword")
class AuthWordCommand(Command):

    def execute(self, *args):
        self.check_moderator()
        word = Words.get_word()
        self.send_message(f"Authword: {word}")
