import io
import os

import discord
import matplotlib.pyplot as plt
from discord.ext import commands
from discord.ext.commands import guild_only

import constants
from controllers import sheets_reader as sheets

swing_ticks_50 = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
swing_ticks_100 = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
swing_ticks_negative_50 = [-500, -450, -400, -350, -300, -250, -200, -150, -100, -50, 0, 50, 100, 150, 200, 250, 300,
                           350, 400, 450, 500]
red = '#cc0000'
blue = '#4185f4'
green = '#6aa74f'


class Batters(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(brief=".ab", aliases=['ab'])
    @guild_only()
    async def all_ab(self, ctx, *, name=None):
        if name:
            result = await update_batter(ctx, name)
            if result is False:
                return
        await histogram(ctx, "All AB", constants.MLN_BIBLE_BATTER_ASSETS['all_ab'],
                        blue,
                        swing_ticks_50, 1, 1000, 50)

    @commands.command(brief=".lrbfb", aliases=['lrbfb'])
    @guild_only()
    async def last_result_bad_for_batter(self, ctx, *, name=None):
        if name:
            result = await update_batter(ctx, name)
            if result is False:
                return
        await histogram(ctx, "Last Result Bad for Batter",
                        constants.MLN_BIBLE_BATTER_ASSETS['last_result_bad_for_batter'],
                        red,
                        swing_ticks_50, 1, 1000, 50)

    @commands.command(brief=".lrgfb", aliases=['lrgfb'])
    @guild_only()
    async def last_result_good_for_batter(self, ctx, *, name=None):
        if name:
            result = await update_batter(ctx, name)
            if result is False:
                return
        await histogram(ctx, "Last Result Good for Batter",
                        constants.MLN_BIBLE_BATTER_ASSETS['last_result_good_for_batter'],
                        green,
                        swing_ticks_50, 1, 1000, 50)

    @commands.command(brief=".brtbr", aliases=['brtbr'])
    @guild_only()
    async def batter_response_to_bad_result(self, ctx, *, name=None):
        if name:
            result = await update_batter(ctx, name)
            if result is False:
                return
        await histogram(ctx, "Batter Response to Bad Result",
                        constants.MLN_BIBLE_BATTER_ASSETS['batter_response_to_bad_result'],
                        red,
                        swing_ticks_negative_50, -500, 500, 50)

    @commands.command(brief=".brtgr", aliases=['brtgr'])
    @guild_only()
    async def batter_response_to_good_result(self, ctx, *, name=None):
        if name:
            result = await update_batter(ctx, name)
            if result is False:
                return
        await histogram(ctx, "Batter Response to Good Result",
                        constants.MLN_BIBLE_BATTER_ASSETS['batter_response_to_good_result'],
                        green,
                        swing_ticks_negative_50, -500, 500, 50)


async def histogram(ctx, title, page_name, color, x_ticks, x_min_limit, x_max_limit, bin_size):
    sheet_id = constants.MLN_BIBLE_SHEET_ID
    data = sheets.read_sheet(sheet_id, page_name, 'COLUMNS')[0]
    name = sheets.read_sheet(sheet_id, constants.MLN_BIBLE_BATTER_ASSETS['name'], 'COLUMNS')[0][0]
    data = list(filter(None, data))
    data = [x for x in data if x.isdigit()]
    data = list(map(int, data))

    plt.figure(figsize=(10.0, 5.0))
    plt.title(f"{name} - {title}")
    plt.xlim(x_min_limit, x_max_limit)
    plt.xticks(rotation=45)
    plt.xticks(x_ticks)
    values, bins, bars = plt.hist(data, color=color, bins=range(x_min_limit, x_max_limit + bin_size, bin_size),
                                  density=False,
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


async def update_batter(ctx, name):
    sheet_id = constants.MLN_BIBLE_SHEET_ID
    player_list = sheets.read_sheet(constants.MLN_ROSTERS, constants.MLN_ROSTERS_ASSETS['persons'], 'COLUMNS')[0]

    match_list_batter = []
    too_many_results_batter = "Your search for " + name + " returned too many results"
    for i in player_list:
        if name.replace(" ", "").lower() == i.replace(" ", "").lower():
            match_list_batter.clear()
            match_list_batter.append(i)
            break
        elif name.replace(" ", "").lower() in i.replace(" ", "").lower():
            match_list_batter.append(i)
            too_many_results_batter += "\n" + i
    if len(match_list_batter) == 0:
        await ctx.send("No results found for " + name)
        return False
    elif len(match_list_batter) > 1:
        await ctx.send(too_many_results_batter)
        return False
    else:
        sheets.update_sheet(sheet_id, constants.MLN_BIBLE_BATTER_ASSETS['name'], match_list_batter[0])
        return True


async def setup(client):
    await client.add_cog(Batters(client))
