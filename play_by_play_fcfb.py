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

fbs_search_test = os.getenv("FBS_SEARCH_TEST")
fbs_webhook_test = Webhook(os.getenv("FBS_WEBHOOK_TEST"))
fcs_search_test = os.getenv("FCS_SEARCH_TEST")
fcs_webhook_test = Webhook(os.getenv("FCS_WEBHOOK_TEST"))
rice_search_test = os.getenv("RICE_SEARCH_TEST")
rice_webhook_test = Webhook(os.getenv("RICE_WEBHOOK_TEST"))
morgan_search_test = os.getenv("MORGAN_SEARCH_TEST")
morgan_webhook_test = Webhook(os.getenv("MORGAN_WEBHOOK_TEST"))

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

        team_color = int("0xf44336", 16)
        if fbs_search_test != "" and fbs_search_test.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "california":
                team_color = int("0xfdb515", 16)
        elif fcs_search_test != "" and fcs_search_test.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "alabama":
                team_color = int("0xC99700", 16)
        elif rice_search_test != "" and rice_search_test.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "rice":
                team_color = int("0x03205b", 16)
        elif morgan_search_test != "" and morgan_search_test.lower() in comment.link_title.lower():
            if lines[0].split(" ")[0].lower() != "morgan":
                team_color = int("0xF47937", 16)

        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body,
                              color=team_color)

        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}",
                         icon_url=icons.get("DEFAULT"))

        embed.set_thumbnail(url=str(comment.author.icon_img))

        embed.add_field(name="", value=f"Comment posted to r/FakeCollegeFootball at <t:{int(comment.created)}:T>", inline=False)

        if fbs_search_test != "" and fbs_search_test.lower() in comment.link_title.lower():
            fbs_webhook_test.send(embed=embed)
            fbs_webhook_test.close()
        if fcs_search_test != "" and fcs_search_test.lower() in comment.link_title.lower():
            fcs_webhook_test.send(embed=embed)
            fcs_webhook_test.close()
        if rice_search_test != "" and rice_search_test.lower() in comment.link_title.lower():
            rice_webhook_test.send(embed=embed)
            rice_webhook_test.close()
        if morgan_search_test != "" and morgan_search_test.lower() in comment.link_title.lower():
            morgan_webhook_test.send(embed=embed)
            morgan_webhook_test.close()


while True:
    try:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing FCFB comments")
        parse_comments()
    except Exception as e:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        time.sleep(10)
    else:
        time.sleep(10)
