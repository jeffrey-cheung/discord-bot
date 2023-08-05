import constants
import discord
import io
import json
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
        plt.savefig("graph.png", bbox_inches='tight')

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

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
        fig.write_image("graph.png")

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

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
            plt.savefig("graph.png", bbox_inches='tight')

            with open('graph.png', 'rb') as f:
                file = io.BytesIO(f.read())

            image = discord.File(file, filename='graph.png')

            await ctx.send(file=image)
            os.remove('graph.png')

        else:
            await ctx.send("No pitching data for Pitcher ID " + pitcherID + ". Please try again.")

    @commands.command()
    @guild_only()
    async def deltas(self, ctx, pitcherID, league):
        """!deltas <Pitcher ID> <League> [optional:\"inning\" <#>, \"season\" <#>, \"hr\", \"corners\", \"loaded\", \"empty\", \"risp\", \"2out\", \"1out\", \"0out\", \"steal\"]. Delta histograms."""
        totaldelta = 0
        deltacount = 0
        inningno = 0  # Will only change if they gave "inning <#>" args
        cmd = ""

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcherID}")).json()

        res = len(data)
        if res > 0:
            # Grab player name for chart
            pname = data[0]['pitcherName']
            await ctx.send('You asked to see deltas for {} in {}'.format(pname, league))
            pitch = []  # actual pitch
            delta = []  # pitch deltas
            inning = []  # inning, for x-axis display
            firstbase = []  # occupied or not
            secondbase = []  # occupied or not
            thirdbase = []  # occupied or not
            result = []  # PA result
            outs = []  # how many outs at time of pitch
            season = []

            i = 0
            # Read it all in
            for p in data:
                if p['pitch'] != None:  # there was a pitch (not an auto)
                    pitch.append(p['pitch'])
                    obc = p['obc']
                    if obc == 1 or obc == 4 or obc == 5 or obc == 7:
                        firstbase.append(True)
                    else:
                        firstbase.append(False)
                    if obc == 2 or obc == 4 or obc == 6 or obc == 7:
                        secondbase.append(True)
                    else:
                        secondbase.append(False)
                    if obc == 3 or obc == 5 or obc == 5 or obc == 7:
                        thirdbase.append(True)
                    else:
                        thirdbase.append(False)
                    result.append(p['exactResult'])
                    outs.append(p['outs'])
                    inning.append(p['inning'])
                    season.append(p['season'])
                    i = i + 1

            # now let's calculate deltas
            subtitle = ""
            for p in range(i - 1):
                # see what "cmd" was issued as args[2]
                if cmd.lower() == "hr":  # they want to see deltas after a HR
                    if result[p] == "HR":
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        print(str(pitchDelta))
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "corners":  # they want to see deltas with runners on the corners
                    subtitle = "with runners on the corners."
                    if firstbase[p] == True and secondbase[p] == False and thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "loaded":  # they want to see deltas with bases loaded
                    subtitle = "with the bases loaded."
                    if firstbase[p] == True and secondbase[p] == True and thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "empty":  # they want to see deltas with bases empty
                    subtitle = "with the bases empty."
                    if firstbase[p] == False and secondbase[p] == False and thirdbase[p] == False:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "season" and int(theseason) > 0:  # they specified a season
                    subtitle = "in season " + str(theseason) + " only."
                    if season[p] == int(theseason):
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "risp":  # they want to see deltas with runners in scoring position
                    subtitle = "with runners in scoring position."
                    if secondbase[p] == True or thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "2out":  # they want to see deltas with 2 outs
                    subtitle = "with 2 outs."
                    if outs[p] == 2:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "1out":  # they want to see deltas with 1 out
                    subtitle = "with 1 out."
                    if outs[p] == 1:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "0out":  # they want to see deltas with 0 outs
                    subtitle = "with runners nobody out."
                    if outs[p] == 0:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "steal":  # they want to see deltas after a steal
                    subtitle = "after a steal"
                    if result[p] == "Steal 2B" or result[p] == "Steal 3B":
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "inning" and int(inningno) > 0:  # arg[3] = inning number
                    subtitle = "in inning # " + inningno + "."
                    if (inning[p] == "T" + str(inningno) or inning[p] == "B" + str(inningno)) and (
                            inning[p + 1] == "T" + str(inningno) or inning[p + 1] == "B" + str(
                            inningno)):  # only the same inning
                        beforePitch = pitch[p]
                        afterPitch = pitch[p + 1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                else:  # they didn't specify anything, so get them all
                    subtitle = "(all situations)"
                    beforePitch = pitch[p]
                    afterPitch = pitch[p + 1]
                    pitchDelta = abs(beforePitch - afterPitch)
                    if pitchDelta > 500:
                        pitchDelta = 1000 - pitchDelta
                    delta.append(pitchDelta)
                    totaldelta = totaldelta + pitchDelta
                    deltacount = deltacount + 1

            if deltacount == 0:
                nonefound = "No pitches for " + pname + " in " + league
                if cmd.lower() == "season":
                    nonefound = nonefound + " for S" + str(season)
                nonefound = nonefound + " " + subtitle + "."
                await ctx.send(nonefound)
            avgdelta = round(totaldelta / deltacount)
            title = "Deltas for " + pname + " in " + league + ". " + str(
                len(delta)) + " total deltas " + subtitle + " (avg delta=" + str(avgdelta) + ")"
            x = delta
            num_bins = 10
            fig, ax = plt.subplots()

            # the histogram of the data
            n, bins, patches = ax.hist(x, num_bins, density=False, rwidth=.8)
            xticks = [(bins[idx + 1] + value) / 2 for idx, value in enumerate(bins[:-1])]
            xticks_labels = ["{:.0f}\nto\n{:.0f}".format(value, bins[idx + 1]) for idx, value in
                             enumerate(bins[:-1])]
            plt.xticks(xticks, labels=xticks_labels)

            ax.set_xlabel('Deltas')
            ax.set_title(title)
            # Tweak spacing to prevent clipping of ylabel
            fig.tight_layout()
            # plt.show()

            fig.tight_layout()
            plt.savefig("graph.png", bbox_inches='tight')

            with open('graph.png', 'rb') as f:
                file = io.BytesIO(f.read())

            image = discord.File(file, filename='graph.png')

            await ctx.send(file=image)
            os.remove('graph.png')

        else:
            await ctx.send("No pitching data for Pitcher ID " + pitcherID + ". Please try again.")

    @commands.command()
    @guild_only()
    async def last(self, ctx, league, numberofpitches, situation, pitcherID):
        """!last <league> <# pitches> <\"all\", \"empty\", \"loaded\", \"corners\", \"risp\", \"0out\", \"1out\", \"2out\"> <Pitcher ID>"""
        situationalpitch = []
        result = []
        inning = []
        xlegend = []
        season = []
        session = []
        sitch = ""
        i = 0

        if league.lower() == "milr":
            leaguetitle = "MiLR"
        elif league.lower() == "mlr":
            leaguetitle = "MLR"
        else:
            leaguetitle = " a league I don't know about "

        data = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{pitcherID}")).json()

        pitcher = "Nobody"
        if len(data) > 0:
            for p in data:
                pitcher = p['pitcherName']
                ################
                # BASES EMPTY  #
                ################
                if situation.lower() == "empty":  # and i < numberofpitches:
                    sitch = "with bases empty"
                    if p['obc'] == 0:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #################
                # BASES LOADED  #
                #################
                elif situation.lower() == "loaded":  # and i < numberofpitches:
                    sitch = "with bases loaded"
                    if p['obc'] == 7:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #######################
                # RUNNERS ON CORNERS  #
                #######################
                elif situation.lower() == "corners":  # and i < numberofpitches:
                    sitch = "with runners on the corners"
                    if p['obc'] == 5:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #########
                # RISP  #
                #########
                elif situation.lower() == "risp":  # and i < numberofpitches:
                    sitch = "with runners in scoring position"
                    if p['obc'] > 2:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #################
                # 0 OUTS        #
                #################
                elif situation.lower() == "0out":  # and i < numberofpitches:
                    sitch = "with no outs"
                    if p['outs'] == 0:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #################
                # 1 OUT         #
                #################
                elif situation.lower() == "1out":  # and i < numberofpitches:
                    sitch = "with one out"
                    if p['outs'] == 1:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                #################
                # 2 OUTS        #
                #################
                elif situation.lower() == "2out":  # and i < numberofpitches:
                    sitch = "with two outs"
                    if p['outs'] == 2:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1
                ##########################
                # DEFAULT - no situation #
                ##########################
                elif situation.lower() == "all":  # just show them all
                    sitch = ""
                    if p['pitch'] is not None:
                        situationalpitch.append(p['pitch'])
                        season.append(str(p['season']))
                        session.append(str(p['session']))
                        inning.append(p['inning'])
                        result.append(p['exactResult'])
                        i = i + 1

            situationalpitch.reverse()
            season.reverse()
            session.reverse()
            inning.reverse()
            # partial list of all situational pitches - limited to # pitches in args
            limpitch = []

            j = 0
            if int(numberofpitches) > i:
                numberofpitches = i
            for t in range(int(numberofpitches)):
                if j <= t:
                    xlegend.append("S" + str(season[t]) + "." + str(session[t]) + "\n" + inning[t] + "\nP: " + str(
                        situationalpitch[t]))
                    limpitch.append(situationalpitch[t])
                    j = j + 1
            limpitch.reverse()
            xlegend.reverse()
            title = leaguetitle + ": Last " + str(numberofpitches) + " pitches from " + pitcher + " " + sitch
            data1 = limpitch
            x_axis = xlegend
            fig = plt.figure(figsize=(len(limpitch) / 1.5, 5))  # Creates a new figure
            ax1 = fig.add_subplot(111)  # Plot with: 1 row, 1 column, first subplot.
            ax1.plot(data1, 'bo-', label='Pitch')
            plt.xticks(range(len(data1)), x_axis, size='small')
            ax1.set_ylim(0, 1050)
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            fig.subplots_adjust(top=.92, bottom=0.2)
            fig.tight_layout()
            plt.savefig("graph.png", bbox_inches='tight')

            with open('graph.png', 'rb') as f:
                file = io.BytesIO(f.read())

            image = discord.File(file, filename='graph.png')

            await ctx.send(file=image)
            os.remove('graph.png')
        else:
            await ctx.send("This player has not thrown a pitch in" + leaguetitle + " yet.")

    @commands.command()
    @guild_only()
    async def hmmmm(self, ctx):
        """Helps you think"""
        think_quotes = [
            'Whatever you\'re thinking - I\'M IN!',
            '...yes?',
            'Hmmmm indeed.',
            ':thinking:'
        ]

        await ctx.send(rdm.choice(think_quotes))

    @commands.command()
    @guild_only()
    async def rando(self, ctx):
        """Gives you a random number"""
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
            xlegend = []  # x-axis to display pitch and delta values
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
                xlegend.append("S: " + thes + "\nD: " + thed)
            data1 = swing
            data2 = diff
            x_axis = xlegend
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
