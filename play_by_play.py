import config
import constants
import datetime
import discord
import json
import os
import praw
import time
from dhooks import Webhook

mlr_search_test = os.getenv("MLR_SEARCH_TEST")
mlr_webhook_test = Webhook(os.getenv("MLR_WEBHOOK_TEST"))
milr_search_test = os.getenv("MILR_SEARCH_TEST")
milr_webhook_test = Webhook(os.getenv("MILR_WEBHOOK_TEST"))
ump_search_test = os.getenv("UMP_SEARCH_TEST")
ump_webhook_test = Webhook(os.getenv("UMP_WEBHOOK_TEST"))
ump2_search_test = os.getenv("UMP2_SEARCH_TEST")
ump2_webhook_test = Webhook(os.getenv("UMP2_WEBHOOK_TEST"))

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT")
)
colors = json.loads(constants.MLR_COLORS)
icons = json.loads(constants.MLR_ICONS)


def parse_comments():
    print("parsing")
    for comment in reddit.subreddit('fakebaseball').stream.comments(skip_existing=True):
        parent_comment = comment
        while parent_comment.parent_id[0:3] == "t1_":
            parent_comment = parent_comment.parent()

        lines = parent_comment.body.splitlines()
        while "" in lines:
            lines.remove("")
        team_abbreviation = "DEFAULT"
        if parent_comment.author == "FakeBaseball_Umpire" and len(lines) >= 3:
            third_line = lines[2].lstrip()
            team_abbreviation = third_line[0:3]
        team_color = int(colors.get(team_abbreviation, "DEFAULT"), 16)
        team_icon = icons.get(team_abbreviation, "DEFAULT")

        embed = discord.Embed(description=comment.body,
                              color=team_color)

        embed.set_author(name=str(comment.link_title),
                         url="https://old.reddit.com" + comment.permalink.rsplit('/', 2)[0],
                         icon_url=team_icon)

        embed.set_footer(
            text='/u/%s posted at %s PST' % (comment.author, datetime.datetime.fromtimestamp(comment.created)))

        if mlr_search_test.lower() in comment.link_title.lower():
            mlr_webhook_test.send(embed=embed)
        elif milr_search_test.lower() in comment.link_title.lower():
            milr_webhook_test.send(embed=embed)
        elif ump_search_test.lower() in comment.link_title.lower():
            ump_webhook_test.send(embed=embed)
        # elif ump2_search_test.lower() in comment.link_title.lower():
        #     ump2_webhook_test.send(embed=embed)


while True:
    try:
        parse_comments()
    except Exception as e:
        print(e)
        time.sleep(60)
    else:
        time.sleep(360)
