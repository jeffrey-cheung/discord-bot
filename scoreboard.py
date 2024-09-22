import config
import aiohttp
import asyncio
import constants
import discord
import os.path
import os
import pytz
import sys
import time
from discord import Webhook
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")


async def scoreboard():
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(os.getenv("MLR_SCOREBOARD_WEBHOOK"), session=session)
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file( "credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        try:
            service = build("sheets", "v4", credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = (sheet.values().get(spreadsheetId=constants.SPREADSHEET_ID, range=constants.SCOREBOARD_RANGE).execute())
            values = result.get("values", [])

            if not values:
                print("No data found.")
                return

            scoreboard_txt = ''
            values.sort(key=lambda x: (x[2], x[4]))
            for row in values:
                away_team = row[0]
                if away_team is None:
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
        except HttpError as err:
            print(err)


print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing scores")
while True:
    try:
        asyncio.run(scoreboard())
        time.sleep(60)
    except Exception as e:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        time.sleep(60)
    else:
        time.sleep(60)
