import config
import constants
import discord
import json
import os
import praw
import pytz
import sys
import time
from datetime import datetime
from dhooks import Webhook
from pprint import pprint

mln_search = os.getenv("MLN_SEARCH_TEST")
mln_webhook = Webhook(os.getenv("MLN_WEBHOOK_TEST"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT_PLAY_BY_PLAY")
)
colors = json.loads(constants.MLN_COLORS)
icons = json.loads(constants.MLN_ICONS)


def parse_comments():
    for comment in reddit.subreddit("BaseballbytheNumbers").stream.comments(skip_existing=True):
        team_color = int(colors.get("CAR"), 16)
        team_icon = icons.get("CAR")

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body,
                              color=team_color)

        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=team_icon)

        embed.set_thumbnail(url=str(comment.author.icon_img))

        embed.add_field(name="", value=f"Comment posted to r/BaseballbytheNumbers at <t:{int(comment.created)}:T>", inline=False)

        if mln_search != "" and mln_search.lower() in comment.link_title.lower():
            mln_webhook.send(embed=embed)
            mln_webhook.close()


while True:
    try:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing comments")
        parse_comments()
    except Exception as e:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        time.sleep(10)
    else:
        time.sleep(10)
