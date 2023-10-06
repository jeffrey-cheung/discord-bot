import constants
import discord
import json
import random as rdm
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only

colors = json.loads(constants.MLR_COLORS)


class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief="!doc Gives you link to the scout bot documentation", aliases=['doc', 'document'])
    @guild_only()
    async def documentation(self, ctx):
        """
            Gives you link to the scout bot documentation

            !doc
        """
        await ctx.send("https://docs.google.com/document/d/1dOT0iBuqpyH0IlS3OBsWLC5J0ZcagCK47WgeBSqpweg/edit?usp=sharing")

    @commands.command(brief="!hmmmm Helps you think", aliases=['hmmm', 'hmmmmm'])
    @guild_only()
    async def hmmmm(self, ctx):
        """
            Helps you think

            !hmmmm
        """
        think_quotes = [
            "Whatever you're thinking - I'M IN!",
            "...yes?",
            "Hmmmm indeed.",
            ":thinking:"
        ]

        await ctx.send(rdm.choice(think_quotes))

    @commands.command(brief="!ping Returns pong if bot is up")
    @guild_only()
    async def ping(self, ctx):
        """
            Returns pong if bot is up

            !ping
        """

        await ctx.send("pong")

    @commands.command(brief="!player <name>")
    @guild_only()
    async def player(self, ctx, *, name: str = commands.parameter(default=None, description="Player name")):
        """
            Shows player information

            !player <name>
        """
        playerList = (requests.get("https://www.rslashfakebaseball.com/api/players")).json()
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
            embed.add_field(name="Hand Bonus", value=player['pitchBonus'], inline=True)
            embed.add_field(name="Discord", value=player['discordName'], inline=True)
            embed.add_field(name="Reddit", value=player['redditName'], inline=True)
            embed.add_field(name="Player ID", value=player['playerID'], inline=True)

            await ctx.send(embed=embed)
        elif len(matchList) == 0:
            await ctx.send("No results found for " + name)
        else:
            await ctx.send(tooManyResults)

    @commands.command(brief="!rando Gives you a random number", aliases=['random'])
    @guild_only()
    async def rando(self, ctx):
        """
            Gives you a random number

            !rando
        """
        await ctx.send(rdm.randint(1, 1000))

async def setup(client):
    await client.add_cog(General(client))
