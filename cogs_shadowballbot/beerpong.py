import asyncpraw
import os
import pickle
import pytz
import sys
import time
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import guild_only

role_id = os.getenv("ROLE_ID")
team_abbrev = os.getenv("TEAM_ABBREV")

pytz_utc = pytz.timezone('UTC')
pytz_pst = pytz.timezone('America/Los_Angeles')

reddit = asyncpraw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT_SHADOWBALLBOT")
)

current_guesses = {}
current_score = {}
game_started = False
usernames = {}


def save_dict():
    with open(f"pickle/current_score.pickle", 'wb') as f:
        pickle.dump(current_score, f, pickle.HIGHEST_PROTOCOL)
    with open(f"pickle/usernames.pickle", 'wb') as f:
        pickle.dump(usernames, f, pickle.HIGHEST_PROTOCOL)
    with open(f"pickle/current_guesses.pickle", 'wb') as f:
        pickle.dump(current_guesses, f, pickle.HIGHEST_PROTOCOL)


def load_dict():
    global current_score
    global usernames
    global current_guesses

    if os.path.isfile(f"pickle/current_score.pickle"):
        with open(f"pickle/current_score.pickle", 'rb') as f:
            current_score = pickle.load(f)
    if os.path.isfile(f"pickle/usernames.pickle"):
        with open(f"pickle/usernames.pickle", 'rb') as f:
            usernames = pickle.load(f)
    if os.path.isfile(f"pickle/current_guesses.pickle"):
        with open(f"pickle/current_guesses.pickle", 'rb') as f:
            current_guesses = pickle.load(f)


def calculate_diff(swing, pitch):
    if abs(int(swing) - int(pitch)) > 500:
        return 1000 - abs(int(swing) - int(pitch))
    else:
        return abs(int(swing) - int(pitch))


def calculate_score(diff):
    if diff <= 5:
        return 10
    elif diff <= 30:
        return 8
    elif diff <= 60:
        return 6
    elif diff <= 90:
        return 4
    elif diff <= 150:
        return 2
    elif diff <= 200:
        return 1
    elif diff <= 300:
        return 0
    elif diff <= 350:
        return -1
    elif diff <= 410:
        return -2
    elif diff <= 440:
        return -4
    elif diff <= 470:
        return -6
    elif diff <= 495:
        return -8
    elif diff <= 500:
        return -10
    else:
        return 0


def reset_game():
    global game_started
    current_guesses.clear()
    current_score.clear()
    game_started = False
    usernames.clear()

    if os.path.isfile(f"pickle/current_score.pickle"):
        os.remove(f"pickle/current_score.pickle")
    if os.path.isfile(f"pickle/usernames.pickle"):
        os.remove(f"pickle/usernames.pickle")


def display_guess_results(pitch):
    if not current_guesses:
        return "\nNo one guessed"
    diff_results = {}
    for user in current_guesses:
        diff = calculate_diff(current_guesses[user], pitch)
        diff_results.update({user: diff})

    string = ""
    for user in sorted(diff_results, key=diff_results.get):
        score = calculate_score(diff_results[user])
        string += f"\n**{usernames[user]}** guessed **{current_guesses[user]}**, for a diff of **{diff_results[user]}**, scoring **{score}** points."

    return string


def display_scoreboard():
    string = "**Scoreboard**:"
    for user in sorted(current_score, key=current_score.get, reverse=True):
        string += f"```{usernames[user]}: {current_score[user]}```"
    return string


def display_guesses():
    string = "**Current Guesses**:"
    for user in sorted(current_guesses, key=current_guesses.get, reverse=True):
        string += f"```{usernames[user]}: {current_guesses[user]}```"
    return string


def result_pitch(pitch):
    for user in current_guesses:
        diff = calculate_diff(current_guesses[user], pitch)
        score = calculate_score(diff)
        if user not in current_score:
            current_score.update({user: int(score)})
        else:
            current_score.update({user: int(current_score[user]) + int(score)})
    save_dict()


class BeerPong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @guild_only()
    async def ping(self, ctx):
        """Sb.ping Returns pong if bot is up"""

        await ctx.send("pong")

    @commands.command(aliases=['start'])
    @guild_only()
    async def startgame(self, ctx):
        """Sb.startgame Starts a new game of Beer Pong"""
        global game_started
        if game_started is True:
            await ctx.send(f"A game is currently in progress")
            return

        load_dict()
        await ctx.send(f"New game started")
        game_started = True
        while game_started is True:
            try:
                print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing comments")
                subreddit = await reddit.subreddit("fakebaseball")
                async for comment in subreddit.stream.comments(skip_existing=True):
                    if game_started is False:
                        await reddit.close()
                        return

                    if comment.author == "FakeBaseball_Umpire":
                        parent_comment = comment
                        await parent_comment.load()
                        while parent_comment.parent_id[0:3] == "t1_":
                            parent_comment = await parent_comment.parent()
                            await parent_comment.load()

                        comment_lines = comment.body.splitlines()
                        while "" in comment_lines:
                            comment_lines.remove("")
                        parent_comment_lines = parent_comment.body.splitlines()
                        while "" in parent_comment_lines:
                            parent_comment_lines.remove("")
                        team_abbreviation = "0xffffff"
                        if parent_comment.author == "FakeBaseball_Umpire" and len(parent_comment_lines) >= 3:
                            third_line = parent_comment_lines[2].lstrip()
                            team_abbreviation = third_line[0:3]

                        if team_abbreviation == team_abbrev and comment.parent_id[0:3] != "t1_" and len(comment_lines) == 3:
                            await ctx.send(f"<@&{role_id}> AB Posted```{comment.body}```")
                        elif team_abbreviation == team_abbrev and len(comment_lines) >= 5:
                            fifth_to_last_line = comment_lines[len(comment_lines) - 5].lstrip()
                            if fifth_to_last_line[0:6] == "Pitch:" and fifth_to_last_line.split(" ")[1].isdigit():
                                pitch = fifth_to_last_line.split(" ")[1]
                                result_pitch(pitch)
                                await ctx.send(f"Pitch was **{pitch}**.\n{display_guess_results(pitch)}\n\n{display_scoreboard()}")
                                current_guesses.clear()
            except Exception as e:
                print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {e}")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                time.sleep(10)
            else:
                time.sleep(10)
        await reddit.close()

    @commands.command(aliases=['end'])
    @guild_only()
    async def endgame(self, ctx):
        """Sb.endgame Ends a game of Beer Pong"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        await ctx.send(f"Game ended\n\n{display_scoreboard()}")
        save_dict()
        reset_game()

    @commands.command()
    @guild_only()
    async def guess(self, ctx, guess):
        """Sb.guess <guess> Submit/Update a guess"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        if not guess.isdigit() or int(guess) < 1 or int(guess) > 1000:
            await ctx.send(f"Invalid guess")
            return

        current_guesses.update({ctx.message.author.id: guess})
        if ctx.message.author.nick is not None:
            usernames.update({ctx.message.author.id: ctx.message.author.nick})
        else:
            usernames.update({ctx.message.author.id: ctx.message.author.name})
        save_dict()
        await ctx.send(f"Received your guess of **{guess}**")

    @commands.command()
    @guild_only()
    async def pitch(self, ctx, pitch):
        """Sb.pitch <pitch> Resolve a pitch manually"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        if not pitch.isdigit() or int(pitch) < 1 or int(pitch) > 1000:
            await ctx.send(f"Invalid pitch")
            return

        result_pitch(pitch)
        await ctx.send(f"Pitch was **{pitch}**.\n{display_guess_results(pitch)}\n\n{display_scoreboard()}")
        current_guesses.clear()

    @commands.command(aliases=['score', 'scores'])
    @guild_only()
    async def scoreboard(self, ctx):
        """Sb.scoreboard Shows current scoreboard"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        await ctx.send(f"-\n\n{display_scoreboard()}")

    @commands.command()
    @guild_only()
    async def showguesses(self, ctx):
        """Sb.showguesses Shows current guesses"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        await ctx.send(f"-\n\n{display_guesses()}")

    @commands.command(hidden=True)
    @commands.is_owner()
    @guild_only()
    async def editscore(self, ctx, _user, _score):
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        current_score.update({int(_user): int(_score)})
        save_dict()

    @commands.command(hidden=True)
    @commands.is_owner()
    @guild_only()
    async def editguess(self, ctx, _user, _guess):
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        current_guesses.update({int(_user): int(_guess)})
        save_dict()

    @commands.command(hidden=True)
    @commands.is_owner()
    @guild_only()
    async def debug(self, ctx):
        await ctx.send(f"```{current_score}```")


async def setup(bot):
    await bot.add_cog(BeerPong(bot))
