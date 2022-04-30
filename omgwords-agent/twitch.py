import irc.client
import logging
import re
import requests
import time
from threading import Thread

from .env import env


TWITCH_API = "https://api.twitch.tv/kraken/"
TWITCH_API_HELIX = "https://api.twitch.tv/helix/"
TWITCH_SERVER = "irc.chat.twitch.tv"
TWITCH_PORT = 6667

logger = logging.getLogger("twitch-bot")

class APIClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": client_id
        }

    def _request(self, endpoint, params={}, headers={}, api=TWITCH_API):
        response = requests.get(f"{api}{endpoint}", params=params,
                                headers={**self.headers, **headers})
        return response.json()

    def user_from_username(self, username, client=None):
        response = self._request("users", { "login": username })
        if "error" in response:
            return None
        elif response["users"]:
            user_obj = response["users"][0]
            return self.wrap_user_dict(user_obj, client)
        else:
            return None

    def user_from_id(self, user_id, client=None):
        response = self._request(f"users/{user_id}")
        if "error" in response:
            return None
        else:
            return self.wrap_user_dict(response, client)

    def own_user(self, token, client=None):
        user_data = self._request(f"users", api=TWITCH_API_HELIX,
                                  headers={"Authorization": f"Bearer {token}"})
        user_dict = user_data["data"][0]
        return User(
            client=client,
            username=user_dict["login"],
            id=user_dict["id"],
            display_name=user_dict["display_name"],
            tags=user_dict
        )

    def usernames_in_channel(self, channel):
        response = self._request(f"group/user/{channel}/chatters", api="http://tmi.twitch.tv/")
        return sum((group for group in response["chatters"].values()), [])

    def wrap_user_dict(self, user_dict, client=None):
        return User(
            client=client,
            username=user_dict["name"],
            id=user_dict["_id"],
            display_name=user_dict["display_name"],
            tags=user_dict
        )



class Client:
    def __init__(self, username, token, default_channels=[]):
        self.username = username
        self.token = token
        self.default_channels = default_channels
        self.reactor = irc.client.Reactor()
        self.connection = self.reactor.server()

        self.on_welcome(self.handle_welcome)

    def handle_welcome(self):
        self.connection.cap("REQ", ":twitch.tv/tags")
        self.connection.cap("REQ", ":twitch.tv/commands")

        Thread(target=self.join_channels).start()

    def start(self):
        self.user_obj = API.user_from_username(self.username, self)
        self.user_id = self.user_obj.id
        self.connection.connect(TWITCH_SERVER, TWITCH_PORT, self.username, self.token)
        self.reactor.process_forever()

    def on_welcome(self, handler):
        self.connection.add_global_handler("welcome", lambda c, e: handler())

    def on_message(self, handler):
        self.connection.add_global_handler("pubmsg", lambda c, e: self._handle_message(e, handler))
        self.connection.add_global_handler("whisper", lambda c, e: self._handle_message(e, handler))
        return handler

    def _handle_message(self, event, handler):
        tags = { tag["key"]: tag["value"] for tag in event.tags }
        username = re.match(r"\w+!(\w+)@[\w.]+", event.source)[1]
        author = User(self, username, tags["user-id"], tags["display-name"], tags)
        if event.type == "pubmsg":
            channel = PublicChannel(self, event.target[1:])
        elif event.type == "whisper":
            channel = Whisper(self, author)
        message = Message(event.arguments[0], author, channel)
        handler(message)

    def send_message(self, target, text):
        self.connection.privmsg(target, text)

    def get_user(self, user_id):
        return API.user_from_id(user_id, self)

    def get_channel(self, channel_name):
        return PublicChannel(self, channel_name)

    def join_channels(self):
        from .models import TwitchChannel
        channel_names = (self.default_channels +
                         list(TwitchChannel.objects.filter(connected=True).values_list("twitch_user__username",
                                                                                       flat=True)))
        for channel in channel_names:
            self.join_channel(channel)
            # Band-aid to prevent Twitch from disconnecting the bot for joining too many channels at
            # once
            time.sleep(0.5)

    def join_channel(self, channel_name):
        logger.info(f"Joining channel #{channel_name}")
        self.connection.join(f"#{channel_name}")

    def leave_channel(self, channel_name):
        logger.info(f"Leaving channel #{channel_name}")
        self.connection.part(f"#{channel_name}")


class User:
    def __init__(self, client, username, id, display_name, tags={}):
        self.client = client
        self.username = username
        self.id = id
        self.display_name = display_name
        self.tags = tags

    @property
    def is_moderator(self):
        return self.tags.get("mod") == "1"

    def send_message(self, message):
        if self.client is None:
            raise Exception("send_message called without client")
        whisper = Whisper(self.client, self)
        whisper.send_message(message)


class Message:
    def __init__(self, content, author, channel):
        self.content = content
        self.author = author
        self.channel = channel


class Channel:
    def __init__(self, client):
        self.client = client

class PublicChannel(Channel):
    type = "channel"
    def __init__(self, client, name):
        super().__init__(client)
        self.name = name

    def send_message(self, message):
        self.client.send_message(f"#{self.name}", message)

class Whisper(Channel):
    type = "whisper"
    def __init__(self, client, author):
        super().__init__(client)
        self.author = author

    def send_message(self, message):
        self.client.send_message("#jtv", f"/w {self.author.username} {message}")



API = APIClient(env("TWITCH_CLIENT_ID", default=""))

if API.client_id != "":
    client = Client(
        env("TWITCH_USERNAME", default=""),
        env("TWITCH_TOKEN"),
        default_channels=[env("TWITCH_USERNAME", default="")]
    )
