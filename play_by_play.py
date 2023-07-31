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

mlr_search_test = os.getenv("MLR_SEARCH_TEST")
mlr_webhook_test = Webhook(os.getenv("MLR_WEBHOOK_TEST"))
milr_search_test = os.getenv("MILR_SEARCH_TEST")
milr_webhook_test = Webhook(os.getenv("MILR_WEBHOOK_TEST"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT_PLAY_BY_PLAY")
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
        team_color = int(colors.get(team_abbreviation, colors.get("DEFAULT")), 16)
        team_icon = icons.get(team_abbreviation, icons.get("DEFAULT"))

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}?sort=new",
                              description=comment.body,
                              color=team_color)

        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=team_icon)

        embed.add_field(name="",
                        value=f"Comment posted to r/fakebaseball at <t:{int(comment.created)}:T>")

        if mlr_search_test != "" and mlr_search_test.lower() in comment.link_title.lower():
            mlr_webhook_test.send(embed=embed)
            mlr_webhook_test.close()
        elif milr_search_test != "" and milr_search_test.lower() in comment.link_title.lower():
            milr_webhook_test.send(embed=embed)
            milr_webhook_test.close()


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
