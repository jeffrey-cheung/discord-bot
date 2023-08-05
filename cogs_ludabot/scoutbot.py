import urllib
import urllib.request, json, re, requests
import plotly.graph_objects as go
import constants
import discord
import io
import json
import matplotlib.pyplot as plt
import os
import random as rdm
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only

colors = json.loads(constants.MLR_COLORS)


class ScoutBot(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @guild_only()
    async def react(self, ctx, pitcherID, league, lowerpitch, upperpitch):
        """[playerId] [league] [lowerPitch] [upperPitch]"""
        lower = int(lowerpitch)
        xlegend = []
        pitch = []  # all non-autoed pitches
        inning = []  # all non-autoed innings
        session = []  # all non-autoed sessions
        result = []  # all non-autoed results
        season = []  # all non-autoed seasons
        obc = []  # bases occupied
        i = 0
        ii = 0

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcherID}")).json()

        # get pitcher name and read it all in
        for p in data:
            pitcher = p['pitcherName']
            if p['pitch'] is not None:  # just skip the non/auto resulted pitches
                pitch.append(p['pitch'])
                inning.append(p['inning'])
                session.append(p['session'])
                result.append(p['oldResult'])
                season.append(p['season'])
                obc.append(['obc'])

        before = []  # pitch before the match
        match = []  # the match
        after = []  # pitch after the match
        # now let's go through and look for matches
        for p in range(len(pitch) - 1):
            lower = int(lowerpitch)
            upper = int(upperpitch)
            if upper < lower:
                switch = upper
                upper = lower
                lower = switch
            if upper >= int(pitch[p]) >= lower:  # it's a match for a range
                legend = "S" + str(season[p]) + "." + str(session[p]) + "\n" + str(inning[p])
                if p > 0:
                    before.append(pitch[p - 1])
                    legend = legend + "\nB: " + str(pitch[p - 1])
                else:
                    before.append(None)
                    legend = legend + "\nB: "
                match.append(pitch[p])
                legend = legend + "\nM: " + str(pitch[p])
                if p < len(pitch) - 1:
                    after.append(pitch[p + 1])
                    legend = legend + "\nA: " + str(pitch[p + 1])
                else:
                    after.append(None)
                    legend = legend + "\nA: "
                i = i + 1  # count matches
                xlegend.append(legend)

            ii = ii + 1  # count all pitches

        # Quick check to report reactions
        ranger = str(lower)
        ranger = ranger + " - " + str(upper)
        await ctx.send("You asked for pitches from " + pitcher + " before & after pitching " + ranger)

        title = "Pitches from " + pitcher + " before & after pitching " + ranger + " (" + str(i) + " matches)"
        data1 = match
        data2 = after
        data3 = before
        x_axis = xlegend
        fig = plt.figure(figsize=(i / 1.5, 5))  # Creates a new figure
        ax1 = fig.add_subplot(111)  # Plot with: 1 row, 1 column, first subplot.
        ax1.plot(data1, 'bo-', label='Match')  # no need for str(x_axis)
        ax1.plot(data2, 'k--', label='After')
        ax1.plot(data3, 'r--', label='Before')
        plt.xticks(range(i), x_axis, size='small')
        ax1.set_ylim(0, 1050)
        plt.setp(ax1.get_xticklabels(), visible=True)
        plt.suptitle(title, y=1.0, fontsize=17)
        plt.legend()
        # GRIDLINES FOR EASIER READING
        plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        # END GRIDLINES
        fig.subplots_adjust(top=.92, bottom=0.2)
        fig.tight_layout()
        plt.savefig("images/beforeafter.png", bbox_inches='tight')

        with open('images/beforeafter.png', 'rb') as fp:
            f = discord.File(fp, filename='images/beforeafter.png')
        await ctx.send(file=f)

    @commands.command()
    @guild_only()
    async def hm(self, ctx, league, pitcherID):
        """[league] [playerId] [optional:hr, loaded, empty, corners, risp, inning #, 2out, 1out, 0out]. MLR heatmaps."""
        if league.lower() == "milr":
            leaguetitle = "MiLR"
        else:
            leaguetitle = "MLR"

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcherID}")).json()

        validpitches = []
        y = []
        x = []
        result = []
        inning = []
        first = []
        second = []
        third = []
        outs = []
        i = 0
        pitcher = "Nobody"
        for p in data:
            pitcher = p['pitcherName']
            if p['pitch'] is not None:
                thepitch = int(p['pitch'])
                y.append(int(thepitch / 100) * 100)  # 100s on the y axis of heatmap
                x.append(int(thepitch % 100))  # 10s/1s on the x axis of heatmap
                result.append(p['exactResult'])  # result (ie: 1B, 2B, HR, RGO, etc.)
                inning.append(p['inning'])  # inning (T# for top of inning, B# for bottom of inning)
                obc = p['obc']
                if obc == 1 or obc == 4 or obc == 5 or obc == 7:
                    first.append(True)
                else:
                    first.append(False)
                if obc == 2 or obc == 4 or obc == 6 or obc == 7:
                    second.append(True)
                else:
                    second.append(False)
                if obc == 3 or obc == 5 or obc == 5 or obc == 7:
                    third.append(True)
                else:
                    third.append(False)
                outs.append(p['outs'])  # Number of outs at time of pitch
                validpitches.append(i)
                i = i + 1

        # Defaults for graph (if no arguments given... ie: all pitches, wide open)
        title = leaguetitle + " heatmap for " + pitcher + " (all " + str(i) + " pitches)"

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
            xbins=dict(start=0, end=99, size=25),
            autobiny=False,
            ybins=dict(start=0, end=1000, size=100),
            x=x,
            y=y
        ))
        fig.update_xaxes(dtick=25)
        fig.update_yaxes(dtick=100)
        fig.update_traces(colorbar=dict(title="Num pitches"))
        fig.update_layout(annotations=annotations)
        fig.write_image("images/heatmap.png")
        with open('images/heatmap.png', 'rb') as fp:
            f = discord.File(fp, filename='images/heatmap.png')
        await ctx.send(file=f)

    @commands.command()
    @guild_only()
    async def chart(self, ctx, pitcherID, league, season=None):
        """!chart <Pitcher ID> <League> <Season #> [option: \"inning\" <#>] shows pitch/delta sequences."""
        totaldelta = 0
        deltacount = 0
        inningno = 0

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcherID}")).json()

        res = len(data)
        if res > 0:
            # Grab player name for chart
            pname = data[0]['pitcherName']
            await ctx.send(
                'You asked to see the pitch/delta details for {} ({})'.format(pname, league))
            pitch = []  # actual pitch
            swing = []  # actual swing
            diff = []  # actual diff
            pitchseq = []  # x-axis zero-indexed
            pitchno = []  # x-axis 1-indexed (to display in human friendly on the graph)
            delta = []  # pitch deltas
            xlegend = []  # x-axis to display pitch and delta values
            inning = []  # inning, for x-axis display
            seasons = []  # season for x-axis display
            sessions = []  # session for x-axis display
            delta.append(0)
            i = 0

            # Read it all in
            for p in data:
                if p['pitch'] != None:  # there was a pitch (not an auto)
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
                if len(args) == 3:
                    nonefound = nonefound + " for S" + str(season)
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
                xlegend.append("S" + str(seasons[p]) + "." + str(sessions[p]) + "   \n" + inning[
                    p] + "     \nP: " + thep + "\nD: " + thed)
            data1 = pitch
            data2 = delta
            x_axis = xlegend
            fig = plt.figure(figsize=(len(pitch) / 1.5, 5))  # Creates a new figure

            ax1 = fig.add_subplot(111)  # Plot with: 1 row, 1 column, first subplot.
            pitch = ax1.plot(data1, 'bo-', label='Pitch')  # no need for str(x_axis)
            delta = ax1.plot(data2, 'k--', label='Delta')
            plt.xticks(range(len(data2)), x_axis, size='small')
            ax1.set_ylim(0, 1050)

            # Assigning labels
            lines = pitch + delta
            labels = [l.get_label() for l in lines]
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            fig.subplots_adjust(top=.92, bottom=0.2)
            fig.tight_layout()
            plt.savefig("images/plog.png", bbox_inches='tight')
            with open('images/plog.png', 'rb') as fp:
                f = discord.File(fp, filename='images/plog.png')
                await ctx.send(file=f)

        else:
            await ctx.send("No pitching data for Pitcher ID " + pitcherID + ". Please try again.")

async def setup(client):
    await client.add_cog(ScoutBot(client))
