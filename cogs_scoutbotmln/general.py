import constants
import discord
import json
import random as rdm
import requests
import sys
from discord.ext import commands
from discord.ext.commands import guild_only


class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief=".hmmmm Helps you think", aliases=['hmmm', 'hmmmmm'])
    @guild_only()
    async def hmmmm(self, ctx):
        """
            Helps you think

            .hmmmm
        """
        think_quotes = [
            "Whatever you're thinking - I'M IN!",
            "...yes?",
            "Hmmmm indeed.",
            ":thinking:"
        ]

        await ctx.send(rdm.choice(think_quotes))

    @commands.command(brief=".ping Returns pong if bot is up")
    @guild_only()
    async def ping(self, ctx):
        """
            Returns pong if bot is up

            .ping
        """

        await ctx.send("pong")

    @commands.command(brief=".rando Gives you a random number", aliases=['random'])
    @guild_only()
    async def rando(self, ctx):
        """
            Gives you a random number

            .rando
        """
        await ctx.send(rdm.randint(1, 1000))

async def setup(client):
    await client.add_cog(General(client))
