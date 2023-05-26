import asyncpraw
import os
import pickle
import pytz
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
submission_id = ""
usernames = {}


def save_dict():
    with open(f"pickle/{submission_id}-current_score.pickle", 'wb') as f:
        pickle.dump(current_score, f, pickle.HIGHEST_PROTOCOL)
    with open(f"pickle/{submission_id}-usernames.pickle", 'wb') as f:
        pickle.dump(usernames, f, pickle.HIGHEST_PROTOCOL)


def load_dict():
    global current_score
    global usernames

    if submission_id == "":
        return
    if os.path.isfile(f"pickle/{submission_id}-current_score.pickle"):
        with open(f"pickle/{submission_id}-current_score.pickle", 'rb') as f:
            current_score = pickle.load(f)
    if os.path.isfile(f"pickle/{submission_id}-usernames.pickle"):
        with open(f"pickle/{submission_id}-usernames.pickle", 'rb') as f:
            usernames = pickle.load(f)


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


def result_pitch(pitch):
    for user in current_guesses:
        diff = calculate_diff(current_guesses[user], pitch)
        score = calculate_score(diff)
        if user not in current_score:
            current_score.update({user: int(score)})
        else:
            current_score.update({user: int(current_score[user]) + int(score)})
    save_dict()


class SHADOWBALL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @guild_only()
    async def startgame(self, ctx, _submission_id=""):
        """Starts a game of Shadow Ball"""
        global game_started
        global submission_id
        if game_started is True:
            await ctx.send(f"A game is currently in progress")
            return

        submission_id = _submission_id
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

                    if team_abbreviation == team_abbrev and comment.parent_id[0:3] != "t1_" and comment.author == "FakeBaseball_Umpire" and len(comment_lines) == 3:
                        submission_id = comment.link_id.split("_")[1]
                        await ctx.send(f"<@&{role_id}> AB Posted```{comment.body}```")
                    elif team_abbreviation == team_abbrev and comment.author == "FakeBaseball_Umpire" and len(comment_lines) >= 5:
                        fifth_to_last_line = comment_lines[len(comment_lines) - 5].lstrip()
                        if fifth_to_last_line[0:6] == "Pitch:":
                            submission_id = comment.link_id.split("_")[1]
                            pitch = fifth_to_last_line.split(" ")[1]
                            result_pitch(pitch)
                            await ctx.send(f"Pitch was **{pitch}**.\n{display_guess_results(pitch)}\n\n{display_scoreboard()}")
                            current_guesses.clear()
            except Exception as e:
                print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {e}")
                time.sleep(10)
            else:
                time.sleep(10)
        await reddit.close()

    @commands.command()
    @guild_only()
    async def endgame(self, ctx):
        """Ends a game of Shadow Ball"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        await ctx.send(f"Game ended\n\n{display_scoreboard()}")
        save_dict()
        reset_game()

    @commands.command()
    @guild_only()
    async def guess(self, ctx, guess):
        """Submit a guess"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        current_guesses.update({ctx.message.author.id: guess})
        if ctx.message.author.nick is not None:
            usernames.update({ctx.message.author.id: ctx.message.author.nick})
        else:
            usernames.update({ctx.message.author.id: ctx.message.author.name})
        await ctx.send(f"Received your guess of **{guess}**")

    @commands.command()
    @guild_only()
    async def pitch(self, ctx, pitch):
        """Submit pitch manually"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        result_pitch(pitch)
        await ctx.send(f"Pitch was **{pitch}**.\n{display_guess_results(pitch)}\n\n{display_scoreboard()}")
        current_guesses.clear()

    @commands.command()
    @guild_only()
    async def scoreboard(self, ctx):
        """Shows current scoreboard"""
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        await ctx.send(f"-\n\n{display_scoreboard()}")


async def setup(bot):
    await bot.add_cog(SHADOWBALL(bot))
