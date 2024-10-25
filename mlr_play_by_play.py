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

mlr_search = os.getenv("MLR_PLAY_BY_PLAY_SEARCH")
mlr_webhook = Webhook(os.getenv("MLR_PLAY_BY_PLAY_WEBHOOK"))
milr_search = os.getenv("MILR_PLAY_BY_PLAY_SEARCH")
milr_webhook = Webhook(os.getenv("MILR_PLAY_BY_PLAY_WEBHOOK"))
watch_party_search = json.loads(os.getenv("MLR_PLAY_BY_PLAY_WATCH_PARTY_SEARCH"))
watch_party_webhook = Webhook(os.getenv("MLR_PLAY_BY_PLAY_WATCH_PARTY_WEBHOOK"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("MLR_PLAY_BY_PLAY_REDDIT_USER_AGENT")
)
colors = json.loads(constants.MLR_COLORS)
icons = json.loads(constants.MLR_ICONS)


def parse_comments():
    for comment in reddit.subreddit("fakebaseball").stream.comments(skip_existing=True):
        parent_comment = comment
        while parent_comment.parent_id[0:3] == "t1_":
            parent_comment = parent_comment.parent()
        lines = parent_comment.body.splitlines()
        while "" in lines:
            lines.remove("")
        team_abbreviation = "0xffffff"
        if parent_comment.author == "FakeBaseball_Umpire" and len(lines) >= 3:
            third_line = lines[2].lstrip()
            team_abbreviation = third_line[0:3]
        elif parent_comment.author == "FakeBaseball_Umpire" and len(lines) == 2:
            third_line = lines[1].lstrip()
            team_abbreviation = third_line[0:3]
        team_color = int(colors.get(team_abbreviation, colors.get("DEFAULT")), 16)
        team_icon = icons.get(team_abbreviation, icons.get("DEFAULT"))

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body,
                              color=team_color)
        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=team_icon)
        embed.set_thumbnail(url=str(comment.author.icon_img))
        embed.add_field(name="", value=f"Comment posted to r/fakebaseball at <t:{int(comment.created)}:T>",
                        inline=False)

        if mlr_search != "" and mlr_search.lower() in comment.link_title.lower():
            mlr_webhook.send(embed=embed)
            mlr_webhook.close()
        if milr_search != "" and milr_search.lower() in comment.link_title.lower():
            milr_webhook.send(embed=embed)
            milr_webhook.close()
        if watch_party_search and any(word in comment.link_title.lower() for word in watch_party_search):
            watch_party_webhook.send(embed=embed)
            watch_party_webhook.close()


while True:
    try:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing MLR comments")
        parse_comments()
    except Exception as error:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {error}")
        print(traceback.format_exc())
    finally:
        time.sleep(10)
