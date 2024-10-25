import config
import json
import os
import time
import traceback
from datetime import datetime

import discord
import praw
import pytz
from dhooks import Webhook

import constants

fcfb_search = os.getenv("FCFB_PLAY_BY_PLAY_SEARCH")
fcfb_webhook = Webhook(os.getenv("FCFB_PLAY_BY_PLAY_WEBHOOK"))
fcfb2_search = os.getenv("FCFB2_PLAY_BY_PLAY_SEARCH")
fcfb2_webhook = Webhook(os.getenv("FCFB2_PLAY_BY_PLAY_WEBHOOK"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("FCFB_PLAY_BY_PLAY_REDDIT_USER_AGENT")
)
icons = json.loads(constants.MLR_ICONS)


def parse_comments():
    for comment in reddit.subreddit("FakeCollegeFootball").stream.comments(skip_existing=True):
        parent_comment = comment
        while parent_comment.parent_id[0:3] == "t1_":
            parent_comment = parent_comment.parent()
        lines = parent_comment.body.splitlines()
        team_color = int("0xf44336", 16)
        if fcfb_search != "" and fcfb_search.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "california":
                team_color = int("0xfdb515", 16)
        elif fcfb2_search != "" and fcfb2_search.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "cal":
                team_color = int("0xb38f4f", 16)

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body,
                              color=team_color)
        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=icons.get("DEFAULT"))
        embed.set_thumbnail(url=str(comment.author.icon_img))
        embed.add_field(name="", value=f"Comment posted to r/FakeCollegeFootball at <t:{int(comment.created)}:T>",
                        inline=False)

        if fcfb_search != "" and fcfb_search.lower() in comment.link_title.lower():
            fcfb_webhook.send(embed=embed)
            fcfb_webhook.close()
        if fcfb2_search != "" and fcfb2_search.lower() in comment.link_title.lower():
            fcfb2_webhook.send(embed=embed)
            fcfb2_webhook.close()


while True:
    try:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing FCFB comments")
        parse_comments()
    except Exception as error:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {error}")
        print(traceback.format_exc())
    finally:
        time.sleep(10)
