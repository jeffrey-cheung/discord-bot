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
        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}",
                              description=comment.body)

        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=icons.get("DEFAULT"))

        embed.add_field(name="",
                        value=f"Comment posted to r/FakeCollegeFootball at <t:{int(comment.created)}:T>")

        if fcfb_search_test != "" and fcfb_search_test.lower() in comment.link_title.lower():
            fcfb_webhook_test.send(embed=embed)
            fcfb_webhook_test.close()


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
