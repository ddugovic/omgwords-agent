from django.core.exceptions import ObjectDoesNotExist

from ..command import Command, CommandException
from ...queue import Queue
from ...util import memoize

"""
queue.py:
    !open
    !close
    !addmatch <player1> <player2>
    !removematch <id>
    !clear
    !queue !q !matches
    !endmatch
    !winner
    !forfeit

challenge.py
    !challenge
    !cancel
    !accept
    !decline
    !forfeit
    !match
    Closest matches are...

"""



class QueueCommand(Command):
    @property
    @memoize
    def queue(self):
        return Queue.get(self.context.channel.name)

    @property
    def current_match(self):
        return self.queue.current_match

    def is_queue_open(self):
        return self.queue and self.queue.is_open()

    def check_queue_exists(self):
        if not self.queue:
            raise CommandException("There is no current queue.")

    def check_current_match(self):
        if not self.current_match:
            raise CommandException("There is no current match.")

    def format_match(self, match):
        if match:
            return "{player1} vs. {player2}".format(
                player1=match.player1.twitch_user.username,
                player2=match.player2.twitch_user.username
            )
        else:
            return "No current match."

    def format_queue(self, queue):
        if queue and not queue.is_empty():
            match_strings = []
            for i, match in enumerate(queue):
                try:
                    match_strings.append(f"[{i+1}]: {self.format_match(match)}")
                except ObjectDoesNotExist:
                    # Something went wrong displaying this match, probably someone changed their
                    # Twitch username
                    pass
            return " ".join(match_strings)
        else:
            return "No current queue."

    def match_index(self, index_string):
        try:
            index = int(index_string)
        except ValueError:
            raise CommandException("Invalid index.")

        if index < 1 or index > len(self.queue):
            raise CommandException("No match at specified index.")

        return index


@Command.register_twitch("open", "openqueue",
                         usage="open")
class OpenQueueCommand(QueueCommand):
    def execute(self):
        self.check_public()
        self.check_moderator()

        if self.is_queue_open():
            raise CommandException("The queue has already been opened.")
        else:
            if self.queue:
                self.queue.open()
                self.send_message("The queue has been repoened!")
            else:
                Queue(self.context.channel.name).open()
                self.send_message("The queue is now open!")


@Command.register_twitch("close", "closequeue",
                         usage="close")
class CloseQueueCommand(QueueCommand):
    def execute(self):
        self.check_public()
        self.check_moderator()

        if not self.is_queue_open():
            raise CommandException("The queue isn't open!")
        else:
            self.queue.close()
            self.send_message("The queue has been closed.")


@Command.register_twitch("queue", "q", "matches",
                         usage="queue")
class ShowQueueCommand(QueueCommand):
    def execute(self):
        self.check_public()
        self.send_message(self.format_queue(self.queue))


@Command.register_twitch("addmatch",
                         usage="addmatch <player 1> <player 2>")
class AddMatchCommand(QueueCommand):
    def execute(self, player1, player2):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()

        twitch_user1 = Command.twitch_user_from_username(player1)
        twitch_user2 = Command.twitch_user_from_username(player2)

        if twitch_user1 is None:
            raise CommandException(f"The twitch user \"{player1}\" does not exist.")
        if twitch_user2 is None:
            raise CommandException(f"The twitch user \"{player2}\" does not exist.")

        self.queue.add_match(twitch_user1.user, twitch_user2.user)
        self.send_message(f"A match has been added between {twitch_user1.user_tag} and {twitch_user2.user_tag}!")


@Command.register_twitch("insertmatch",
                         usage="insertmatch <player 1> <player 2> <index>")
class InsertMatchCommand(QueueCommand):
    def execute(self, player1, player2, index):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()

        twitch_user1 = Command.twitch_user_from_username(player1)
        twitch_user2 = Command.twitch_user_from_username(player2)

        if twitch_user1 is None:
            raise CommandException(f"The twitch user \"{player1}\" does not exist.")
        if twitch_user2 is None:
            raise CommandException(f"The twitch user \"{player2}\" does not exist.")

        try:
            index = int(index)
        except:
            raise CommandException("Invalid index.")


        i = self.queue.insert_match(twitch_user1.user, twitch_user2.user, index)
        self.send_message(f"A match has been added between {twitch_user1.user_tag} and "
                          f"{twitch_user2.user_tag} at index {i}!")


@Command.register_twitch("movematch", "move",
                         usage="move <current index> <new index>")
class MoveMatchCommand(QueueCommand):
    def execute(self, old_index, new_index):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()

        try:
            i1 = int(old_index)
            i2 = int(new_index)
        except ValueError:
            raise CommandException("One of your indicies is invalid.")

        if i1 > len(self.queue):
            raise CommandException(f"There's no match to move at index {i1}.")

        self.queue.move_match(i1, i2)
        self.send_message("Match moved! New queue: {queue}".format(
            queue=self.format_queue(self.queue)
        ))


@Command.register_twitch("removematch",
                         usage="removematch <index>")
class RemoveMatchCommand(QueueCommand):
    def execute(self, index):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()

        index = self.match_index(index)
        self.queue.remove_match(index)
        self.send_message("Match removed! New queue: {queue}".format(
            queue=self.format_queue(self.queue)
        ))


@Command.register_twitch("clear", "clearqueue",
                         usage="clear yesimsure")
class ClearQueueCommand(QueueCommand):
    def execute(self, confirm):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()

        if confirm == "yesimsure":
            self.queue.clear()
            self.send_message("The queue has been cleared.")

        else:
            self.send_usage()


@Command.register_twitch("winner", "declarewinner",
                         usage="winner <player> [losing score]")
class DeclareWinnerCommand(QueueCommand):
    def execute(self, player_name, losing_score=None):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()
        self.check_current_match()

        if losing_score is not None:
            try:
                losing_score = int(losing_score)
            except ValueError:
                raise CommandException("Invalid losing score.")
            if losing_score < 0 or losing_score > 1400000:
                raise CommandException("Invalid losing score.")

        twitch_user = self.twitch_user_from_username(player_name)
        if not twitch_user:
            raise CommandException(f"Twitch user \"{player_name}\" does not exist.")


        try:
            self.queue.declare_winner(twitch_user.user, losing_score)
        except ValueError:
            raise CommandException(f"player \"{twitch_user.username}\" is not in the current match.")


        current_winner = self.current_match.get_current_winner()

        msg_winner = f"{twitch_user.username} has won a game!"
        msg_score = "The score is now {score1}-{score2}.".format(
            score1=self.current_match.wins1,
            score2=self.current_match.wins2
        )
        if current_winner:
            msg_lead = f"{current_winner.twitch_user.username} is ahead!"
        else:
            msg_lead = "It's all tied up!"

        strings = [msg_winner, msg_score, msg_lead]
        self.send_message(" ".join(strings))


@Command.register_twitch("endmatch",
                         usage="endmatch")
class EndMatchCommand(QueueCommand):
    def execute(self):
        self.check_public()
        self.check_moderator()
        self.check_queue_exists()
        self.check_current_match()

        match = self.current_match
        winner = match.get_current_winner()
        self.queue.end_match()

        # TODO: Handle ties?
        if winner:
            self.send_message(f"Congratulations, {winner.twitch_user.username}!")
        self.send_message(f"Next match: {self.format_match(self.current_match)}")


@Command.register_twitch("forfeit",
                         usage="forfeit <index>")
class ForfeitMatchCommand(QueueCommand):
    def execute(self, index):
        self.check_public()
        self.check_queue_exists()

        index = self.match_index(index)
        match = self.queue.get_match(index)
        user = self.context.user

        forfeitee = None
        if match.player1 == user:
            forfeitee = match.player2
        elif match.player2 == user:
            forfeitee = match.player1

        if forfeitee:
            self.queue.remove_match(index)
            self.send_message("{player1} has forfeited their match against {player2}! New queue: {queue}".format(
                player1=user.twitch_user.username,
                player2=forfeitee.twitch_user.username,
                queue=self.format_queue(self.queue)
            ))
        else:
            raise CommandException(f"{user.twitch_user.user_tag}, you're not playing in that match!")
