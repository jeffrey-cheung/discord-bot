import constants
import discord
import io
import matplotlib.pyplot as plt
import os
import sheets_reader as sheets
from discord.ext import commands
from discord.ext.commands import guild_only

pitch_ticks_50 = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
pitch_ticks_100 = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
pitch_ticks_negative_100 = [-500, -400, -300, -200, -100, 0, 100, 200, 300, 400, 500]
red = '#cc0000'
blue = '#4185f4'
green = '#6aa74f'


class Pitchers(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief=".all_pitches", aliases=['ap'])
    @guild_only()
    async def all_pitches(self, ctx):
        await histogram(ctx, "All Pitches", constants.MLN_BIBLE_PITCHER_ASSETS['all_pitches'],
                        blue,
                        pitch_ticks_50, 1, 1000, 50)

    @commands.command(brief=".last_result_bad_for_pitcher", aliases=['lrbfp'])
    @guild_only()
    async def last_result_bad_for_pitcher(self, ctx):
        await histogram(ctx, "Last Result Bad for Pitcher", constants.MLN_BIBLE_PITCHER_ASSETS['last_result_bad_for_pitcher'],
                        red,
                        pitch_ticks_100, 1, 1000, 100)

    @commands.command(brief=".last_result_good_for_pitcher", aliases=['lrgfp'])
    @guild_only()
    async def last_result_good_for_pitcher(self, ctx):
        await histogram(ctx, "Last Result Good for Pitcher", constants.MLN_BIBLE_PITCHER_ASSETS['last_result_good_for_pitcher'],
                        green,
                        pitch_ticks_100, 1, 1000, 100)

    @commands.command(brief=".next_pitch", aliases=['np'])
    @guild_only()
    async def next_pitch(self, ctx):
        await histogram(ctx, "Next Pitch\nWhen Last Pitch and Last Pitch - 1 Were Within 50 of Current Last Pitch and Last Pitch - 1", constants.MLN_BIBLE_PITCHER_ASSETS['next_pitch'],
                        blue,
                        pitch_ticks_negative_100, -500, 500, 100)

    @commands.command(brief=".pitch_response_to_bad_result", aliases=['prtbr'])
    @guild_only()
    async def pitch_response_to_bad_result(self, ctx):
        await histogram(ctx, "Pitch Response to Bad Result", constants.MLN_BIBLE_PITCHER_ASSETS['pitch_response_to_bad_result'],
                        red,
                        pitch_ticks_negative_100, -500, 500, 100)

    @commands.command(brief=".pitch_response_to_good_result", aliases=['prtgr'])
    @guild_only()
    async def pitch_response_to_good_result(self, ctx):
        await histogram(ctx, "Pitch Response to Good Result", constants.MLN_BIBLE_PITCHER_ASSETS['pitch_response_to_good_result'],
                        green,
                        pitch_ticks_negative_100, -500, 500, 100)


async def histogram(ctx, title, page_name, color, x_ticks, x_min_limit, x_max_limit, bin_size):
    sheet_id = constants.MLN_BIBLE_SHEET_ID
    data = sheets.read_sheet(sheet_id, page_name, 'COLUMNS')[0]
    data = list(filter(None, data))
    data = list(map(int, data))

    plt.figure(figsize=(10.0, 5.0))
    plt.title(title)
    plt.xlim(x_min_limit, x_max_limit)
    plt.xticks(rotation=45)
    plt.xticks(x_ticks)
    values, bins, bars = plt.hist(data, color=color, bins=range(x_min_limit, x_max_limit + bin_size, bin_size), density=False,
                                  rwidth=0.8)
    plt.bar_label(bars)
    plt.tight_layout()
    plt.savefig('graph.png')
    plt.close()

    with open('graph.png', 'rb') as f:
        file = io.BytesIO(f.read())

    image = discord.File(file, filename='graph.png')

    await ctx.send(file=image)
    os.remove('graph.png')


async def setup(client):
    await client.add_cog(Pitchers(client))