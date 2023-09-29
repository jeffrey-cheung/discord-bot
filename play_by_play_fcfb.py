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

fcfb_search_test = os.getenv("FCFB_SEARCH_TEST")
fcfb_webhook_test = Webhook(os.getenv("FCFB_WEBHOOK_TEST"))
wc_search_test = os.getenv("WC_SEARCH_TEST")
wc_webhook_test = Webhook(os.getenv("WC_WEBHOOK_TEST"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT_FCFB")
)
icons = json.loads(constants.MLR_ICONS)


def parse_comments():
    for comment in reddit.subreddit("FakeCollegeFootball").stream.comments(skip_existing=True):
        parent_comment = comment
        while parent_comment.parent_id[0:3] == "t1_":
            parent_comment = parent_comment.parent()

        lines = parent_comment.body.splitlines()

        team_color = int("0x800203", 16)
        if lines[0].split(" ")[0].lower() == "lafayette":
            team_color = int("0xffffff", 16)

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body,
                              color=team_color)

        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=icons.get("DEFAULT"))

        embed.set_thumbnail(url=str(comment.author.icon_img))

        embed.add_field(name="", value=f"Comment posted to r/FakeCollegeFootball at <t:{int(comment.created)}:T>", inline=False)

        if fcfb_search_test != "" and fcfb_search_test.lower() in comment.link_title.lower():
            fcfb_webhook_test.send(embed=embed)
            fcfb_webhook_test.close()
        elif wc_search_test != "" and wc_search_test.lower() in comment.link_title.lower():
            wc_webhook_test.send(embed=embed)
            wc_webhook_test.close()


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
