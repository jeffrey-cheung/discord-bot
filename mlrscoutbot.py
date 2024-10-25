import config
import asyncio
import os
import traceback
from datetime import datetime
from os import listdir

import discord
import pytz
from discord.ext import commands

pytz_utc = pytz.timezone('UTC')
pytz_pst = pytz.timezone('America/Los_Angeles')

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!!!", case_insensitive=True, help_command=commands.DefaultHelpCommand(),
                      intents=intents)


@client.event
async def on_ready():
    print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} Logged in as {client.user}")
    for guild in client.guilds:
        print(guild)


async def load_extensions():
    for file in listdir('cogs_mlrscoutbot/'):
        if file.endswith('.py'):
            await client.load_extension(f'cogs_mlrscoutbot.{file[:-3]}')


@client.event
async def on_command_error(ctx, error):
    if ctx.command is not None:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {ctx.command}")
        traceback_lines = traceback.format_exception(type(error), error, error.__traceback__)
        traceback_text = "".join(traceback_lines)
        print(traceback_text)
        await ctx.send("An error occurred while processing your command.")


async def main():
    async with client:
        await load_extensions()
        await client.start(os.getenv("DISCORD_TOKEN_MLRSCOUTBOT"))


asyncio.run(main())
