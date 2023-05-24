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

bot = commands.Bot(command_prefix="sb.", help_command=commands.DefaultHelpCommand(), intents=intents)


@bot.event
async def on_ready():
    print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} Logged in as {bot.user}")


async def load_extensions():
    for file in listdir('cogs_shadowballbot/'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs_shadowballbot.{file[:-3]}')


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("TOKEN_SHADOWBALL"))


asyncio.run(main())
