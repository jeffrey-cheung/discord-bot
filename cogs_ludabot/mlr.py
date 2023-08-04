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


class MLR(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @guild_only()
    async def random(self, ctx):
        """Returns random number between 1 and 1000"""
        await ctx.send(rdm.randint(1, 1000))

    @commands.command()
    @guild_only()
    async def pitches(self, ctx, league, player_id, number_of_pitches=None):
        """[league] [playerId] [optional:numberOfPitches]"""
        if number_of_pitches is None:
            number_of_pitches = 50

        player = (requests.get("https://www.swing420.com/api/players/id/" + player_id)).json()
        response = (
            requests.get(f"https://www.swing420.com/api/plateappearances/pitching/{league}/{player_id}")).json()

        list_of_pitches = []
        list_of_swings = []
        current_season = -1
        current_game = -1
        for x in response:
            if (x['pitch'] != 0) & (x['swing'] != 0):
                if number_of_pitches == "current":
                    if int(x['season']) > int(current_season):
                        list_of_pitches = []
                        list_of_swings = []
                        current_season = x['season']
                        current_game = x['gameID']
                    if int(x['gameID']) > int(current_game):
                        list_of_pitches = []
                        list_of_swings = []
                        current_game = x['gameID']
                    if int(x['season']) == int(current_season) and int(x['gameID']) == int(current_game):
                        list_of_pitches.append(x['pitch'])
                        list_of_swings.append(x['swing'])
                else:
                    list_of_pitches.append(x['pitch'])
                    list_of_swings.append(x['swing'])

        if number_of_pitches != "current":
            number_of_pitches = int(number_of_pitches)
            list_of_pitches = list_of_pitches[-number_of_pitches:]
            list_of_swings = list_of_swings[-number_of_pitches:]

        number_of_pitches = len(list_of_pitches)
        list_of_numbers = list(range(1, number_of_pitches + 1))

        plt.figure(figsize=(10.0, 5.0))
        if current_game != -1:
            plt.title(player['playerName'] + " current game pitches in " + str(league))
        else:
            plt.title(player['playerName'] + " last " + str(number_of_pitches) + " pitches in " + str(league))
        plt.ylim(0, 1000)
        plt.xlim(0, number_of_pitches + 1)
        plt.yticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        plt.grid(axis='y', alpha=0.7)
        plt.plot(list_of_numbers, list_of_pitches, color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(list_of_numbers, list_of_swings, marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.legend(['Pitch', 'Swing'])
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @guild_only()
    async def swings(self, ctx, league, player_id, number_of_swings=50):
        """[league] [playerId] [optional:numberOfSwings]"""
        player = (requests.get("https://www.swing420.com/api/players/id/" + player_id)).json()
        response = (
            requests.get(f"https://www.swing420.com/api/plateappearances/batting/{league}/{player_id}")).json()

        list_of_pitches = []
        list_of_swings = []
        for x in response:
            if (x['pitch'] != 0) & (x['swing'] != 0):
                list_of_pitches.append(x['pitch'])
                list_of_swings.append(x['swing'])
        list_of_pitches = list_of_pitches[-number_of_swings:]
        list_of_swings = list_of_swings[-number_of_swings:]

        number_of_swings = len(list_of_swings)
        list_of_numbers = list(range(1, number_of_swings + 1))

        plt.figure(figsize=(10.0, 5.0))
        plt.title(player['playerName'] + ' last ' + str(number_of_swings) + " swings in " + str(league))
        plt.ylim(0, 1000)
        plt.xlim(0, number_of_swings + 1)
        plt.yticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        plt.grid(axis='y', alpha=0.7)
        plt.plot(list_of_numbers, list_of_pitches, color='red', marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.plot(list_of_numbers, list_of_swings, marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.legend(['Pitch', 'Swing'])
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await ctx.send(file=image)
        os.remove('graph.png')

    @commands.command()
    @commands.is_owner()
    @guild_only()
    async def player(self, ctx, *, name):
        """[name]"""
        playerList = (requests.get("https://www.swing420.com/api/players")).json()
        matchList = []
        tooManyResults = "Your search for " + name + " returned too many results"

        for i in playerList:
            if name.replace(" ", "").lower() in i['playerName'].replace(" ", "").lower():
                matchList.append(i)
                tooManyResults += "\n" + i['playerName']

        if len(matchList) == 1:
            player = matchList[0]
            team_abbreviation = player['Team']
            position = player['priPos']
            if player['secPos'] != "":
                position += "/" + player['secPos']
            if player['tertPos'] != "":
                position += "/" + player['tertPos']

            team_color = int(colors.get(team_abbreviation, colors.get("DEFAULT")), 16)
            embed = discord.Embed(color=team_color)

            embed.set_author(name=player['playerName'])

            embed.add_field(name="Team", value=team_abbreviation, inline=True)
            embed.add_field(name="Hand", value=player['hand'], inline=True)
            embed.add_field(name="Position", value=position, inline=True)
            embed.add_field(name="Batting Type", value=player['batType'], inline=True)
            embed.add_field(name="Pitching Type", value=player['pitchType'], inline=True)
            embed.add_field(name="", value="", inline=True)
            embed.add_field(name="Discord", value=player['discordName'], inline=True)
            embed.add_field(name="Reddit", value=player['redditName'], inline=True)
            embed.add_field(name="Player ID", value=player['playerID'], inline=True)

            await ctx.send(embed=embed)
        elif len(matchList) == 0:
            await ctx.send("No results found for " + name)
        else:
            await ctx.send(tooManyResults)


async def setup(client):
    await client.add_cog(MLR(client))
