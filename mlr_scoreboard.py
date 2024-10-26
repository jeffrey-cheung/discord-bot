import config
import asyncio
import os
import os.path
import time
import traceback
from datetime import datetime

import aiohttp
import discord
import pytz
from discord import Webhook

import constants
from controllers import sheets_reader as sheets

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")


async def scoreboard():
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(os.getenv("MLR_SCOREBOARD_WEBHOOK"), session=session)
        values = sheets.read_sheet(constants.MLR_SCOREBOARD_SPREADSHEET_ID, constants.MLR_SCOREBOARD_RANGE)
        if not values:
            print("No data found.")
            return

        scoreboard_txt = ''
        values.sort(key=lambda x: (x[2], x[26], x[6]))
        for row in values:
            away_team = row[0]
            if away_team is None or away_team == "":
                continue
            home_team = row[1]
            away_score = int(row[8])
            home_score = int(row[9])
            inning = row[5]
            outs = int(row[6])
            obc = int(row[7])
            complete = int(row[2])
            b1 = '○'
            b2 = '○'
            b3 = '○'
            if obc in [1, 4, 5, 7]:
                b1 = '●'
            if obc in [2, 4, 6, 7]:
                b2 = '●'
            if obc in [3, 5, 6, 7]:
                b3 = '●'
            if outs == 3:
                if 'T' in inning:
                    inning = f"B{int(inning[1:])}"
                    outs = 0
                else:
                    inning = f"T{int(inning[1:]) + 1}"
                    outs = 0
            if 'T' in inning:
                inning = '▲' + inning[1:]
            else:
                inning = '▼' + inning[1:]
            if complete:
                scoreboard_txt += '```%3s %2s        Final\n' % (away_team, away_score)
                scoreboard_txt += '%3s %2s                \r\n```' % (home_team, home_score)
            else:
                scoreboard_txt += '```%3s %2s     %s       %s\n' % (away_team, away_score, b2, inning)
                scoreboard_txt += '%3s %2s   %s   %s   %s out\r\n```' % (home_team, home_score, b3, b1, outs)
            scoreboard_txt += ''
        scoreboard_txt += ''

        embed = discord.Embed(title='League Scoreboard', color=discord.Colour.yellow(), description=scoreboard_txt)
        embed.add_field(name="", value=f"Last updated <t:{int(datetime.now().timestamp())}:T>", inline=False)
        # await webhook.send(embed=embed)
        await webhook.edit_message(int(os.getenv("MLR_SCOREBOARD_MSG_ID")), embed=embed)


async def main():
    print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing MLR scores")
    while True:
        try:
            await scoreboard()
        except Exception as error:
            print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {error}")
            print(traceback.format_exc())
        finally:
            time.sleep(120)


asyncio.run(main())
