import config
import os
import praw
from pprint import pprint

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT_FCFB")
)

submission_list = []

if len(submission_list) == 0:
    comments = reddit.redditor("").comments.new()
    for x in comments:
        if x.link_author == "NFCAAOfficialRefBot":
            last = x.body.split(' ')[-1]
            if last.isdigit():
                if x.link_id not in submission_list:
                    submission_list.insert(0, x.link_id)

for submission_id in submission_list:
    submission_comments = reddit.submission(submission_id[-7:]).comments.list()
    submission_comments.sort(key=lambda y: y.created)

    for x in submission_comments:
        if x.author is not None and x.author.name == "NFCAAOfficialRefBot":
            lines = x.body.splitlines()
            offense = "0"
            defense = "0"
            difference = "0"
            down = "0"
            play = "0"
            for y in lines:
                if len(y) > 9 and y.split(" ")[0] == "Offense:" and y.split(" ")[1].isdigit():
                    offense = y.split(" ")[1]
                elif len(y) > 9 and y.split(" ")[0] == "Defense:" and y.split(" ")[1].isdigit():
                    defense = y.split(" ")[1]
                elif len(y) > 12 and y.split(" ")[0] == "Difference:" and y.split(" ")[1].isdigit():
                    difference = y.split(" ")[1]
            if offense != "0" and defense != "0":
                user_comment = x.parent().body.splitlines()
                parent_comment = x
                while parent_comment.parent_id[0:3] == "t1_":
                    parent_comment = parent_comment.parent()
                parent_first = parent_comment.body.splitlines()
                if "has submitted their number." in parent_first[0] and "you're up." in parent_first[0]:
                    if "It's 1st and " in parent_first[2]:
                        down = "1st"
                    elif "It's 2nd and " in parent_first[2]:
                        down = "2nd"
                    elif "It's 3rd and " in parent_first[2]:
                        down = "3rd"
                    elif "It's 4th and " in parent_first[2]:
                        down = "4th"
                    elif " is kicking off." in parent_first[2]:
                        down = "kickoff"
                    elif " just scored." in parent_first[2]:
                        down = "pat"
                    if "field goal " in user_comment[0].lower():
                        play = "field goal"
                    elif "punt " in user_comment[0].lower():
                        play = "punt"
                    elif "pass " in user_comment[0].lower():
                        play = "pass"
                    elif "run " in user_comment[0].lower():
                        play = "run"
                    elif down == "pat" and "pat " in user_comment[0].lower():
                        play = "pat"
                    elif down == "pat" and "two point " in user_comment[0].lower():
                        play = "two point"
                    elif down == "kickoff" and "onside " in user_comment[0].lower():
                        play = "onside"
                    elif down == "kickoff" and "normal " in user_comment[0].lower():
                        play = "normal"
                    elif down == "kickoff" and "squib " in user_comment[0].lower():
                        play = "squib"
                    print(f"{x.link_id},{parent_first[0].split(' ')[0]},{offense},{defense},{difference},{down},{play}")