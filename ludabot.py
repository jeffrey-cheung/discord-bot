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

for file in listdir('cogs/'):
    if file.endswith('.py'):
        bot.load_extension(f'cogs.{file[:-3]}')

bot.run(os.getenv("TOKEN"))
