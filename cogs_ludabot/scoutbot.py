import constants
import discord
import io
import matplotlib.pyplot as plt
import os
import plotly.graph_objects as go
import random as rdm
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only


class ScoutBot(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @guild_only()
    async def react(self,
                    ctx,
                    pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    lower_pitch: int = commands.parameter(default=None, description="Lower Pitch"),
                    upper_pitch: int = commands.parameter(default=None, description="optional:Upper Pitch")):
        """
            <pitcher_id> <league> <lower_pitch> [optional:upper_pitch]
            Reactions before & after pitching a certain range
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
        for i, p in enumerate(data):
            pitcher_name = p['pitcherName']
            if p['pitch'] is not None and p['swing'] is not None and p['pitch'] != 0 and p['swing'] != 0:  # just skip the non/auto resulted pitches
                pitch.append(p['pitch'])
                season.append(p['season'])
                session.append(p['session'])
                inning.append(p['inning'])
            else:
                data.pop(i)

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
                    legend += f"\nM: {pitch[p]}"

                    after.append(pitch[p + 1])
                    legend += f"\nA: {pitch[p + 1]}"

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
        plt.yticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(matches_count), x_legend, size='small')
        plt.plot(after, label='After', color='black', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(match, label='Match', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7, alpha=0.4)
        plt.plot(before, label='Before', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7, alpha=0.4)
        plt.legend()
        plt.tight_layout()
        plt.savefig("graph.png", bbox_inches='tight')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @guild_only()
    async def hm(self,
                 ctx,
                 pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                 league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                 situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]")):
        """
            <pitcher_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]
            Pitcher heatmap

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
        result = []
        inning = []
        pitch = []
        matches_count = 0
        pitcher = ""
        for i, p in enumerate(data):
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:  # just skip the non/auto resulted pitches
                data.pop(i)

        for i, p in enumerate(data):
            pitcher = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            if i > 0:
                same_game = data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1]['session']
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
            result.append(p['exactResult'])  # result (ie: 1B, 2B, HR, RGO, etc.)
            inning.append(p['inning'])  # inning (T# for top of inning, B# for bottom of inning)
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
        fig = go.Figure()
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
        fig.update_layout(annotations=annotations)
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
        plt.xticks([0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625, 650, 675, 700, 725, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000])
        values, bins, bars = plt.hist(pitch, bins=range(1, 1025, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @guild_only()
    async def chart(self,
                    ctx,
                    pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    season: int = commands.parameter(default=None, description="Season #")):
        """
            <pitcher_id> <league> [optional:season]
            Shows pitcher pitch/delta sequences
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        totaldelta = 0
        deltacount = 0
        inningno = 0

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        res = len(data)
        if res > 0:
            # Grab player name for chart
            pname = data[0]['pitcherName']
            await ctx.send(f"You asked to see the pitch/delta details for {pname}. ({league})")
            pitch = []  # actual pitch
            swing = []  # actual swing
            diff = []  # actual diff
            pitchseq = []  # x-axis zero-indexed
            pitchno = []  # x-axis 1-indexed (to display in human friendly on the graph)
            delta = []  # pitch deltas
            x_legend = []  # x-axis to display pitch and delta values
            inning = []  # inning, for x-axis display
            seasons = []  # season for x-axis display
            sessions = []  # session for x-axis display
            delta.append(0)
            i = 0

            # Read it all in
            for p in data:
                if p['pitch'] is not None:  # there was a pitch (not an auto)
                    if season is not None:  # they specified a season
                        if p['season'] == int(season):  # so limit to that season only
                            pitch.append(p['pitch'])
                            swing.append(p['swing'])
                            diff.append(p['diff'])
                            inning.append(p['inning'])
                            seasons.append(p['season'])
                            sessions.append(p['session'])
                            i = i + 1
                    else:  # they didn't specify a season, so get them all
                        pitch.append(p['pitch'])
                        swing.append(p['swing'])
                        diff.append(p['diff'])
                        inning.append(p['inning'])
                        seasons.append(p['season'])
                        sessions.append(p['session'])
                        i = i + 1

            # they want to limit to a specific inning for the given season.
            # This requires a different graph, with overlayed game sequences,
            # like the old Excel pivot chart
            if int(inningno) > 0:
                limgame = 0
                for t in pitch:
                    if inning[limgame] == "B" + str(inningno) or inning[limgame] == "T" + str(inningno):
                        pass  # need to flesh this out
                    limgame = limgame + 1

            # populate with the number of PAs/pitches
            for s in range(i):
                pitchseq.append(s)
                pitchno.append(s + 1)  # for x-axis of the chart

            # calculate diffs
            for d in range(
                    len(pitch)):  # range -> just the pitches picked up from the opposing pitcher (does not include autos)
                if (d > 0):
                    pitchd = abs(pitch[d] - pitch[d - 1])
                    if pitchd > 500:
                        pitchd = 1000 - pitchd
                    delta.append(pitchd)
                    totaldelta = totaldelta + pitchd
                    deltacount = deltacount + 1

            if deltacount == 0:
                nonefound = "No pitches for " + pname + " in " + league
                nonefound = nonefound + "."
                await ctx.send(nonefound)
            avgdelta = round(totaldelta / deltacount)
            title = "Pitch sequence for " + pname + " in " + league + ". " + str(i) + " pitches" + " (avg delta=" + str(
                avgdelta) + ")"
            if season is not None:
                title = title + " (S" + str(season) + " only)"
            for p in range(len(swing)):
                if pitch[p] < 10:
                    thep = "   " + str(pitch[p])
                elif pitch[p] < 100:
                    thep = " " + str(pitch[p])
                else:
                    thep = str(pitch[p])

                if delta[p] < 10:
                    thed = "   " + str(delta[p])
                elif delta[p] < 100:
                    thed = " " + str(delta[p])
                else:
                    thed = str(delta[p])
                x_legend.append("S" + str(seasons[p]) + "." + str(sessions[p]) + "   \n" + inning[
                    p] + "     \nP: " + thep + "\nD: " + thed)
            data1 = pitch
            data2 = delta
            x_axis = x_legend

            plt.figure(figsize=(max(len(pitch) / 1.5, 10.0), 5.0))  # Creates a new figure
            plt.title(title)
            plt.ylim(0, 1000)
            plt.yticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
            plt.grid(axis='y', alpha=0.7)
            plt.xticks(range(len(data2)), x_axis, size='small')
            plt.plot(data1, label='Pitch', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7)
            plt.plot(data2, label='Delta', color='black', marker='o', linestyle='dashed', linewidth=1, markersize=7)
            plt.legend()
            plt.tight_layout()
            plt.savefig("graph.png", bbox_inches='tight')
            plt.close()

            with open('graph.png', 'rb') as f:
                file = io.BytesIO(f.read())

            image = discord.File(file, filename='graph.png')

            await ctx.send(file=image)
            os.remove('graph.png')

        else:
            await ctx.send(f"No pitching data for Pitcher ID {pitcher_id}. Please try again.")

    @commands.command()
    @guild_only()
    async def deltas(self,
                     ctx,
                     pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                     league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                     situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]")):
        """
            <pitcher_id> <league> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstinning]
            Pitcher delta histogram

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

        deltas = []
        matches_count = 0
        pitcher = ""
        for i, p in enumerate(data):
            if p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0:
                data.pop(i)

        for i, p in enumerate(data):
            pitcher = p['pitcherName']
            outs = int(p['outs'])
            obc = int(p['obc'])
            same_game = False
            previous_result = None
            previous_pitch = None
            if i > 0:
                same_game = data[i]['season'] == data[i - 1]['season'] and data[i]['session'] == data[i - 1][
                    'session']
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

        await ctx.send(f"You asked for pitch deltas for {pitcher}. ({league}) ({situation})")

        title = f"Pitch deltas for {pitcher}. ({league}) ({situation}) ({matches_count} deltas)"

        plt.figure(figsize=(10.0, 5.0))
        plt.title(title)
        plt.xlim(0, 500)
        plt.xticks(rotation=90)
        plt.xticks(
            [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500])
        values, bins, bars = plt.hist(deltas, bins=range(0, 525, 25), density=False, rwidth=0.8)
        plt.bar_label(bars)
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @guild_only()
    async def last(self,
                   ctx,
                   pitcher_id: int = commands.parameter(default=None, description="Pitcher ID"),
                   league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                   number_of_pitches: int = commands.parameter(default=30, description="Number of Pitches"),
                   situation: str = commands.parameter(default="all", description="optional:Situation [all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]")):
        """
            <pitcher_id> <league> <number_of_pitches> [optional:situation:all, empty, onbase, risp, corners, loaded, dp, hit, out, hr, 3b, 2b, 1b, bb, 0out, 1out, 2out, firstgame, firstinning]
        """
        if pitcher_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcher_id}")).json()

        x_legend = []
        list_of_pitches = []
        list_of_swings = []
        pitcher_name = ""
        for p in data:
            pitcher_name = p['pitcherName']
            if p['pitch'] is not None and p['swing'] is not None and p['pitch'] != 0 and p['swing'] != 0:
                list_of_pitches.append(p['pitch'])
                list_of_swings.append(p['swing'])
                x_legend.append(f"S{p['season']}.{p['session']}\n{p['inning']}\nP: {p['pitch']}")

        x_legend = x_legend[-number_of_pitches:]
        list_of_pitches = list_of_pitches[-number_of_pitches:]
        list_of_swings = list_of_swings[-number_of_pitches:]
        number_of_pitches = len(list_of_pitches)

        if number_of_pitches == 0:
            await ctx.send(f"No matches")
            return

        await ctx.send(f"You asked for last {number_of_pitches} pitches for {pitcher_name}. ({league})")

        plt.figure(figsize=(max(number_of_pitches / 1.5, 10.0), 5.0))
        plt.title(f"Last {number_of_pitches} pitches for {pitcher_name}. ({league})")
        plt.ylim(0, 1000)
        plt.yticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        plt.grid(axis='y', alpha=0.7)
        plt.xticks(range(number_of_pitches), x_legend, size='small')
        plt.plot(list_of_pitches, label='Pitch', color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(list_of_swings, label='Swing', color='blue', marker='o', linestyle='dashed', linewidth=1, markersize=7, alpha=0.4)
        for i, txt in enumerate(list_of_pitches):
            plt.annotate(f" {txt}", (i, list_of_pitches[i]))
        plt.legend()
        plt.tight_layout()
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @guild_only()
    async def hmmmm(self, ctx):
        """
            Helps you think
        """
        think_quotes = [
            "Whatever you're thinking - I'M IN!",
            "...yes?",
            "Hmmmm indeed.",
            ":thinking:"
        ]

        await ctx.send(rdm.choice(think_quotes))

    @commands.command()
    @guild_only()
    async def rando(self, ctx):
        """
            Gives you a random number
        """
        await ctx.send(rdm.randint(1, 1000))

    @commands.command()
    @guild_only()
    async def swing(self, ctx, playerID, league, season=None):
        """!swing <Player ID> <League> shows swing/diff sequences"""
        totaldiff = 0
        diffcount = 0

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/batting/{league}/{playerID}")).json()

        res = len(data)
        if res > 0:
            # Grab player name for chart
            bname = data[0]['hitterName']
            await ctx.send('You asked to see the swing/diff details for {} in {}'.format(bname, league))
            swing = []  # actual swing
            diff = []  # swing diffs
            x_legend = []  # x-axis to display pitch and delta values
            i = 0
            for p in data:
                if p['pitch'] is not None:  # there was a pitch (not an auto)
                    if season is not None:  # they specified a season
                        if p['season'] == int(season):  # so limit to that season only
                            swing.append(p['swing'])
                            diff.append(p['diff'])
                            totaldiff = totaldiff + p['diff']
                            diffcount = diffcount + 1
                            i = i + 1
                    else:  # they didn't specify a season, so get them all
                        swing.append(p['swing'])
                        diff.append(p['diff'])
                        totaldiff = totaldiff + p['diff']
                        diffcount = diffcount + 1
                        i = i + 1
            avgdiff = round(totaldiff / i)
            title = "Swing history for " + bname + " in " + league + ": " + str(
                i) + " swings " + " (avg diff=" + str(avgdiff) + ")"
            if season is not None:
                title = title + " (S" + str(season) + " only)"
            for p in range(len(swing)):
                if swing[p] < 10:
                    thes = "   " + str(swing[p])
                elif swing[p] < 100:
                    thes = " " + str(swing[p])
                else:
                    thes = str(swing[p])

                if diff[p] < 10:
                    thed = "   " + str(diff[p])
                elif diff[p] < 100:
                    thed = " " + str(diff[p])
                else:
                    thed = str(diff[p])
                x_legend.append("S: " + thes + "\nD: " + thed)
            data1 = swing
            data2 = diff
            x_axis = x_legend
            fig = plt.figure(figsize=(len(swing) / 1.5, 5))  # Creates a new figure

            ax1 = fig.add_subplot(111)  # Plot with: 1 row, 1 column, first subplot.
            pitch = ax1.plot(data1, 'bo-', label='Swing')  # no need for str(x_axis)
            delta = ax1.plot(data2, 'k--', label='Diff')
            plt.xticks(range(len(data2)), x_axis, size='small')
            ax1.set_ylim(0, 1050)

            # Assigning labels
            lines = pitch + delta  # +line3
            labels = [l.get_label() for l in lines]
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            ## GRIDLINES FOR EASIER READING
            plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            ## END GRIDLINES
            fig.subplots_adjust(top=.92, bottom=0.2)
            fig.tight_layout()
            plt.savefig("graph.png", bbox_inches='tight')

            with open('graph.png', 'rb') as f:
                file = io.BytesIO(f.read())

            image = discord.File(file, filename='graph.png')

            await ctx.send(file=image)
            os.remove('graph.png')
        else:
            await ctx.send("No swing history for Player ID " + playerID + ". Please try again.")


async def setup(client):
    await client.add_cog(ScoutBot(client))
