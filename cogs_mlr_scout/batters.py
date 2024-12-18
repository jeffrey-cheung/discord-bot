import io
import os

import discord
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import requests
from discord.ext import commands
from discord.ext.commands import guild_only

pitch_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525,
               550, 575, 600, 625, 650, 675, 700, 725, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
delta_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500]
grid_ticks = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


class Batters(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief="!bhm <batter_id> <league> [optional:situation]", aliases=['bhm', 'bheatmap', 'batterhm'])
    @guild_only()
    async def batterheatmap(self,
                            ctx,
                            batter_id: int = commands.parameter(default=None, description="Batter ID"),
                            league: str = commands.parameter(default=None,
                                                             description="League [MLR, MiLR, FCB, Scrim]"),
                            situation: str = commands.parameter(default="all",
                                                                description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, 0out, 1out, 2out]")):
        """
            Shows batter swing heatmap

            !batterheatmap <batter_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, 0out, 1out, 2out]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
        """
        if batter_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(
            f"https://www.rslashfakebaseball.com/api/plateappearances/batting/{league}/{batter_id}")).json()

        y = []
        x = []
        swing = []
        matches_count = 0
        batter = ""
        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        for i, p in enumerate(data):
            batter = p['hitterName']
            outs = int(p['outs'])
            obc = int(p['obc'])

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
                case "0out":
                    if outs != 0:
                        continue
                case "1out":
                    if outs != 1:
                        continue
                case "2out":
                    if outs != 2:
                        continue
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            the_swing = int(p['swing'])
            swing.append(the_swing)
            y.append(int((the_swing - 1) / 100) * 100)  # 100s on the y axis of heatmap
            x.append(int((the_swing - 1) % 100))  # 10s/1s on the x axis of heatmap
            matches_count += 1

        if matches_count == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for swing heatmap for {batter}. ({league}) ({situation})")

        title = f"Swing heatmap for {batter}. ({league}) ({situation}) ({matches_count} swings)"
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
            xbins=dict(start=0, end=100, size=25),
            autobiny=False,
            ybins=dict(start=0, end=1000, size=100),
            x=x,
            y=y
        ))
        fig.update_xaxes(dtick=25)
        fig.update_yaxes(dtick=100)
        fig.update_traces(colorbar=dict(title="Num swings"))
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
        values, bins, bars = plt.hist(swing, color="red", bins=range(1, 1025, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!blast <batter_id> <league> <number_of_swings> [optional:situation]", aliases=['blast'])
    @guild_only()
    async def batterlast(self,
                         ctx,
                         batter_id: int = commands.parameter(default=None, description="Batter ID"),
                         league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                         number_of_swings: int = commands.parameter(default=None, description="Number of Swings"),
                         situation: str = commands.parameter(default="all",
                                                             description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, 0out, 1out, 2out]")):
        """
            Shows last N swings and pitches for batter

            !batterlast <batter_id> <league> <number_of_swings> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, 0out, 1out, 2out, firstgame]

            Possible situations:
            all - All pitches
            empty - Bases empty
            onbase - At least 1 runner on base
            risp - Runner on 2nd and/or 3rd
            corners - Runner on 1st and 3rd
            loaded - Bases load
            dp - Runner on 1st with less than 2 outs
            0out - 0 out(s)
            1out - 1 out(s)
            2out - 2 out(s)
            firstgame - First swing of game
        """
        if batter_id is None or league is None or number_of_swings is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(
            f"https://www.rslashfakebaseball.com/api/plateappearances/batting/{league}/{batter_id}")).json()

        x_legend = []
        pitches = []
        swings = []
        batter_name = ""
        for p in data[:]:
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.remove(p)

        for i, p in enumerate(data):
            batter_name = p['hitterName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False

            if i > 0:
                same_game = data[i]['gameID'] == data[i - 1]['gameID'] and data[i]['season'] == data[i - 1][
                    'season'] and data[i]['session'] == data[i - 1]['session']

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
                case _:
                    await ctx.send(f"Unrecognized situation")
                    return

            pitches.append(p['pitch'])
            swings.append(p['swing'])
            x_legend.append(f"S{p['season']}.{p['session']}\n{p['inning']}\nS: {p['swing']}\nP: {p['pitch']}")

        x_legend = x_legend[-number_of_swings:]
        pitches = pitches[-number_of_swings:]
        swings = swings[-number_of_swings:]
        number_of_swings = len(swings)

        if number_of_swings == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for last {number_of_swings} swings for {batter_name}. ({league}) ({situation})")

        plt.figure(figsize=(max(number_of_swings / 1.5, 10.0), 5.0))
        plt.title(f"Last {number_of_swings} swings for {batter_name}. ({league}) ({situation})")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_swings), x_legend, size='small')
        plt.plot(swings, label='Swing', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(pitches, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(swings):
            plt.annotate(f" {txt}", (i, swings[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command(brief="!swing <batter_id> <league> [optional:season]", aliases=['swings'])
    @guild_only()
    async def swing(self,
                    ctx,
                    batter_id: int = commands.parameter(default=None, description="Batter ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    season: int = commands.parameter(default=None, description="Season #")):
        """
            Shows batter swing/pitch/diff sequences

            !swing <batter_id> <league> [optional:season]
        """
        if batter_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(
            f"https://www.rslashfakebaseball.com/api/plateappearances/batting/{league}/{batter_id}")).json()

        for p in data[:]:
            if (p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0) or (
                    season is not None and season != int(p['season'])):
                data.remove(p)

        x_legend = []
        pitches = []
        swings = []
        diffs = []
        hitter_name = ""

        for i, p in enumerate(data):
            hitter_name = p['hitterName']
            pitches.append(p['pitch'])
            swings.append(p['swing'])
            diffs.append(p['diff'])
            x_legend.append(f"S: {p['swing']}\nP: {p['pitch']}\nD: {p['diff']}")

        number_of_pitches = len(pitches)

        if number_of_pitches == 0:
            await ctx.send(f"No matches")
            return

        if season is None:
            season = "all"

        await ctx.send(f"You asked to see the swing/pitch/diff details for {hitter_name}. ({league}) ({season})")

        plt.figure(figsize=(max(number_of_pitches / 1.5, 10.0), 5.0))
        plt.title(f"Swing/pitch/diff details for {hitter_name}. ({league}) ({season})")
        plt.ylim(0, 1000)
        plt.yticks(grid_ticks)
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_pitches), x_legend, size='small')
        plt.plot(swings, label='Swing', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(pitches, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(diffs, label='Diff', color='grey', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        for i, txt in enumerate(swings):
            plt.annotate(f" {txt}", (i, swings[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')


async def setup(client):
    await client.add_cog(Batters(client))
