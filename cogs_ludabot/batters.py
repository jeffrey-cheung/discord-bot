import constants
import discord
import io
import matplotlib.pyplot as plt
import os
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only

pitch_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625, 650, 675, 700, 725, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
delta_ticks = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500]
grid_ticks = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


class Batters(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['swings'])
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
    await client.add_cog(Batters(client))
