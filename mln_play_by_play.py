import config
import os
import time
import traceback
from datetime import datetime

import discord
import praw
import pytz
from dhooks import Webhook

mln_search = os.getenv("MLN_PLAY_BY_PLAY_SEARCH")
mln_webhook = Webhook(os.getenv("MLN_PLAY_BY_PLAY_WEBHOOK"))

pytz_utc = pytz.timezone("UTC")
pytz_pst = pytz.timezone("America/Los_Angeles")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("MLN_PLAY_BY_PLAY_REDDIT_USER_AGENT")
)


def parse_comments():
    for comment in reddit.subreddit("BaseballbytheNumbers").stream.comments(skip_existing=True):
        embed = discord.Embed(title=str(comment.link_title),
                              url=f"https://old.reddit.com{comment.permalink.rsplit('/', 2)[0]}/?sort=new",
                              description=comment.body)
        embed.set_author(name=str(comment.author.name),
                         url=f"https://www.reddit.com/user/{comment.author.name}")
        embed.set_thumbnail(url=str(comment.author.icon_img))
        embed.add_field(name="", value=f"Comment posted to r/BaseballbytheNumbers at <t:{int(comment.created)}:T>",
                        inline=False)

        if mln_search != "" and mln_search.lower() in comment.link_title.lower():
            mln_webhook.send(embed=embed)
            mln_webhook.close()


while True:
    try:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - Parsing MLN comments")
        parse_comments()
    except Exception as error:
        print(f"{datetime.now().astimezone(pytz_pst).strftime('%Y-%m-%d %H:%M:%S')} - {error}")
        print(traceback.format_exc())
    finally:
        time.sleep(10)
