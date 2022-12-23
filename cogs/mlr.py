import constants
import discord
import io
import matplotlib.pyplot as plt
import os
import random as rdm
import requests
from discord.ext import commands

HYPE_LIST = constants.HYPE_LIST


class MLR(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def random(self, ctx):
        """Returns random number between 1 and 1000"""
        await ctx.send(rdm.randint(1, 1000))

    @commands.command()
    async def pitches(self, ctx, league, player_id, number_of_pitches=50):
        """Returns line chart of recent pitches"""
        player = (requests.get("https://www.swing420.com/api/players/id/" + player_id)).json()
        response = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{player_id}")).json()

        list_of_pitches = []
        for x in response:
            if (x['pitch'] != 0) & (x['swing'] != 0) & (x['session'] != 0):
                list_of_pitches.append(x['pitch'])
        list_of_pitches = list_of_pitches[-number_of_pitches:]

        number_of_pitches = len(list_of_pitches)
        list_of_numbers = list(range(1, number_of_pitches + 1))

        plt.title(player['playerName'] + ' last ' + str(number_of_pitches) + " pitches in " + str(league))
        plt.ylim(0, 1000)
        plt.xlim(0, number_of_pitches + 1)
        plt.grid(True)
        plt.plot(list_of_numbers, list_of_pitches, marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    async def hype(self, ctx):
        """Returns random hype gif"""
        await ctx.send(rdm.choice(HYPE_LIST))


def setup(bot):
    bot.add_cog(MLR(bot))
