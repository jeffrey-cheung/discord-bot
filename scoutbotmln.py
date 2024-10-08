import asyncio
import config
import discord
import os
import pytz
from datetime import datetime
from discord.ext import commands
from os import listdir

pytz_utc = pytz.timezone('UTC')
pytz_pst = pytz.timezone('America/Los_Angeles')

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=".", case_insensitive=True, help_command=commands.DefaultHelpCommand(), intents=intents)


@client.event
async def on_ready():
    print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} Logged in as {client.user}")
    for guild in client.guilds:
        print(guild)


async def load_extensions():
    for file in listdir('cogs_scoutbotmln/'):
        if file.endswith('.py'):
            await client.load_extension(f'cogs_scoutbotmln.{file[:-3]}')


async def main():
    async with client:
        await load_extensions()
        await client.start(os.getenv("TOKEN_SCOUTBOTMLN"))


asyncio.run(main())
