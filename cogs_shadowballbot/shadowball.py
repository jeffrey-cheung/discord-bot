import asyncpraw
import os
from discord.ext import commands

game_started = False
current_guesses = {}
current_score = {}
usernames = {}
waiting_for_pitch = False


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
    else:
        return -1


def reset_game():
    global game_started
    global current_guesses
    global current_score
    global usernames
    global waiting_for_pitch
    game_started = False
    current_guesses = {}
    current_score = {}
    usernames = {}
    waiting_for_pitch = False


def display_guess_results(pitch):
    if not current_guesses:
        return "No one guessed"
    string = ""
    for user in current_guesses:
        diff = calculate_diff(current_guesses[user], pitch)
        score = calculate_score(diff)
        string += f"**{usernames[user]}** guessed **{current_guesses[user]}**, for a diff of **{diff}**, scoring **{score}** points."
    return string


def display_scoreboard():
    string = "**Scoreboard**:"
    for user in current_score:
        string += f"```{usernames[user]}: {current_score[user]}```"
    return string


def result_pitch(ctx, pitch):
    global current_guesses
    global waiting_for_pitch
    waiting_for_pitch = False
    for user in current_guesses:
        diff = calculate_diff(current_guesses[user], pitch)
        score = calculate_score(diff)
        if user not in current_score:
            current_score.update({user: score})
        else:
            current_score.update({user: current_score[user] + score})
    await ctx.send(f"Pitch was **{pitch}**.\n\n{display_guess_results(pitch)}\n\n{display_scoreboard()}")
    current_guesses = {}


class SHADOWBALL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def start_game(self, ctx):
        """Starts a game of Shadow Ball"""
        global game_started
        global waiting_for_pitch
        if game_started is True:
            await ctx.send(f"A game is currently in progress")
            return

        reddit = asyncpraw.Reddit(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            user_agent=os.getenv("USER_AGENT_PLAY_BY_PLAY")
        )

        await ctx.send(f"New game started")
        game_started = True

        # submission = await reddit.submission("13fm4bi")
        # comments = await submission.comments()
        # for top_level_comment in comments:
        #     comment = top_level_comment

        subreddit = await reddit.subreddit("fakebaseball")
        async for comment in subreddit.stream.comments(skip_existing=True):
            if game_started is False:
                await reddit.close()
                return

            parent_comment = comment
            while parent_comment.parent_id[0:3] == "t1_":
                parent_comment = parent_comment.parent()

            lines = parent_comment.body.splitlines()
            while "" in lines:
                lines.remove("")
            team_abbreviation = "0xffffff"
            if parent_comment.author == "FakeBaseball_Umpire" and len(lines) >= 3:
                third_line = lines[2].lstrip()
                team_abbreviation = third_line[0:3]

            if waiting_for_pitch is False and comment.parent_id[0:3] != "t1_" and comment.author == "FakeBaseball_Umpire" and len(lines) == 3:
                waiting_for_pitch = True
                await ctx.send(f"<@&1060698924584804416> AB Posted!```{comment.body}```")
            elif waiting_for_pitch is True and comment.author == "FakeBaseball_Umpire" and len(lines) >= 5:
                fifth_to_last_line = lines[len(lines) - 5].lstrip()
                if fifth_to_last_line[0:6] == "Pitch:":
                    pitch = fifth_to_last_line.split(" ")[1]
                    result_pitch(ctx, pitch)

    @commands.command()
    async def end_game(self, ctx):
        """Ends a game of Shadow Ball"""
        global game_started
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        reset_game()
        await ctx.send(f"Game ended")

    @commands.command()
    async def guess(self, ctx, guess):
        """Submit a guess"""
        global game_started
        global current_guesses
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        current_guesses.update({ctx.message.author.id: guess})
        usernames.update({ctx.message.author.id: ctx.message.author.name})
        await ctx.send(f"Received your guess of **{guess}**")

    @commands.command()
    async def pitch(self, ctx, pitch):
        """Submit pitch manually"""
        global game_started
        if game_started is False:
            await ctx.send(f"There is no game in progress")
            return

        result_pitch(ctx, pitch)


async def setup(bot):
    await bot.add_cog(SHADOWBALL(bot))
