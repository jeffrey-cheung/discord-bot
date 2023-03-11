import asyncio
import config
import discord
import os
from discord.ext import commands
from os import listdir

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", help_command=commands.DefaultHelpCommand(), intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


async def load_extensions():
    for file in listdir('cogs/'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs.{file[:-3]}')


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("TOKEN"))


asyncio.run(main())
