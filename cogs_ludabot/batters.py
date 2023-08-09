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
    async def swing(self,
                    ctx,
                    batter_id: int = commands.parameter(default=None, description="Batter ID"),
                    league: str = commands.parameter(default=None, description="League [MLR, MiLR, FCB, Scrim]"),
                    season: int = commands.parameter(default=None, description="Season #")):
        """
            <batter_id> <league> [optional:season]
            Shows batter swing/pitch/diff sequences
        """
        if batter_id is None or league is None:
            await ctx.send(f"Missing argument(s)")
            return

        data = (requests.get(f"https://www.swing420.com/api/plateappearances/batting/{league}/{batter_id}")).json()

        for p in data[:]:
            if (p['pitch'] is None or p['swing'] is None or p['pitch'] == 0 or p['swing'] == 0) or (season is not None and season != int(p['season'])):
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
            x_legend.append(f"S: {p['swing']}\nD: {p['diff']}")

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
