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

bot = commands.Bot(command_prefix=("sb.", "SB.", "Sb.", "sB."), case_insensitive=True,
                   help_command=commands.DefaultHelpCommand(), intents=intents)


@bot.event
async def on_ready():
    print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} Logged in as {bot.user}")
    for guild in bot.guilds:
        print(guild)


@bot.event
async def on_command_error(ctx, error):
    if ctx.command is not None:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {ctx.command}")
        traceback_lines = traceback.format_exception(type(error), error, error.__traceback__)
        traceback_text = "".join(traceback_lines)
        print(traceback_text)
        await ctx.send("An error occurred while processing your command.")


async def load_extensions():
    for file in listdir('cogs_mlr_shadowball/'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs_mlr_shadowball.{file[:-3]}')


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("MLR_SHADOWBALL_DISCORD_TOKEN"))


asyncio.run(main())
