import random as rdm

from discord.ext import commands
from discord.ext.commands import guild_only

import constants
from controllers import sheets_reader as sheets


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

    @commands.command(brief='.ranges Calculates ranges for batter and pitcher')
    async def ranges(self, ctx, *, players):
        players = players.replace(' ;', ';')
        players = players.replace('; ', ';')
        players = players.split(';')
        if len(players) == 1:
            await ctx.send(
                'Improper format. Please use `.ranges <battername>; <pitchername>`')
            return

        batter = players[0]
        pitcher = players[1]
        player_list = sheets.read_sheet(constants.MLN_ROSTERS, constants.MLN_ROSTERS_ASSETS['persons'], 'COLUMNS')[0]

        match_list_batter = []
        too_many_results_batter = "Your search for " + batter + " returned too many results"
        for i in player_list:
            if batter.replace(" ", "").lower() == i.replace(" ", "").lower():
                match_list_batter.clear()
                match_list_batter.append(i)
                break
            elif batter.replace(" ", "").lower() in i.replace(" ", "").lower():
                match_list_batter.append(i)
                too_many_results_batter += "\n" + i
        if len(match_list_batter) == 0:
            await ctx.send("No results found for " + batter)
            return
        elif len(match_list_batter) > 1:
            await ctx.send(too_many_results_batter)
            return

        match_list_pitcher = []
        too_many_results_pitcher = "Your search for " + pitcher + " returned too many results"
        for i in player_list:
            if pitcher.replace(" ", "").lower() == i.replace(" ", "").lower():
                match_list_pitcher.clear()
                match_list_pitcher.append(i)
                break
            elif pitcher.replace(" ", "").lower() in i.replace(" ", "").lower():
                match_list_pitcher.append(i)
                too_many_results_pitcher += "\n" + i
        if len(match_list_pitcher) == 0:
            await ctx.send("No results found for " + pitcher)
            return
        elif len(match_list_pitcher) > 1:
            await ctx.send(too_many_results_pitcher)
            return

        message = await ctx.send("Calculating...")
        batter = match_list_batter[0]
        pitcher = match_list_pitcher[0]

        batch_update_data = {
            f"{constants.MLN_CALCULATOR_ASSETS['pitcher']}": pitcher,
            f"{constants.MLN_CALCULATOR_ASSETS['batter']}": batter
        }
        sheets.batch_update_sheet(constants.MLN_CALCULATOR, batch_update_data)

        matchup_info = sheets.read_sheet(constants.MLN_CALCULATOR, constants.MLN_CALCULATOR_ASSETS['matchup_info'])
        pitcher_info = matchup_info[0]
        batter_info = matchup_info[1]
        if len(batter_info) == 5:
            batter_info.append('0')
            batter_info.append('0')
            batter_info.append('0')
            batter_info.append('0')
        if len(pitcher_info) == 5:
            pitcher_info.append('0')
            pitcher_info.append('0')
            pitcher_info.append('0')
            pitcher_info.append('0')

        response = (f'{batter} ({batter_info[4]}-{batter_info[5]}{batter_info[6]}{batter_info[7]}{batter_info[8]}) '
                    f'batting against {pitcher} ({pitcher_info[4]}-{pitcher_info[5]}{pitcher_info[6]}{pitcher_info[7]}{pitcher_info[8]}).')

        ranges = sheets.read_sheet(constants.MLN_CALCULATOR, constants.MLN_CALCULATOR_ASSETS['ranges'])
        response += '```'
        for val in ranges:
            response += f"%4s: %3s - %3s\n" % (val[0], val[3], val[4])
        response += '```'

        await message.edit(content=response)


async def setup(client):
    await client.add_cog(General(client))
