import constants
import discord
import io
import matplotlib.pyplot as plt
import os
import plotly.graph_objects as go
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only

pitch_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625, 650, 675, 700, 725, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
delta_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500]
grid_ticks = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


class Pitchers(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief="!cg <pitcher_id> <league>", aliases=['cg', 'current'])
    @guild_only()
    async def currentgame(self,
                          ctx,
                          pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                          league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]")):
        """
            Shows current game pitcher pitch/swing/delta sequences

            !currentgame <pitcher_id> <league>
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        x_legend = []
        pitches = []
        swings = []
        deltas = []
        pitcher_name = ""
        current_season = -1
        current_game = -1

        for i, p in enumerate(data):
            pitcher_name = p['pitcherName']
            same_game = False
            previous_pitch = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
                previous_pitch = int(data[i - 1]['pitch'])

            if int(p['season']) > int(current_season):
                pitches = []
                swings = []
                deltas = []
                x_legend = []
                current_season = p['season']
                current_game = p['gameID']
            if int(p['gameID']) > int(current_game):
                pitches = []
                swings = []
                deltas = []
                x_legend = []
                current_season = p['season']
                current_game = p['gameID']
            if int(p['season']) == int(current_season) and int(p['gameID']) == int(current_game):
                pitches.append(p['pitch'])
                swings.append(p['swing'])

                delta = ""
                if i == 0 or not same_game:
                    deltas.append(None)
                else:
                    delta = abs(int(p['pitch']) - previous_pitch)
                    if delta > 500:
                        delta = 1000 - delta
                    deltas.append(delta)

                x_legend.append(f"S{p['season']}.{p['session']}\nP: {p['pitch']}\nS: {p['swing']}\nD: {delta}")

        number_of_pitches = len(pitches)

        if number_of_pitches == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked to see the current game pitch/swing/delta details for {pitcher_name}. ({league})")

        plt.figure(figsize=(max(number_of_pitches / 1.5, 10.0), 5.0))
        plt.title(f"Current game pitch/swing/delta details for {pitcher_name}. ({league})")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_pitches), x_legend, size='small')
        plt.plot(pitches, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(swings, label='Swing', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(deltas, label='Delta', color='grey', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(pitches):
            plt.annotate(f" {txt}", (i, pitches[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!chart <pitcher_id> <league> [optional:season]", aliases=['charts'])
    @guild_only()
    async def chart(self,
                    ctx,
                    pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    season: int = commands.parameter(default=None, description="Season #")):
        """
            Shows pitcher pitch/swing/delta sequences

            !chart <pitcher_id> <league> [optional:season]
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        for p in data[:]:
            if (p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0) or (season is not None and season != int(p['season'])):
                data.remove(p)

        x_legend = []
        pitches = []
        swings = []
        deltas = []
        pitcher_name = ""

        for i, p in enumerate(data):
            pitcher_name = p['pitcherName']
            same_game = False
            previous_pitch = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
                previous_pitch = int(data[i - 1]['pitch'])

            delta = ""
            if i == 0 or not same_game:
                deltas.append(None)
            else:
                delta = abs(int(p['pitch']) - previous_pitch)
                if delta > 500:
                    delta = 1000 - delta
                deltas.append(delta)

            pitches.append(p['pitch'])
            swings.append(p['swing'])
            x_legend.append(f"S{p['season']}.{p['session']}\nP: {p['pitch']}\nS: {p['swing']}\nD: {delta}")

        number_of_pitches = len(pitches)

        if number_of_pitches == 0:
            await ctx.send(f"No matches")
            return

        if season is None:
            season = "all"

        await ctx.send(f"You asked to see the pitch/swing/delta details for {pitcher_name}. ({league}) ({season})")

        plt.figure(figsize=(max(number_of_pitches / 1.5, 10.0), 5.0))
        plt.title(f"Pitch/swing/delta details for {pitcher_name}. ({league}) ({season})")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_pitches), x_legend, size='small')
        plt.plot(pitches, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(swings, label='Swing', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(deltas, label='Delta', color='grey', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(pitches):
            plt.annotate(f" {txt}", (i, pitches[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!delta <pitcher_id> <league> [optional:situation:all]", aliases=['deltas'])
    @guild_only()
    async def delta(self,
                    ctx,
                    pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]")):
        """
            Shows pitcher pitch delta histogram

            !delta <pitcher_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            hit - After allowing a hit (walks included)
            out - After getting an out
            hr - After allowing a Home Run
            3b - After allowing a Triple
            2b - After allowing a Double
            1b - After allowing a Single
            bb - After allowing a Walk
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
            firstinning - First pitch of inning
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        deltas = []
        matches_count = 0
        pitcher = ""

        for i, p in enumerate(data):
            pitcher = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            previous_pitch = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
                previous_result = data[i - 1]['exactResult']
                previous_pitch = int(data[i - 1]['pitch'])

            match situation:
                case "all":
                    if i == 0 or not same_game:
                        continue
                case "empty":
                    if i == 0 or not same_game or obc >= 1:
                        continue
                case "onbase":
                    if i == 0 or not same_game or obc == 0:
                        continue
                case "risp":
                    if i == 0 or not same_game or obc <= 1:
                        continue
                case "corners":
                    if i == 0 or not same_game or obc != 5:
                        continue
                case "loaded":
                    if i == 0 or not same_game or obc <= 6:
                        continue
                case "dp":
                    if (i == 0 or not same_game) or (outs == 2 or not (obc == 1 or obc == 4 or obc == 5 or obc == 7)):
                        continue
                case "hit":
                    if i == 0 or not same_game or previous_result not in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "out":
                    if i == 0 or not same_game or previous_result in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "hr":
                    if i == 0 or not same_game or previous_result != "HR":
                        continue
                case "3b":
                    if i == 0 or not same_game or previous_result != "3B":
                        continue
                case "2b":
                    if i == 0 or not same_game or previous_result != "2B":
                        continue
                case "1b":
                    if i == 0 or not same_game or previous_result != "1B":
                        continue
                case "bb":
                    if i == 0 or not same_game or previous_result != "BB":
                        continue
                case "0out":
                    if i == 0 or not same_game or outs != 0:
                        continue
                case "1out":
                    if i == 0 or not same_game or outs != 1:
                        continue
                case "2out":
                    if i == 0 or not same_game or outs != 2:
                        continue
                case "firstinning":
                    if outs != 0 or (i > 0 and same_game and data[i]['inning'] == data[i - 1]['inning']):
                        continue
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            delta = abs(int(p['pitch']) - previous_pitch)
            if delta > 500:
                delta = 1000 - delta
            deltas.append(delta)
            matches_count += 1

        if matches_count == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for pitcher pitch deltas for {pitcher}. ({league}) ({situation})")

        plt.figure(figsize=(10.0, 5.0))
        plt.title(f"Pitcher pitch deltas for {pitcher}. ({league}) ({situation}) ({matches_count} deltas)")
        plt.xlim(0, 500)
        plt.xticks(rotation=90)
        plt.xticks(delta_ticks)
        values, bins, bars = plt.hist(deltas, color='grey', bins=range(0, 525, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!deltaswing <pitcher_id> <league> [optional:situation]", aliases=['deltaswings'])
    @guild_only()
    async def deltaswing(self,
                         ctx,
                         pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                         league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                         situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]")):
        """
            Shows pitcher swing delta histogram

            !deltaswing <pitcher_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            hit - After allowing a hit (walks included)
            out - After getting an out
            hr - After allowing a Home Run
            3b - After allowing a Triple
            2b - After allowing a Double
            1b - After allowing a Single
            bb - After allowing a Walk
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
            firstinning - First pitch of inning
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        deltas = []
        matches_count = 0
        pitcher = ""

        for i, p in enumerate(data):
            pitcher = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            previous_swing = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1][
                    'season'] and data[i]['session'] == data[i - 1]['session']
                previous_result = data[i - 1]['exactResult']
                previous_swing = int(data[i - 1]['swing'])

            match situation:
                case "all":
                    if i == 0 or not same_game:
                        continue
                case "empty":
                    if i == 0 or not same_game or obc >= 1:
                        continue
                case "onbase":
                    if i == 0 or not same_game or obc == 0:
                        continue
                case "risp":
                    if i == 0 or not same_game or obc <= 1:
                        continue
                case "corners":
                    if i == 0 or not same_game or obc != 5:
                        continue
                case "loaded":
                    if i == 0 or not same_game or obc <= 6:
                        continue
                case "dp":
                    if (i == 0 or not same_game) or (outs == 2 or not (obc == 1 or obc == 4 or obc == 5 or obc == 7)):
                        continue
                case "hit":
                    if i == 0 or not same_game or previous_result not in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "out":
                    if i == 0 or not same_game or previous_result in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "hr":
                    if i == 0 or not same_game or previous_result != "HR":
                        continue
                case "3b":
                    if i == 0 or not same_game or previous_result != "3B":
                        continue
                case "2b":
                    if i == 0 or not same_game or previous_result != "2B":
                        continue
                case "1b":
                    if i == 0 or not same_game or previous_result != "1B":
                        continue
                case "bb":
                    if i == 0 or not same_game or previous_result != "BB":
                        continue
                case "0out":
                    if i == 0 or not same_game or outs != 0:
                        continue
                case "1out":
                    if i == 0 or not same_game or outs != 1:
                        continue
                case "2out":
                    if i == 0 or not same_game or outs != 2:
                        continue
                case "firstinning":
                    if outs != 0 or (i > 0 and same_game and data[i]['inning'] == data[i - 1]['inning']):
                        continue
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            delta = abs(int(p['pitch']) - previous_swing)
            if delta > 500:
                delta = 1000 - delta
            deltas.append(delta)
            matches_count += 1

        if matches_count == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for pitcher swing deltas for {pitcher}. ({league}) ({situation})")

        plt.figure(figsize=(10.0, 5.0))
        plt.title(f"Pitcher swing deltas for {pitcher}. ({league}) ({situation}) ({matches_count} deltas)")
        plt.xlim(0, 500)
        plt.xticks(rotation=90)
        plt.xticks(delta_ticks)
        values, bins, bars = plt.hist(deltas, color='green', bins=range(0, 525, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!hm <pitcher_id> <league> [optional:situation]", aliases=['hm', 'heat'])
    @guild_only()
    async def heatmap(self,
                      ctx,
                      pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                      league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                      situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]")):
        """
            Shows pitcher heatmap

            !heatmap <pitcher_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            hit - After allowing a hit (walks included)
            out - After getting an out
            hr - After allowing a Home Run
            3b - After allowing a Triple
            2b - After allowing a Double
            1b - After allowing a Single
            bb - After allowing a Walk
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
            firstgame - First pitch of game
            firstinning - First pitch of inning
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        y = []
        x = []
        pitch = []
        matches_count = 0
        pitcher = ""
        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:  # just skip the non/auto resulted pitches
                data.remove(p)

        for i, p in enumerate(data):
            pitcher = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
                previous_result = data[i - 1]['exactResult']

            match situation:
                case "all":
                    pass
                case "empty":
                    if obc >= 1:
                        continue
                case "onbase":
                    if obc == 0:
                        continue
                case "risp":
                    if obc <= 1:
                        continue
                case "corners":
                    if obc != 5:
                        continue
                case "loaded":
                    if obc <= 6:
                        continue
                case "dp":
                    if outs == 2 or not (obc == 1 or obc == 4 or obc == 5 or obc == 7):
                        continue
                case "hit":
                    if i == 0 or not same_game or previous_result not in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "out":
                    if i == 0 or not same_game or previous_result in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "hr":
                    if i == 0 or not same_game or previous_result != "HR":
                        continue
                case "3b":
                    if i == 0 or not same_game or previous_result != "3B":
                        continue
                case "2b":
                    if i == 0 or not same_game or previous_result != "2B":
                        continue
                case "1b":
                    if i == 0 or not same_game or previous_result != "1B":
                        continue
                case "bb":
                    if i == 0 or not same_game or previous_result != "BB":
                        continue
                case "0out":
                    if outs != 0:
                        continue
                case "1out":
                    if outs != 1:
                        continue
                case "2out":
                    if outs != 2:
                        continue
                case "firstgame":
                    if same_game:
                        continue
                case "firstinning":
                    if outs != 0 or (i > 0 and same_game and data[i]['inning'] == data[i - 1]['inning']):
                        continue
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            the_pitch = int(p['pitch'])
            pitch.append(the_pitch)
            y.append(int(the_pitch / 100) * 100)  # 100s on the y axis of heatmap
            x.append(int(the_pitch % 100))  # 10s/1s on the x axis of heatmap
            matches_count += 1

        if matches_count == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for heatmap for {pitcher}. ({league}) ({situation})")

        title = f"Heatmap for {pitcher}. ({league}) ({situation}) ({matches_count} pitches)"
        annotations = [dict(xref='paper', yref='paper', x=0.0, y=1.05,
                            xanchor='left', yanchor='bottom',
                            text=title,
                            font=dict(family='Arial',
                                      size=18,
                                      color='rgb(37,37,37)'),
                            showarrow=False)]
        layout = go.Layout(
            autosize=False,
            width=1000,
            height=500,
        )
        fig = go.Figure(layout=layout)
        fig.add_trace(go.Histogram2d(
            colorscale=[[0, 'rgb(253,34,5)'], [0.25, 'rgb(253,192,5)'], [0.5, 'rgb(233,253,5)'],
                        [0.75, 'rgb(113,196,5)'], [1, 'rgb(5,196,19)']],
            reversescale=True,
            xbingroup=4,
            ybingroup=10,
            ygap=2,
            xgap=2,
            autobinx=False,
            xbins=dict(start=1, end=100, size=25),
            autobiny=False,
            ybins=dict(start=0, end=1000, size=100),
            x=x,
            y=y
        ))
        fig.update_xaxes(dtick=25)
        fig.update_yaxes(dtick=100)
        fig.update_traces(colorbar=dict(title="Num pitches"))
        fig.update_layout(annotations=annotations, margin_l=200, margin_r=200)
        fig.write_image("graph.png")

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

        plt.figure(figsize=(10.0, 5.0))
        plt.title(title)
        plt.xlim(1, 1000)
        plt.xticks(rotation=90)
        plt.xticks(pitch_ticks)
        values, bins, bars = plt.hist(pitch, color="blue", bins=range(1, 1025, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!last <pitcher_id> <league> <number_of_pitches> [optional:situation]")
    @guild_only()
    async def last(self,
                   ctx,
                   pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                   league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                   number_of_pitches: int = commands.parameter(default=None, description="Number of Pitches"),
                   situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]")):
        """
            Shows last N pitches and swings

            !last <pitcher_id> <league> <number_of_pitches> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            hit - After allowing a hit (walks included)
            out - After getting an out
            hr - After allowing a Home Run
            3b - After allowing a Triple
            2b - After allowing a Double
            1b - After allowing a Single
            bb - After allowing a Walk
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
            firstgame - First pitch of game
            firstinning - First pitch of inning
        """
        if pitcher_id is None or league is None or number_of_pitches is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        x_legend = []
        pitches = []
        swings = []
        pitcher_name = ""
        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        for i, p in enumerate(data):
            pitcher_name = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
                previous_result = data[i - 1]['exactResult']

            match situation:
                case "all":
                    pass
                case "empty":
                    if obc >= 1:
                        continue
                case "onbase":
                    if obc == 0:
                        continue
                case "risp":
                    if obc <= 1:
                        continue
                case "corners":
                    if obc != 5:
                        continue
                case "loaded":
                    if obc <= 6:
                        continue
                case "dp":
                    if outs == 2 or not (obc == 1 or obc == 4 or obc == 5 or obc == 7):
                        continue
                case "hit":
                    if i == 0 or not same_game or previous_result not in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "out":
                    if i == 0 or not same_game or previous_result in ("HR", "3B", "2B", "1B", "BB"):
                        continue
                case "hr":
                    if i == 0 or not same_game or previous_result != "HR":
                        continue
                case "3b":
                    if i == 0 or not same_game or previous_result != "3B":
                        continue
                case "2b":
                    if i == 0 or not same_game or previous_result != "2B":
                        continue
                case "1b":
                    if i == 0 or not same_game or previous_result != "1B":
                        continue
                case "bb":
                    if i == 0 or not same_game or previous_result != "BB":
                        continue
                case "0out":
                    if outs != 0:
                        continue
                case "1out":
                    if outs != 1:
                        continue
                case "2out":
                    if outs != 2:
                        continue
                case "firstgame":
                    if same_game:
                        continue
                case "firstinning":
                    if outs != 0 or (i > 0 and same_game and data[i]['inning'] == data[i - 1]['inning']):
                        continue
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            pitches.append(p['pitch'])
            swings.append(p['swing'])
            x_legend.append(f"S{p['season']}.{p['session']}\n{p['inning']}\nP: {p['pitch']}\nS: {p['swing']}")

        x_legend = x_legend[-number_of_pitches:]
        pitches = pitches[-number_of_pitches:]
        swings = swings[-number_of_pitches:]
        number_of_pitches = len(pitches)

        if number_of_pitches == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for last {number_of_pitches} pitches for {pitcher_name}. ({league}) ({situation})")

        plt.figure(figsize=(max(number_of_pitches / 1.5, 10.0), 5.0))
        plt.title(f"Last {number_of_pitches} pitches for {pitcher_name}. ({league}) ({situation})")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_pitches), x_legend, size='small')
        plt.plot(pitches, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(swings, label='Swing', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(pitches):
            plt.annotate(f" {txt}", (i, pitches[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!react <pitcher_id> <league> <lower_pitch> [optional:upper_pitch]", aliases=['reacts'])
    @guild_only()
    async def react(self,
                    ctx,
                    pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    lower_pitch: int = commands.parameter(default=None, description="Lower Pitch"),
                    upper_pitch: int = commands.parameter(default=None, description="optional:Upper Pitch")):
        """
            Shows reactions before & after pitching a certain range

            !react <pitcher_id> <league> <lower_pitch> [optional:upper_pitch]
        """
        if pitcher_id is None or league is None or lower_pitch is None:
            await ctx.send(f"Missing argument(s)")
            return

        if upper_pitch is None:
            upper_pitch = lower_pitch

        x_legend = []
        pitch = []  # all non-autoed pitches
        season = []  # all non-autoed seasons
        session = []  # all non-autoed sessions
        inning = []  # all non-autoed innings
        pitcher_name = ""
        matches_count = 0

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        # get pitcher name and read it all in
        for p in data[:]:
            pitcher_name = p['pitcherName']
            if p['pitch'] is not None and p['swing'] is not None and p['pitch'] != 0 and p['swing'] != 0:  # just skip the non/auto resulted pitches
                pitch.append(p['pitch'])
                season.append(p['season'])
                session.append(p['session'])
                inning.append(p['inning'])
            else:
                data.remove(p)

        before = []  # pitch before the match
        match = []  # the match
        after = []  # pitch after the match

        # now let's go through and look for matches
        for p in range(len(pitch) - 1):
            if (upper_pitch >= lower_pitch and upper_pitch >= int(pitch[p]) >= lower_pitch) or (upper_pitch < lower_pitch and (upper_pitch >= int(pitch[p]) or lower_pitch <= int(pitch[p]))):  # it's a match for a range
                if p < len(pitch) - 1 and season[p] == season[p + 1] and session[p] == session[p + 1]:
                    legend = f"S{season[p]}.{session[p]}\n{inning[p]}"
                    if p > 0 and season[p] == season[p - 1] and session[p] == session[p - 1]:
                        before.append(pitch[p - 1])
                        legend += f"\nB: {pitch[p - 1]}"
                    else:
                        before.append(None)
                        legend += "\nB: "

                    match.append(pitch[p])
                    after.append(pitch[p + 1])

                    legend += f"\nM: {pitch[p]}\nA: {pitch[p + 1]}"

                    matches_count += 1  # count matches
                    x_legend.append(legend)

        if matches_count == 0:
            await ctx.send(f"No matches")
            return

        # Quick check to report reactions
        range_title = f"{lower_pitch} - {upper_pitch}"
        await ctx.send(f"You asked for pitches for {pitcher_name} before & after pitching {range_title}. ({league})")

        plt.figure(figsize=(max(matches_count / 1.5, 10.0), 5.0))  # Creates a new figure
        plt.title(f"Pitches for {pitcher_name} before & after pitching {range_title}. ({league}) ({matches_count} matches)")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(matches_count), x_legend, size='small')
        plt.plot(before, label='Before', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(match, label='Match', color='grey', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(after, label='After', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(after):
            plt.annotate(f" {txt}", (i, after[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig("graph.png", bbox_inches='tight')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')


async def setup(client):
    await client.add_cog(Pitchers(client))
