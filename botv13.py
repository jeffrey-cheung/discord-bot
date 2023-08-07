# botv12-noslash.py
# 
# 11/3/2022
# Reverted to non-slash version, but to work with Discord.py v2
#
# converted to use JSON API for new website http://www.swing420.com/api
# !react converted to JSON                  11/4
# !hm modified for both leagues, 
#     converted to JSON                     11/7
# !hmm deprecated                           11/7
# !chart converted to JSON                  11/7
# !deltas converted to JSON                 11/7
# !last modified for both leagues, 
#     converted to JSON                     11/7
# !lastm deprecated                         11/7
# !swing converted to JSON                  11/7
# !diffs deleted                            11/7
# 
# botv10-sql.py - 
# added diffs command
# added swingdeltas command
# added swinglast command
# 
# botv8-sql.py see botv8.py for Redditball API features
# NEW:
# !player to replace the old Umpty command   5/2 - moved to Dumpty on 5/9
# !ranges to replace the old Umpty command   5/6 - moved to Dumpty on 5/9
# 
# CONVERTED:
# !player changed to !batter and !pitcher   4/27
# !cg converted to sheets                   5/8
# !chart converted to SQL                   4/27
# !deltas converted to SQL                  4/30
# !hm converted to SQL                      4/30  tweaked to use OBC 5/23
# !hmm converted to SQL                     4/30  tweaked to use OBC 5/24
# !last converted to SQL                    4/28
# !lastm converted to SQL                   4/28
# !react converted to SQL                   4/29
# !swing
#
# OBC key for situational queries:
# 0 = bases empty
# 1 = runner on 1st
# 2 = runner on 2nd
# 3 = runner on 3rd
# 4 = runners on 1st & 2nd
# 5 = runners on 1st & 3rd
# 6 = runners on 2nd & 3rd
# 7 = bases loaded


import os
import random
import discord, pygsheets, csv, math
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib.request, json, re, requests
import mysql.connector
from matplotlib.ticker import PercentFormatter
from matplotlib.ticker import AutoMinorLocator
from dotenv import load_dotenv
from tabulate import tabulate
from oauth2client.service_account import ServiceAccountCredentials
from pylab import xticks
from discord.ext import commands
from dotenv import load_dotenv

if not os.path.exists("images"):
    os.mkdir("images")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True
intents.members = True
intents.all()

bot = commands.Bot(command_prefix='!', description='Scout Bot', case_insensitive=True, intents=intents)
channel = bot.get_channel(676223227869003776)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='react', help="!react <Pitcher ID> <League> <lower#|only pitch#> [optional: upper pitch#] MLR reactions after pitch or pitch range.")
async def react(ctx, *args):
    pitcherID        = int(args[0])
    league           = args[1]
    lowerpitch       = int(args[2])
    upperpitch       = 0
    lower            = int(lowerpitch)
    xlegend          = []
    pitch            = [] # all non-autoed pitches
    inning           = [] # all non-autoed innings
    session          = [] # all non-autoed sessions
    result           = [] # all non-autoed results
    season           = [] # all non-autoed seasons
    obc              = [] # bases occupied
    i = 0
    ii = 0

    if league.lower() == "milr":
        pitcherurl="https://www.swing420.com/api/plateappearances/pitching/milr/" + str(pitcherID)
    else:
        pitcherurl="https://www.swing420.com/api/plateappearances/pitching/mlr/" + str(pitcherID)
    with urllib.request.urlopen(pitcherurl) as url:
        data = json.loads(url.read().decode())
    # Let's grab everything that matches
    i = 0
    ii = 0

    # get pitcher name and read it all in
    for p in data:
        pitcher = p['pitcherName']
        if p['pitch'] != None: # just skip the non/auto resulted pitches
            pitch.append(p['pitch'])
            inning.append(p['inning'])
            session.append(p['session'])
            result.append(p['oldResult']) 
            season.append(p['season'])
            obc.append(['obc'])

    before = [] # pitch before the match
    match  = [] # the match
    after  = [] # pitch after the match
    # now let's go through and look for matches
    for p in range(len(pitch) - 1):
        if len(args) == 4: # looking for a range
            upperpitch = args[3]
            # fix in lower to be lower, in case they input range backwards
            lower = int(lowerpitch)
            upper = int(upperpitch)
            if upper < lower:
                switch = upper
                upper = lower
                lower = switch
            if int(pitch[p]) <= upper and int(pitch[p]) >= lower: # it's a match for a range
                legend = "S" + str(season[p]) + "." + str(session[p]) + "\n" +  str(inning[p])
                if p > 0:
                    before.append(pitch[p-1])
                    legend = legend + "\nB: " + str(pitch[p-1])
                else:
                    before.append(None)
                    legend = legend + "\nB: "
                match.append(pitch[p])
                legend = legend + "\nM: " + str(pitch[p])
                if p < len(pitch)-1:
                    after.append(pitch[p+1])
                    legend = legend + "\nA: " + str(pitch[p+1])
                else:
                    after.append(None)
                    legend = legend + "\nA: "
                i = i + 1 # count matches
                xlegend.append(legend)
        else: # exact pitch match OR situational pitch (add later, like 2out)
            if pitch[p] == lower: # it's a match
                legend = "S" + str(season[p]) + "." + str(session[p]) + "\n" +  str(inning[p])
                if p > 0:
                    before.append(pitch[p-1])
                    legend = legend + "\nB: " + str(pitch[p-1])
                else:
                    before.append(None)
                    legend = legend + "\nB: "
                match.append(pitch[p])
                legend = legend + "\nM: " + str(pitch[p])
                if p < len(pitch)-1:
                    after.append(pitch[p+1])
                    legend = legend + "\nA: " + str(pitch[p+1])
                else:
                    after.append(None)
                    legend = legend + "\nA: "
                i = i + 1 # count matches
                xlegend.append(legend)
        ii = ii + 1 # count all pitches

    # Quick check to report reactions
    ranger = str(lower)
    if len(args) == 4:
        ranger = ranger + " - " + str(upper)
    await ctx.send("You asked for pitches from " + pitcher + " before & after pitching " + ranger)

    title = "Pitches from " + pitcher + " before & after pitching " + ranger + " (" + str(i) + " matches)"
    data1 = match
    data2 = after
    data3 = before
    x_axis = xlegend
    fig=plt.figure(figsize=(i/1.5,5)) #Creates a new figure
    ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
    pitch = ax1.plot(data1,'bo-',label='Match') #no need for str(x_axis)
    after = ax1.plot(data2,'k--',label='After') 
    before = ax1.plot(data3,'r--',label='Before') 
    plt.xticks(range(i), x_axis, size='small')
    ax1.set_ylim(0,1050)
    plt.setp(ax1.get_xticklabels(), visible=True)
    plt.suptitle(title, y=1.0, fontsize=17)
    plt.legend()
    ## GRIDLINES FOR EASIER READING
    plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
    ## END GRIDLINES
    fig.subplots_adjust(top=.92,bottom=0.2)
    fig.tight_layout()
    plt.savefig("images/beforeafter.png",bbox_inches='tight')
    with open('images/beforeafter.png', 'rb') as fp:
        f=discord.File(fp, filename='images/beforeafter.png')
    await ctx.send(file=f)
    

@bot.command(name='none') 
async def plot_currentgame(ctx, *args):
    # DID THEY SPECIFY BOTH TEAM AND LEAGUE?
    await ctx.send("This command does not currently work")
    if len(args) < 200:
    #if len(args) < 2: 
        await ctx.send("This command does not currently work")
    else:
        # OK LET'S MAKE SURE IT'S A VALID COMBINATION OF TEAM/LEAGUE
        # We do that by generating an active games log URL and looking for a 404
        # First step, get ID of the current active game, using Team/League provided:
        team = args[0].upper()
        league = args[1].upper()
        activegameurl = "https://"
        gamelogurl    = "https://"
        redditurl     = "https://redd.it/"
        redditballurl = "https://"
        if league.lower() == "milr":
            activegameurl = activegameurl + "milr."
            gamelogurl = gamelogurl + "milr."
            redditballurl = redditurl + "milr."
        activegameurl = activegameurl + "redditball.com/api/v1/games/active/" + team

        # Here's the 404 check:
        r = requests.get(activegameurl)
        if r.status_code == 404:
            await ctx.send( "Check the <Team> and <League> inputs")
        else: 
            # OK Team/League combo is valid, so let's grab game ID for the active game
            with urllib.request.urlopen(activegameurl) as url:
                data = json.loads(url.read().decode())
            gameid       = data['id']
            gameidreddit = data['id36']

            # And build out the gamelog for that game, to parse and chart
            await ctx.send('You asked to see the pitch/delta details for {} in {}'.format(args[0], args[1]))
            gamelogurl = gamelogurl + "redditball.com/api/v1/games/" + str(gameid) + "/log"
            #with urllib.request.urlopen("https://redditball.com/api/v1/games/1391/log") as url:
            # And away we go!
            redditballurl = redditballurl + "redditball.com/games/" + str(gameid)
            #print("Viewing log for ", gamelogurl)
            with urllib.request.urlopen(gamelogurl) as url:
                data = json.loads(url.read().decode())
            numpitches = len(data)

            #print(numpitches, " PAs in the game so far.")
            pitch      = [] # actual pitch
            swing      = [] # actual swing
            diff       = [] # actual diff
            pitchseq   = [] # x-axis zero-indexed
            pitchno    = [] # x-axis 1-indexed (to display in human friendly on the graph)
            sitdata    = [] # situational data to display below x-axis bar
            delta      = [] # pitch deltas
            inning     = [] # inning, for x-axis display
            totaldelta = 0 #used to calculate average delta
            xlegend    = [] # x-axis with Inning/Pitch/Delta info

            # Populate with PA results: Need to limit it to just ONE team's pitches, rather than all pitches
            # example: MIL is using the bot (ie: they want to see pitches from the OTHER team only)
            # We check to see if MIL is the home team, and if so we want to look for pitches in the 
            # bottom of the inning (when MIL is batting). Otherwise, look for pitches in the top of 
            # the inning.
            i = 0
            hometeam = data[0]['game']['homeTeam']['tag']
            awayteam = data[0]['game']['awayTeam']['tag']
            season   = data[0]['game']['season']
            session  = data[0]['game']['session']
            if re.findall(team, data[0]['game']['homeTeam']['tag']):
                isHomeTeam = True
                regexInning = '^B' # look at pitches in bottom of inning when the home team is batting
            else:
                isHomeTeam = False
                regexInning = '^T' # look at pitches in the top of the inning when the visiting team is batting
            # Populate with PA results
            for p in data:
                # does this match top or bottom of inning as required?
                # does the pitch value also not null (ie: not "None" - skip the autos)
                if re.findall(regexInning, p['beforeState']['inning']) and p['pitch'] is not None: 
                    #print("Bottom of the inning is when our team is batting")
                    pitch.append(p['pitch'])
                    swing.append(p['swing'])
                    diff.append(p['diff'])
                    inning.append(p['beforeState']['inning'])
                    #print("Added: ", p['beforeState']['inning'] , " pitch/swing/diff: ", p['pitch'], "/", p['swing'], "/", p['diff'])
                    i = i+1

            # populate with the number of PAs/pitches
            for s in range(i):  
                pitchseq.append(s)
                pitchno.append(s+1) # for x-axis of the chart

            # calculate deltas
            for d in range(len(pitch)): # range -> just the pitches picked up from the opposing pitcher (does not include autos)
                if (d > 0):
                    pitchd = abs(pitch[d] - pitch[d-1])
                    if pitchd > 500:
                        pitchd = 1000- pitchd
                    delta.append(pitchd)
                    totaldelta = totaldelta + pitchd
            pitch.reverse()
            swing.reverse()
            diff.reverse()
            delta.reverse()
            #delta.insert(0,"") # after reversing, stick a blank in the first position - there is no first pitch delta
            delta.insert(0,0)
            inning.reverse()

            for t in range(i):  
                textsit = inning[t] + "\nP: " + str(pitch[t]) + "\nD: " + str(delta[t])
                sitdata.append(textsit)
            
            avgdelta = round(totaldelta/(len(delta)))
            #annotations = []
            title = "PAs for " + team + " (S" + str(season) + "." + str(session) + " " + awayteam + "@" + hometeam + ")" + ". Avg delta: " + str(avgdelta)
            #annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
            #                        xanchor='left', yanchor='bottom',
            #                        text=title,
            #                        font=dict(family='Arial',
            #                                    size=24,
            #                                    color='rgb(37,37,37)'),
            #                        showarrow=False))
            #fig = go.Figure()
            #fig.add_trace(go.Scatter(x=pitchno, y=pitch, name='Pitch', text=["1","2","3","4","5"], textposition="top center"))
            #fig.add_trace(go.Scatter(x=pitchno, y=delta, name='Delta'))
            #fig.update_layout(annotations=annotations)
            #fig.update_xaxes(nticks=numpitches, dtick=1, tickangle=75)
            #fig.update_yaxes(nticks=10)
            #fig.update_traces(textposition='top center')
            thep = ""
            thed = ""
            for p in range(len(swing)):
                #print(swing[p])
                if pitch[p] < 10:
                    thep = "   " + str(pitch[p])
                elif pitch[p] < 100:
                    thep = " " + str(pitch[p])
                else:
                    thep = str(pitch[p])
                
                if delta[p] < 10:
                    thed = "   " + str(delta[p])
                elif delta[p] < 100:
                    thed = " " + str(delta[p])
                else:
                    thed = str(delta[p])
                xlegend.append(inning[p] + "     \nP: " + thep + "\nD: " + thed)
            data1=pitch
            data2=delta
            x_axis = xlegend
            fig=plt.figure(figsize=(len(pitch)/1.5,5)) #Creates a new figure

            ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
            pitch = ax1.plot(data1,'bo-',label='Pitch') #no need for str(x_axis)
            delta = ax1.plot(data2,'k--',label='Delta') 
            plt.xticks(range(len(data2)), x_axis, size='small')
            ax1.set_ylim(0,1050)

            #Assigning labels
            lines = pitch+delta
            labels = [l.get_label() for l in lines]
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            fig.subplots_adjust(top=.92,bottom=0.2)
            fig.tight_layout()
            plt.savefig("images/gamelog.png",bbox_inches='tight')
            #plt.close(fig)
            with open('images/gamelog.png', 'rb') as fp:
                f=discord.File(fp, filename='images/gamelog.png')
                await ctx.send(file=f)
            await ctx.send("Reddit thread link: <" + redditurl + gameidreddit + ">")
            await ctx.send("Redditball game link: <" + redditballurl + ">")

@bot.command(name='hm', help="!hm <League> <Pitcher ID> [optional:hr, loaded, empty, corners, risp, inning #, 2out, 1out, 0out]. MLR heatmaps.")
async def heatmap(ctx, *args):
    if len(args) > 1:
        league = args[0]
        pitcherID = args[1]
        if league.lower() == "milr":
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/milr/" + str(pitcherID)
            leaguetitle = "MiLR"
        else: 
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/mlr/" + str(pitcherID)
            leaguetitle = "MLR"
    if len(args) < 2: # didn't give enough args - minimum is league and name
        # do this
        await ctx.send("You need to provide at least a league and pitcher ID.")
    else: 
        with urllib.request.urlopen(pitcherurl) as url:
            data = json.loads(url.read().decode())
        validpitches = []
        y      = []
        x      = []
        result = []
        inning = []
        first  = []
        second = []
        third  = []
        outs   = []
        hrx    = []
        hry    = []
        i = 0
        obc = 0
        thepitch = 0
        pitcher = "Nobody"
        for p in data:
            pitcher = p['pitcherName']
            if p['pitch'] != None:
                thepitch = int(p['pitch'])
                y.append(int(thepitch/100)*100) # 100s on the y axis of heatmap
                x.append(int(thepitch % 100))   # 10s/1s on the x axis of heatmap
                result.append(p['exactResult'])      # result (ie: 1B, 2B, HR, RGO, etc.)
                inning.append(p['inning']) # inning (T# for top of inning, B# for bottom of inning)
                obc = p['obc']
                if (obc == 1 or obc == 4 or obc == 5 or obc == 7):
                    first.append(True)
                else:
                    first.append(False)
                if (obc == 2 or obc == 4 or obc == 6 or obc == 7):
                        second.append(True)
                else:
                    second.append(False)
                if (obc == 3 or obc == 5 or obc == 5 or obc == 7):
                    third.append(True)
                else:
                    third.append(False)
                outs.append(p['outs']) # Number of outs at time of pitch
                validpitches.append(i)
                i = i + 1
            
        # Defaults for graph (if no arguments given... ie: all pitches, wide open)
        title = leaguetitle + " heatmap for " + pitcher + " (all " + str(i) +" pitches)"
        hrcount = 0

        if len(args) > 2: # they provided optional arguments, so let's separate those out from the "total" pitches
            j = 0
            nextpitch = 0
            nexty = 0
            nextx = 0

            ###########
            # HOMERUN #
            ###########
            if args[2].lower() == "hr":
                for hr in result:
                    if hr.lower() == "hr" and j + 1 < i: #this is a HR, and it's not the last pitch
                        nextpitch = j + 1
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab the next pitch's x value
                        hry.append(nexty) # grab the next pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " after HR (" + str(hrcount) + " total)" # update the title

            ################
            # BASES LOADED #
            ################    
            elif args[2].lower() == "loaded":
                for loaded in result:
                    if first[j] == True and second[j] == True and third[j] == True and j + 1 < i: #bases loaded, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " with bases loaded (" + str(hrcount) + " total)" # update the title

            ##########
            # 2 OUTS #
            ##########    
            elif args[2].lower() == "2out":
                for loaded in result:
                    if outs[j] == 2 and j + 1 < i: #bases loaded, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " with 2 outs (" + str(j) + " total)" # update the title
                
            ##########
            # 1 OUT  #
            ##########    
            elif args[2].lower() == "1out":
                for loaded in result:
                    if outs[j] == 1 and j + 1 < i: #bases loaded, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " with 1 out (" + str(j) + " total)" # update the title

            ###########
            # NO OUTS #
            ###########    
            elif args[2].lower() == "0out":
                for loaded in result:
                    if outs[j] == 0 and j + 1 < i: #bases loaded, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " with no outs (" + str(j) + " total)" # update the title

            ################
            # BASES EMPTY  #
            ################    
            elif args[2].lower() == "empty":
                for loaded in result:
                    if first[j] == False and second[j] == False and third[j] == False and j + 1 < i: #bases empty, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " (with bases empty - " + str(hrcount) + " total)" # update the title

            ###########################
            # FIRST PITCH OF THE GAME #
            ###########################    
            #elif args[2].lower() == "firsgame":
            #    for loaded in result:
            #        if first[j] == False and second[j] == False and third[j] == False and j + 1 < i: #bases empty, and it's not the last pitch
            #            nextpitch = j
            #            nexty = y[nextpitch]
            #            nextx = x[nextpitch]
            #            hrx.append(nextx) # grab THIS pitch's x value
            #            hry.append(nexty) # grab THIS pitch's y value
            #            hrcount = hrcount + 1
            #        j = j + 1
            #    x = hrx
            #    y  = hry
            #    title = leaguetitle + " heatmap for " + pitcher + " (first pitch of the game - " + str(hrcount) + " total)" # update the title

            #############################
            # FIRST PITCH OF THE INNING #
            #############################    
            #elif args[2].lower() == "firstinnings":
            #    for loaded in result:
            #        if first[j] == False and second[j] == False and third[j] == False and j + 1 < i: #bases empty, and it's not the last pitch
            #            nextpitch = j
            #            nexty = y[nextpitch]
            #            nextx = x[nextpitch]
            #            hrx.append(nextx) # grab THIS pitch's x value
            #            hry.append(nexty) # grab THIS pitch's y value
            #            hrcount = hrcount + 1
            #        j = j + 1
            #    x = hrx
            #    y  = hry
            #    title = leaguetitle + " heatmap for " + pitcher + " (first pitch of the inning - " + str(hrcount) + " total)" # update the title

            #######################
            # RUNNERS ON CORNERS  #
            #######################    
            elif args[2].lower() == "corners":
                for loaded in result:
                    if first[j] == True and second[j] == False and third[j] == True and j + 1 < i: #runners on corners, and it's not the last pitch
                        #nextpitch = j + 1
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab THIS pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " - runners on the corners (" + str(hrcount) + " total)" # update the title

            #########
            # RISP  #
            #########    
            elif args[2].lower() == "risp":
                for loaded in result:
                    if (second[j] == True or third[j] == True) and j + 1 < i: #RISP, and it's not the last pitch
                        nextpitch = j
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab THIS pitch's x value
                        hry.append(nexty) # grab This pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " - RISP (" + str(hrcount) + " total)" # update the title

            ####################
            # SPECIFIC INNING  #
            ####################    
            elif args[2].lower() == "inning" and args[2].isnumeric() == True: 
                for inn in inning:
                    tinning = "T" + str(args[2])
                    binning = "B" + str(args[2])
                    if (inning[j] == tinning or inning[j] == binning) and j + 1 < i: #matches an inning, and it's not the last pitch
                        nextpitch = j + 1
                        nexty = y[nextpitch]
                        nextx = x[nextpitch]
                        hrx.append(nextx) # grab the next pitch's x value
                        hry.append(nexty) # grab the next pitch's y value
                        hrcount = hrcount + 1
                    j = j + 1
                x = hrx
                y  = hry
                title = leaguetitle + " heatmap for " + pitcher + " in inning #" + str(args[2]) + " (" + str(hrcount) + " total)" # update the title


        annotations = []
        annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                                xanchor='left', yanchor='bottom',
                                text=title,
                                font=dict(family='Arial',
                                            size=18,
                                            color='rgb(37,37,37)'),
                                showarrow=False))
        fig = go.Figure()
        fig.add_trace(go.Histogram2d(
                colorscale=[[0, 'rgb(253,34,5)'], [0.25, 'rgb(253,192,5)'], [0.5, 'rgb(233,253,5)'], [0.75, 'rgb(113,196,5)'], [1, 'rgb(5,196,19)']],
                reversescale=True,
                xbingroup=4,
                ybingroup=10,
                ygap=2,
                xgap=2,
                autobinx=False,
                xbins=dict(start=0, end=99, size=25),
                autobiny=False,
                ybins=dict(start=0, end=1000, size=100),
                x=x,
                y=y
            ))
        fig.update_xaxes(dtick=25)
        fig.update_yaxes(dtick=100)
        fig.update_traces(colorbar=dict(title="Num pitches"))
        fig.update_layout(annotations=annotations)
        fig.write_image("images/heatmap.png")
        with open('images/heatmap.png', 'rb') as fp:
            f=discord.File(fp, filename='images/heatmap.png')
        await ctx.send(file=f)

@bot.command(name='chart', help="!chart <Pitcher ID> <League> <Season #> [option: \"inning\" <#>] shows pitch/delta sequences.")
async def charts(ctx, *args):
    totaldelta = 0
    deltacount = 0
    avgdelta = 0
    inningno = 0
    if len(args) < 2:
        await ctx.send("Usage: !chart <Pitcher ID> <League> <Season #> [option: \"inning\"  <#>")
    elif len(args) == 4: # maybe wrote inning but didn't give inning number?
        await ctx.send("Usage: !chart <Pitcher ID> <League> <Season #> [option: \"inning\"  <#>")
    else:
        pitcherID   = args[0]
        league      = args[1]
        if len(args) == 5:
            inningno = args[4]
        if league.lower() == "milr":
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/milr/" + str(pitcherID)
        else:
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/mlr/" + str(pitcherID)
        with urllib.request.urlopen(pitcherurl) as url:
            data = json.loads(url.read().decode())
        res = len(data)
        if res > 0:
            # Grab player name for chart
            pname = data[0]['pitcherName']
            await ctx.send('You asked to see the pitch/delta details for {} ({}) in S{}'.format(pname, args[1], args[2]))
            pitch    = [] # actual pitch
            swing    = [] # actual swing
            diff     = [] # actual diff
            pitchseq = [] # x-axis zero-indexed
            pitchno =  [] # x-axis 1-indexed (to display in human friendly on the graph)
            delta    = [] # pitch deltas
            xlegend  = [] # x-axis to display pitch and delta values
            inning   = [] # inning, for x-axis display
            seasons  = [] # season for x-axis display
            sessions = [] # session for x-axis display
            delta.append(0)
            i = 0
            
            # Read it all in
            for p in data:
                if p['pitch'] != None: # there was a pitch (not an auto)
                        if len(args) == 3: # they specified a season
                            season = int(args[2])
                            if p['season'] == season: # so limit to that season only 
                                pitch.append(p['pitch'])
                                swing.append(p['swing'])
                                diff.append(p['diff'])
                                inning.append(p['inning'])
                                seasons.append(p['season'])
                                sessions.append(p['session'])
                                i = i + 1
                        else: # they didn't specify a season, so get them all
                            pitch.append(p['pitch'])
                            swing.append(p['swing'])
                            diff.append(p['diff'])
                            inning.append(p['inning'])
                            seasons.append(p['season'])
                            sessions.append(p['session'])
                            i = i + 1

            # they want to limit to a specific inning for the given season. 
            # This requires a different graph, with overlayed game sequences, 
            # like the old Excel pivot chart
            if int(inningno) > 0: 
                limgame = 0
                limpitch = [] # store pitches limited to specific inning
                for t in pitch:
                    if inning[limgame] == "B" + str(inningno) or inning[limgame] == "T" + str(inningno):
                        pass # need to flesh this out
                    limgame = limgame + 1

            # populate with the number of PAs/pitches
            for s in range(i):  
                pitchseq.append(s)
                pitchno.append(s+1) # for x-axis of the chart

            # calculate diffs
            for d in range(len(pitch)): # range -> just the pitches picked up from the opposing pitcher (does not include autos)
                if (d > 0):
                    pitchd = abs(pitch[d] - pitch[d-1])
                    if pitchd > 500:
                        pitchd = 1000- pitchd
                    delta.append(pitchd)
                    totaldelta = totaldelta + pitchd
                    deltacount = deltacount + 1
            
            if deltacount == 0:
                nonefound = "No pitches for " + pname + " in " + league
                if len(args) == 3:
                    nonefound = nonefound + " for S" + str(season)
                nonefound = nonefound + "."
                await ctx.send(nonefound)
            avgdelta = round(totaldelta / deltacount)
            title = "Pitch sequence for " + pname + " in " + league + ". " + str(i) + " pitches" + " (avg delta=" + str(avgdelta) + ")"
            if len(args) == 3:
                title = title + " (S" + str(season) + " only)"
            thep = ""
            thed = ""
            for p in range(len(swing)):
                if pitch[p] < 10:
                    thep = "   " + str(pitch[p])
                elif pitch[p] < 100:
                    thep = " " + str(pitch[p])
                else:
                    thep = str(pitch[p])
                
                if delta[p] < 10:
                    thed = "   " + str(delta[p])
                elif delta[p] < 100:
                    thed = " " + str(delta[p])
                else:
                    thed = str(delta[p])
                xlegend.append("S" + str(seasons[p]) + "." + str(sessions[p]) + "   \n" + inning[p] + "     \nP: " + thep + "\nD: " + thed)
            data1=pitch
            data2=delta
            x_axis = xlegend
            fig=plt.figure(figsize=(len(pitch)/1.5,5)) #Creates a new figure

            ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
            pitch = ax1.plot(data1,'bo-',label='Pitch') #no need for str(x_axis)
            delta = ax1.plot(data2,'k--',label='Delta') 
            plt.xticks(range(len(data2)), x_axis, size='small')
            ax1.set_ylim(0,1050)

            #Assigning labels
            lines = pitch+delta
            labels = [l.get_label() for l in lines]
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            fig.subplots_adjust(top=.92,bottom=0.2)
            fig.tight_layout()
            plt.savefig("images/plog.png",bbox_inches='tight')
            with open('images/plog.png', 'rb') as fp:
                f=discord.File(fp, filename='images/plog.png')
                await ctx.send(file=f)

        else:
            await ctx.send("No pitching data for Pitcher ID " + pitcherID + ". Please try again.")

@bot.command(name='deltas', help="!deltas <Pitcher ID> <League> [optional:\"inning\" <#>, \"season\" <#>, \"hr\", \"corners\", \"loaded\", \"empty\", \"risp\", \"2out\", \"1out\", \"0out\", \"steal\"]. Delta histograms.")
async def deltas(ctx, *args):
    totaldelta = 0
    deltacount = 0
    avgdelta   = 0
    inningno   = 0 # Will only change if they gave "inning <#>" args
    cmd        = ""
    sich       = ""
    if len(args) < 2:
        await ctx.send("Usage: !deltas <Pitcher ID> <League> [optional:\"inning\" <#>")
    else:
        pitcherID   = args[0]
        league      = args[1]
        if len(args) > 2:
            cmd = args[2]
            print(cmd)
        if len(args) == 4:
            if args[2].lower() == "inning":
                inningno = args[3]
            elif args[2].lower() == "season":
                theseason = args[3]
        if league.lower() == "milr":
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/milr/" + str(pitcherID)
        else:
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/mlr/" + str(pitcherID)
        with urllib.request.urlopen(pitcherurl) as url:
            data = json.loads(url.read().decode())
        res = len(data)
        if res > 0:
            # Grab player name for chart
            pname = data[0]['pitcherName']
            await ctx.send( 'You asked to see deltas for {} in {}'.format(pname, args[1]) )
            pitch      = [] # actual pitch
            delta      = [] # pitch deltas
            inning     = [] # inning, for x-axis display
            firstbase  = [] # occupied or not
            secondbase = [] # occupied or not
            thirdbase  = [] # occupied or not
            result     = [] # PA result
            outs       = [] # how many outs at time of pitch
            season     = []

            i = 0
            obc = 0
            # Read it all in
            for p in data:
                if p['pitch'] != None: # there was a pitch (not an auto)
                    pitch.append(p['pitch'])
                    obc = p['obc']
                    if (obc == 1 or obc == 4 or obc == 5 or obc == 7):
                        firstbase.append(True)
                    else:
                        firstbase.append(False)
                    if (obc == 2 or obc == 4 or obc == 6 or obc == 7):
                            secondbase.append(True)
                    else:
                        secondbase.append(False)
                    if (obc == 3 or obc == 5 or obc == 5 or obc == 7):
                        thirdbase.append(True)
                    else:
                        thirdbase.append(False)
                    result.append(p['exactResult'])
                    outs.append(p['outs'])
                    inning.append(p['inning'])
                    season.append(p['season'])
                    i = i + 1
            
            # now let's calculate deltas
            beforePitch = 0
            afterPitch   = 0
            pitchDelta   = 0
            subtitle = ""
            for p in range(i-1):
                # see what "cmd" was issued as args[2]
                if cmd.lower() == "hr": # they want to see deltas after a HR
                    if result[p] == "HR":
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta                
                        print(str(pitchDelta))
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "corners": # they want to see deltas with runners on the corners
                    subtitle = "with runners on the corners."
                    if firstbase[p] == True and secondbase[p] == False and thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "loaded": # they want to see deltas with bases loaded
                    subtitle = "with the bases loaded."
                    if firstbase[p] == True and secondbase[p] == True and thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "empty": # they want to see deltas with bases empty
                    subtitle = "with the bases empty."
                    if firstbase[p] == False and secondbase[p] == False and thirdbase[p] == False:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "season" and int(theseason) > 0: # they specified a season
                    subtitle = "in season " + str(theseason) + " only."
                    if season[p] == int(theseason): 
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1                    
                elif cmd.lower() == "risp": # they want to see deltas with runners in scoring position
                    subtitle = "with runners in scoring position."
                    if secondbase[p] == True or thirdbase[p] == True:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "2out": # they want to see deltas with 2 outs
                    subtitle = "with 2 outs."
                    if outs[p] == 2:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "1out": # they want to see deltas with 1 out
                    subtitle = "with 1 out."
                    if outs[p] == 1:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "0out": # they want to see deltas with 0 outs
                    subtitle = "with runners nobody out."
                    if outs[p] == 0:
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "steal": # they want to see deltas after a steal
                    subtitle = "after a steal"
                    if result[p] == "Steal 2B" or result[p] == "Steal 3B":
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)               
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "inning" and int(inningno) > 0: # arg[3] = inning number
                    subtitle = "in inning # " + inningno + "."
                    if (inning[p] == "T" + str(inningno) or inning[p] == "B" + str(inningno)) and (inning[p+1] == "T" + str(inningno) or inning[p+1] == "B" + str(inningno)): # only the same inning
                        beforePitch = pitch[p]
                        afterPitch = pitch[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)               
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                else: # they didn't specify anything, so get them all
                    subtitle = "(all situations)"
                    beforePitch = pitch[p]
                    afterPitch = pitch[p+1]
                    pitchDelta = abs(beforePitch - afterPitch)
                    if pitchDelta > 500:
                        pitchDelta = 1000 - pitchDelta
                    delta.append(pitchDelta)
                    totaldelta = totaldelta + pitchDelta
                    deltacount = deltacount + 1
            
            if deltacount == 0:
                nonefound = "No pitches for " + pname + " in " + league
                if cmd.lower() == "season":
                    nonefound = nonefound + " for S" + str(season)
                nonefound = nonefound + " " + subtitle + "."
                await ctx.send(nonefound)
            avgdelta = round(totaldelta / deltacount)
            title = "Deltas for " + pname + " in " + league + ". " + str(len(delta)) + " total deltas " + subtitle + " (avg delta=" + str(avgdelta) + ")"
            x = delta
            num_bins = 10
            fig, ax = plt.subplots()

            # the histogram of the data
            n, bins, patches = ax.hist(x, num_bins, density=False, rwidth=.8)
            xticks = [(bins[idx+1] + value)/2 for idx, value in enumerate(bins[:-1])]
            xticks_labels = [ "{:.0f}\nto\n{:.0f}".format(value, bins[idx+1]) for idx, value in enumerate(bins[:-1])]
            plt.xticks(xticks, labels = xticks_labels)
            
            ax.set_xlabel('Deltas')
            ax.set_title(title)
            # Tweak spacing to prevent clipping of ylabel
            fig.tight_layout()
            #plt.show()
            
            fig.tight_layout()
            plt.savefig("images/deltas.png",bbox_inches='tight')
            with open('images/deltas.png', 'rb') as fp:
                f=discord.File(fp, filename='images/deltas.png')
                await ctx.send(file=f)

        else:
            await ctx.send("No pitching data for Pitcher ID " + pitcherID + ". Please try again.")

@bot.command(name='last', help="!last <league> <# pitches> <\"all\", \"empty\", \"loaded\", \"corners\", \"risp\", \"0out\", \"1out\", \"2out\"> <Pitcher ID>")
async def last(ctx, *args):
    numberofpitches  = int(args[1])
    league           = args[0]
    situation        = args[2]
    pitcherID        = int(args[3])     
    validpitches     = []
    situationalpitch = []
    result           = []
    inning           = []
    first            = []
    second           = []
    third            = []
    outs             = []
    thepitch         = []
    xlegend          = []
    season           = []
    session          = []
    sitch            = ""
    i = 0
    if len(args) > 3:
        if league.lower() == "milr":
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/milr/" + str(pitcherID)
            leaguetitle = "MiLR"
        elif league.lower() == "mlr":
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/mlr/" + str(pitcherID)
            leaguetitle = "MLR"
        else:
            await ctx.send("League must be MLR or MiLR.")
            pitcherurl="https://www.swing420.com/api/plateappearances/pitching/" + league.lower() + "/" + str(pitcherID)
            leaguetitle = " a league I don't know about "
    with urllib.request.urlopen(pitcherurl) as url:
        data = json.loads(url.read().decode())
    pitcher = "Nobody"
    if len(data) > 0:
        for p in data:
            pitcher = p['pitcherName']
            ################
            # BASES EMPTY  #
            ################    
            if situation.lower() == "empty": # and i < numberofpitches:
                sitch = "with bases empty"
                if p['obc'] == 0:
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #################
            # BASES LOADED  #
            #################    
            elif situation.lower() == "loaded": # and i < numberofpitches:
                sitch = "with bases loaded"
                if p['obc'] == 7: 
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #######################
            # RUNNERS ON CORNERS  #
            #######################    
            elif situation.lower() == "corners": # and i < numberofpitches:
                sitch = "with runners on the corners"
                if p['obc'] == 5:
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #########
            # RISP  #
            #########    
            elif situation.lower() == "risp": # and i < numberofpitches:
                sitch = "with runners in scoring position"
                if p['obc'] > 2:
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #################
            # 0 OUTS        #
            #################    
            elif situation.lower() == "0out": # and i < numberofpitches:
                sitch = "with no outs"
                if p['outs'] == 0: 
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #################
            # 1 OUT         #
            #################    
            elif situation.lower() == "1out": # and i < numberofpitches:
                sitch = "with one out"
                if p['outs'] == 1: 
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            #################
            # 2 OUTS        #
            #################    
            elif situation.lower() == "2out": # and i < numberofpitches:
                sitch = "with two outs"
                if p['outs'] == 2: 
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1
            ##########################
            # DEFAULT - no situation #
            ##########################
            elif situation.lower() == "all": # just show them all
                sitch = ""
                if p['pitch'] != None:
                    situationalpitch.append(p['pitch'])
                    season.append(str(p['season']))
                    session.append(str(p['session']))
                    inning.append(p['inning'])
                    result.append(p['exactResult'])
                    i = i + 1

        situationalpitch.reverse()
        season.reverse()
        session.reverse()
        inning.reverse()
        # partial list of all situational pitches - limited to # pitches in args
        limpitch  = []
        
        j = 0
        if numberofpitches > i:
            numberofpitches = i
        for t in range(numberofpitches):
            if j <= t:
                xlegend.append("S" + str(season[t]) + "." + str(session[t]) + "\n" +  inning[t] + "\nP: " + str(situationalpitch[t]))
                limpitch.append(situationalpitch[t])
                j = j + 1

        limpitch.reverse()
        xlegend.reverse()

        title = leaguetitle + ": Last " + str(numberofpitches) + " pitches from " + pitcher + " " + sitch
        data1 = limpitch
        x_axis = xlegend
        fig=plt.figure(figsize=(len(limpitch)/1.5,5)) #Creates a new figure
        ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
        pitch = ax1.plot(data1,'bo-',label='Pitch')
        plt.xticks(range(len(data1)), x_axis, size='small')
        ax1.set_ylim(0,1050)
        plt.setp(ax1.get_xticklabels(), visible=True)
        plt.suptitle(title, y=1.0, fontsize=17)
        fig.subplots_adjust(top=.92,bottom=0.2)
        fig.tight_layout()
        plt.savefig("images/sitch.png",bbox_inches='tight')
        with open('images/sitch.png', 'rb') as fp:
            f=discord.File(fp, filename='images/sitch.png')
        await ctx.send(file=f)
    else:
        await ctx.send("This player has not thrown a pitch in" + leaguetitle + " yet.")

@bot.command(name='pitcher', help="!pitcher <Name> will return list of matching pitcher names and their ID numbers")
async def name(ctx, *, arg):
    mydb = mysql.connector.connect(
        host="mysqlhost",
        user="mysqluser",
        password="mysqluserpassword",
        database="mysqldatabase"
    )
    mycursor = mydb.cursor()
    if arg == None:
        await ctx.send("Usage: !pitcher <Player Name>")
    else:
        pname = arg #re.sub(' ', '%20', arg)
        query = "SELECT DISTINCT `Pitcher`, `Pitcher ID` FROM `mlrgamelogs` WHERE `Pitcher` LIKE \"%" + pname + "%\""
        mycursor.execute(query)
        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            await ctx.send("No matches. Please check spelling of player name.")
        else:
            for id in myresult:
                await ctx.send(id[0] + " ID: "  + str(id[1]))
    mycursor.close()

@bot.command(name='batter', help="!batter <Name> will return list of matching batter names and their ID numbers")
async def name(ctx, *, arg):
    mydb = mysql.connector.connect(
        host="mysqlhost.com",
        user="mysqlusername",
        password="mysqlusernamepassowrd",
        database="mysqldatabase"
    )
    mycursor = mydb.cursor()
    if arg == None:
        await ctx.send("Usage: !batter <Player Name>")
    else:
        pname = arg #re.sub(' ', '%20', arg)
        query = "SELECT DISTINCT `Hitter`, `Hitter ID` FROM `mlrgamelogs` WHERE `Hitter` LIKE \"%" + pname + "%\""
        mycursor.execute(query)
        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            await ctx.send("No matches. Please check spelling of player name.")
        else:
            for id in myresult:
                await ctx.send(id[0] + " ID: "  + str(id[1]))
    mycursor.close()

@bot.command(name='hmmmm', help='Helps you think')
async def thinking(ctx):
    think_quotes = [
        'Whatever you\'re thinking - I\'M IN!',
        '...yes?',
        'Hmmmm indeed.',
        ':thinking:'
    ]

    response = random.choice(think_quotes)
    await ctx.send(response)

@bot.command(name='rando', help='Gives you a random number')
async def rando(ctx):
    response = random.randint(1,1000)
    await ctx.send(response)

@bot.command(name='swing', help="!swing <Player ID> <League> shows swing/diff sequences.")
async def swings(ctx, *args):
    totaldiff = 0
    diffcount = 0
    avgdiff   = 0
    if len(args) < 2:
        await ctx.send("Usage: !swing <Player ID> <League> <Season #>")
    else:
        playerID   = args[0]
        league      = args[1]
        if league.lower() == "milr":
            playerurl="https://www.swing420.com/api/plateappearances/batting/milr/" + str(playerID)
        else:
            playerurl="https://www.swing420.com/api/plateappearances/batting/mlr/" + str(playerID)
        with urllib.request.urlopen(playerurl) as url:
            data = json.loads(url.read().decode())
        res = len(data)
        if res > 0:
            # Grab player name for chart
            bname = data[0]['hitterName']
            await ctx.send('You asked to see the swing/diff details for {} in {}'.format(bname, args[1]))
            pitch    = [] # actual pitch
            swing    = [] # actual swing
            diff     = [] # swing diffs
            xlegend  = [] # x-axis to display pitch and delta values
            pitcher  = ""
            i = 0
            for p in data:
                if p['pitch'] != None: # there was a pitch (not an auto)
                    if len(args) == 3: # they specified a season
                        season = int(args[2])
                        if p['season'] == season: # so limit to that season only 
                            swing.append(p['swing'])
                            diff.append(p['diff'])
                            totaldiff = totaldiff + p['diff']
                            diffcount = diffcount + 1
                            i = i + 1
                    else: # they didn't specify a season, so get them all
                        swing.append(p['swing'])
                        diff.append(p['diff'])
                        totaldiff = totaldiff + p['diff']
                        diffcount = diffcount + 1
                        i = i + 1
            avgdiff = round(totaldiff / i)
            title = "Swing history for " + bname + " in " + league + ": " + str(i) + " swings " + " (avg diff=" + str(avgdiff) + ")"
            if len(args) == 3:
                title = title + " (S" + str(season) + " only)"
            thes = ""
            thed = ""
            for p in range(len(swing)):
                if swing[p] < 10:
                    thes = "   " + str(swing[p])
                elif swing[p] < 100:
                    thes = " " + str(swing[p])
                else:
                    thes = str(swing[p])
                
                if diff[p] < 10:
                    thed = "   " + str(diff[p])
                elif diff[p] < 100:
                    thed = " " + str(diff[p])
                else:
                    thed = str(diff[p])
                xlegend.append("S: " + thes + "\nD: " + thed)
            data1=swing
            data2=diff
            x_axis = xlegend
            fig=plt.figure(figsize=(len(swing)/1.5,5)) #Creates a new figure

            ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
            pitch = ax1.plot(data1,'bo-',label='Swing') #no need for str(x_axis)
            delta = ax1.plot(data2,'k--',label='Diff') 
            plt.xticks(range(len(data2)), x_axis, size='small')
            ax1.set_ylim(0,1050)

            #Assigning labels
            lines = pitch+delta#+line3
            labels = [l.get_label() for l in lines]
            plt.setp(ax1.get_xticklabels(), visible=True)
            plt.suptitle(title, y=1.0, fontsize=17)
            ## GRIDLINES FOR EASIER READING
            plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
            ## END GRIDLINES
            fig.subplots_adjust(top=.92,bottom=0.2)
            fig.tight_layout()
            plt.savefig("images/slog.png",bbox_inches='tight')
            #plt.close(fig)
            with open('images/slog.png', 'rb') as fp:
                f=discord.File(fp, filename='images/slog.png')
                await ctx.send(file=f)
            #plt.close()
        else:
            await ctx.send("No swing history for Player ID " + playerID + ". Please try again.")
    
@bot.command(name='cg', help='!cg <Team> <League> Shows pitch/delta results for current <Team> game in <League>')
async def cg(ctx, *args):
    if len(args) < 2: 
        await ctx.send("Usage: !cg <Team> <League>")
    else:
        # OK LET'S MAKE SURE IT'S A VALID COMBINATION OF TEAM/LEAGUE
        # We do that by generating an active games log URL and looking for a 404
        # First step, get ID of the current active game, using Team/League provided:
        team = args[0].upper()
        league = args[1].upper()
        client = pygsheets.authorize('client_secret.json')
        token = "10pQGKuqO7GEBcQ3-Wr5boPFVw0ehj9PXAFaAaQ2jVC0" # My sheet copy of gamelogs/with importrange
        sheet = client.open_by_key(token)
        if league == "MLR":
            MLR = sheet.worksheet_by_title('MLRS6')
        else:
            MLR = sheet.worksheet_by_title('MILRS6')
        rows = MLR.rows
        cols = MLR.cols
        current_session = MLR.cell((rows,20)).value
        await ctx.send( "Current session: " + str(current_session))

        pitch      = [] # actual pitch
        swing      = [] # actual swing
        diff       = [] # actual diff
        pitchseq   = [] # x-axis zero-indexed
        pitchno    = [] # x-axis 1-indexed (to display in human friendly on the graph)
        sitdata    = [] # situational data to display below x-axis bar
        delta      = [] # pitch deltas
        inning     = [] # inning, for x-axis display
        totaldelta = 0 #used to calculate average delta
        xlegend    = [] # x-axis with Inning/Pitch/Delta info
        i = 0
        otherteam = "Opponent"
        for row in MLR:
            if (row[20] == team) and row[19] == current_session and row[5] != "" and row[2] != "": # ignore autos (blanks in row[5] or [2])
                otherteam = row[21]
                pitch.append(int(row[5]))
                swing.append(int(row[2]))
                diff.append(int(row[7]))
                inning.append(row[8])
                i = i + 1
        
        # populate with the number of PAs/pitches
        for s in range(i):  
            pitchseq.append(s)
            pitchno.append(s+1) # for x-axis of the chart

        # calculate deltas
        for d in range(len(pitch)): # range -> just the pitches picked up from the opposing pitcher (does not include autos)
            if (d > 0):
                pitchd = abs(pitch[d] - pitch[d-1])
                if pitchd > 500:
                    pitchd = 1000- pitchd
                delta.append(pitchd)
                totaldelta = totaldelta + pitchd
        pitch.reverse()
        swing.reverse()
        diff.reverse()
        delta.reverse()
        delta.insert(0,0)
        inning.reverse()

        for t in range(i):  
            textsit = inning[t] + "\nP: " + str(pitch[t]) + "\nD: " + str(delta[t])
            sitdata.append(textsit)
                
        avgdelta = round(totaldelta/(len(delta)))
        #annotations = []
        #title = "PAs for " + team + " (S" + str(season) + "." + str(session) + " " + awayteam + "@" + hometeam + ")" + ". Avg delta: " + str(avgdelta)
        title = "S6." + str(current_session) + " PAs for " + team + " batting against " + str(otherteam) +  ". Avg delta: " + str(avgdelta)
        thep = ""
        thed = ""
        for p in range(len(swing)):
            #print(swing[p])
            if pitch[p] < 10:
                thep = "   " + str(pitch[p])
            elif pitch[p] < 100:
                thep = " " + str(pitch[p])
            else:
                thep = str(pitch[p])
                    
            if delta[p] < 10:
                thed = "   " + str(delta[p])
            elif delta[p] < 100:
                thed = " " + str(delta[p])
            else:
                thed = str(delta[p])
            xlegend.append(inning[p] + "     \nP: " + thep + "\nD: " + thed)
        data1=pitch
        data2=delta
        x_axis = xlegend
        fig=plt.figure(figsize=(len(pitch)/1.5,5)) #Creates a new figure

        ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
        pitch = ax1.plot(data1,'bo-',label='Pitch') #no need for str(x_axis)
        delta = ax1.plot(data2,'k--',label='Delta') 
        plt.xticks(range(len(data2)), x_axis, size='small')
        ax1.set_ylim(0,1050)

        #Assigning labels
        lines = pitch+delta
        labels = [l.get_label() for l in lines]
        plt.setp(ax1.get_xticklabels(), visible=True)
        plt.suptitle(title, y=1.0, fontsize=17)
        fig.subplots_adjust(top=.92,bottom=0.2)
        fig.tight_layout()
        plt.savefig("images/gamelog.png",bbox_inches='tight')
        with open('images/gamelog.png', 'rb') as fp:
            f=discord.File(fp, filename='images/gamelog.png')
            await ctx.send(file=f)

@bot.command(name='swingdeltas', help="!swingdeltas <Batter ID> <League> [optional:\"inning\" <#>, \"season\" <#>, \"corners\", \"loaded\", \"empty\", \"risp\", \"2out\", \"1out\", \"0out\"]. Delta histograms.")
async def batterdeltas(ctx, *args):
    totaldelta = 0
    deltacount = 0
    avgdelta   = 0
    inningno   = 0 # Will only change if they gave "inning <#>" args
    cmd        = ""
    sich       = ""
    theleague  = "S" # As in S6 for Season 6 of MLR. Change to I for MILR below
    if len(args) < 2:
        await ctx.send("Usage: !swingdeltas <Batter ID> <League> [optional:\"inning\" <#>")
    else:
        hitterID   = args[0]
        league      = args[1]
        if len(args) > 2:
            cmd = args[2]
            #print(cmd)
        if len(args) == 4:
            if args[2].lower() == "inning":
                inningno = args[3]
            elif args[2].lower() == "season":
                theseason = args[3]
        if league.lower() == "milr":
            theleague = "I"
        
        query = "SELECT `Hitter`, `Swing`, `OBC`, `Old Result`, `Outs`, `Inning`, `Season` FROM `mlrgamelogs` WHERE "
        query = query + "`Season` LIKE '" + theleague + "%' AND `Swing` > 0 AND `Hitter ID` = " + str(hitterID)
        mydb = mysql.connector.connect(
            host="mysqlhost",
            user="mysqluser",
            password="mysqluserpassword",
            database="mysqldatabase"
        )
        mycursor = mydb.cursor()
        mycursor.execute(query)
        myresult = mycursor.fetchall()
        mycursor.close()
        res = len(myresult)
        lastname = res - 1
        if res > 0:
            # Grab last name used by pitcher for chart
            hname = myresult[lastname][0]
            await ctx.send( 'You asked to see swing deltas for {} in {}'.format(hname, args[1]) )
            swing      = [] # actual swing
            delta      = [] # pitch deltas
            inning     = [] # inning, for x-axis display
            firstbase  = [] # occupied or not
            secondbase = [] # occupied or not
            thirdbase  = [] # occupied or not
            result     = [] # PA result
            outs       = [] # how many outs at time of pitch
            season     = []

            i = 0

            # Read it all in
            for s in myresult:
                swing.append(myresult[i][1])
                if myresult[i][2] == 1 or myresult[i][2] == 4 or myresult[i][2] == 5 or myresult[i][2] == 7:
                    firstbase.append("True")
                else:
                    firstbase.append("False")
                if myresult[i][2] == 2 or myresult[i][2] == 4 or myresult[i][2] == 6 or myresult[i][2] == 7:
                    secondbase.append("True")
                else:
                    secondbase.append("False")
                if myresult[i][2] == 3 or myresult[i][2] == 5 or myresult[i][2] == 6 or myresult[i][2] == 7:
                    thirdbase.append("True")
                else:
                    thirdbase.append("False")
                result.append(myresult[i][3]) # 1B, HR, CS, RGO, etc.
                outs.append(myresult[i][4]) # 0, 1 or 2
                inning.append(myresult[i][5]) # "T5"
                season.append(myresult[i][6]) # "S6"
                i = i + 1
            
            # now let's calculate deltas
            beforePitch = 0
            afterPitch   = 0
            pitchDelta   = 0
            subtitle = ""
            for p in range(i-1):
                # see what "cmd" was issued as args[2]
                if cmd.lower() == "corners": # they want to see deltas with runners on the corners
                    subtitle = "with runners on the corners."
                    if firstbase[p] == True and secondbase[p] == False and thirdbase[p] == True:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "loaded": # they want to see deltas with bases loaded
                    subtitle = "with the bases loaded."
                    if firstbase[p] == True and secondbase[p] == True and thirdbase[p] == True:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "empty": # they want to see deltas with bases empty
                    subtitle = "with the bases empty."
                    if firstbase[p] == False and secondbase[p] == False and thirdbase[p] == False:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "season" and int(theseason) > 0: # they specified a season
                    subtitle = "in season " + str(theseason) + " only."
                    if season[p] == theleague + str(theseason): #int(season): 
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1                    
                elif cmd.lower() == "risp": # they want to see deltas with runners in scoring position
                    subtitle = "with runners in scoring position."
                    if secondbase[p] == True or thirdbase[p] == True:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "2out": # they want to see deltas with 2 outs
                    subtitle = "with 2 outs."
                    if outs[p] == 2:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "1out": # they want to see deltas with 1 out
                    subtitle = "with 1 out."
                    if outs[p] == 1:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "0out": # they want to see deltas with 0 outs
                    subtitle = "with runners nobody out."
                    if outs[p] == 0:
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                elif cmd.lower() == "inning" and int(inningno) > 0: # arg[3] = inning number
                    subtitle = "in inning # " + inningno + "."
                    if (inning[p] == "T" + str(inningno) or inning[p] == "B" + str(inningno)) and (inning[p+1] == "T" + str(inningno) or inning[p+1] == "B" + str(inningno)): # only the same inning
                        beforePitch = swing[p]
                        afterPitch = swing[p+1]
                        pitchDelta = abs(beforePitch - afterPitch)
                        if pitchDelta > 500:
                            pitchDelta = 1000 - pitchDelta
                        delta.append(pitchDelta)               
                        totaldelta = totaldelta + pitchDelta
                        deltacount = deltacount + 1
                else: # they didn't specify anything, so get them all
                    subtitle = "(all situations)"
                    beforePitch = swing[p]
                    afterPitch = swing[p+1]
                    pitchDelta = abs(beforePitch - afterPitch)
                    if pitchDelta > 500:
                        pitchDelta = 1000 - pitchDelta
                    delta.append(pitchDelta)
                    totaldelta = totaldelta + pitchDelta
                    deltacount = deltacount + 1
            
            if deltacount == 0:
                nonefound = "No pitches for " + hname + " in " + league
                if cmd.lower() == "season":
                    nonefound = nonefound + " for season " + str(theseason)# str(season)
                await ctx.send(nonefound)
            if deltacount == 0: 
                avgdelta = "N/A"
            else:
                avgdelta = round(totaldelta / deltacount)
                title = "Swing deltas for " + hname + " in " + league + ". " + str(len(delta)) + " total deltas " + subtitle + " (avg delta=" + str(avgdelta) + ")"
                x = delta
                num_bins = 10
                fig, ax = plt.subplots()

                # the histogram of the data
                n, bins, patches = ax.hist(x, num_bins, density=False, rwidth=.8)
                xticks = [(bins[idx+1] + value)/2 for idx, value in enumerate(bins[:-1])]
                xticks_labels = [ "{:.0f}\nto\n{:.0f}".format(value, bins[idx+1]) for idx, value in enumerate(bins[:-1])]
                plt.xticks(xticks, labels = xticks_labels)
                
                ax.set_xlabel('Deltas')
                ax.set_title(title)
                # Tweak spacing to prevent clipping of ylabel
                fig.tight_layout()
                
                fig.tight_layout()
                plt.savefig("images/deltas.png",bbox_inches='tight')
                with open('images/deltas.png', 'rb') as fp:
                    f=discord.File(fp, filename='images/deltas.png')
                    await ctx.send(file=f)

        else:
            await ctx.send("No pitching data for Hitter ID " + hitterID + ". Please try again.")

@bot.command(name='swinglast', help="!swinglast <# swings> <\"all\", \"empty\", \"loaded\", \"corners\", \"risp\"> <Hitter ID> . MLR last # swings by situation.")
async def last(ctx, *args):
    numberofpitches = int(args[0])
    situation = args[1]
    hitterID = int(args[2])     
    validpitches     = []
    situationalpitch = []
    result           = []
    inning           = []
    first            = []
    second           = []
    third            = []
    outs             = []
    theswing         = []
    xlegend          = []
    season           = []
    session          = []
    sitch            = ""
    query = "SELECT `Hitter`, `Swing`, `Season`, `Session`, `Inning`, `Old Result` FROM `mlrgamelogs` "
    i = 0
    if len(args) > 2:
        hitterID = args[2]
        query = query + "WHERE `Hitter ID` = " + hitterID
    query = query + " AND `Season` LIKE 'S%'"
    #####################################
    # GO THROUGH THE VARIOUS SITUATIONS #
    #####################################
    ################
    # BASES EMPTY  #
    ################
    if situation.lower() == "empty": 
        sitch = "with bases empty"
        query = query + " AND OBC = 0"
    #################
    # BASES LOADED  #
    #################
    elif situation.lower() == "loaded":
        sitch = "with bases loaded"
        query = query + " AND OBC = 7"
    #######################
    # RUNNERS ON CORNERS  #
    #######################    
    elif situation.lower() == "corners": 
        sitch = "with runners on the corners"
        query = query + " AND OBC = 5"
    #########
    # RISP  #
    #########    
    elif situation.lower() == "risp": 
        sitch = "with runners in scoring position"
        query = query + " AND OBC > 1"
    ##########################
    # DEFAULT - no situation #
    ##########################
    elif situation.lower() == "all": # just show them all
        sitch = ""
    #print(query)
    # LET'S GO GRAB THE RESULTS OF THE QUERY
    mydb = mysql.connector.connect(
        host="mysqlhost",
        user="mysqlueser",
        password="mysqluserpassword",
        database="mysqldatabase"
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    mycursor.close()
    res = len(myresult)
    lastname = res - 1
    if res > 0: # there were matches
        # Grab player name for chart
        hitter = myresult[lastname][0]
        # Slurp them up
        for p in myresult:
            situationalpitch.append(myresult[i][1])
            season.append(str(myresult[i][2]))
            session.append(str(myresult[i][3]))
            inning.append(myresult[i][4])
            result.append(myresult[i][5])
            i = i + 1
        situationalpitch.reverse()
        season.reverse()
        session.reverse()
        inning.reverse()
        # partial list of all situational pitches - limited to # pitches in args
        limpitch  = []
        
        j = 0
        if numberofpitches > i:
            numberofpitches = i
        for t in range(numberofpitches):
            #print("t: " + str(t))
            if j <= t:
                xlegend.append(str(season[t]) + "." + str(session[t]) + "\n" +  inning[t] + "\nS: " + str(situationalpitch[t]))
                limpitch.append(situationalpitch[t])
                j = j + 1

        limpitch.reverse()
        xlegend.reverse()

        title = "MLR: Last " + str(numberofpitches) + " swings by " + hitter + " " + sitch
        data1 = limpitch
        x_axis = xlegend
        fig=plt.figure(figsize=(len(limpitch)/1.5,5)) #Creates a new figure
        ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
        pitch = ax1.plot(data1,'bo-',label='Swing')
        plt.xticks(range(len(data1)), x_axis, size='small')
        ax1.set_ylim(0,1050)
        plt.setp(ax1.get_xticklabels(), visible=True)
        plt.suptitle(title, y=1.0, fontsize=17)
        ## GRIDLINES FOR EASIER READING
        plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        ## END GRIDLINES
        fig.subplots_adjust(top=.92,bottom=0.2)
        fig.tight_layout()
        plt.savefig("images/sitch.png",bbox_inches='tight')
        with open('images/sitch.png', 'rb') as fp:
            f=discord.File(fp, filename='images/sitch.png')
        await ctx.send(file=f)
    else:
        await ctx.send("This player has not had a big league PA yet.")

@bot.command(name='swinglastm', help="!swinglastm <# swings> <\"all\", \"empty\", \"loaded\", \"corners\", \"risp\"> <Hitter ID> . MiLR last # swings by situation.")
async def last(ctx, *args):
    numberofpitches = int(args[0])
    situation = args[1]
    hitterID = int(args[2])     
    validpitches     = []
    situationalpitch = []
    result           = []
    inning           = []
    first            = []
    second           = []
    third            = []
    outs             = []
    theswing         = []
    xlegend          = []
    season           = []
    session          = []
    sitch            = ""
    query = "SELECT `Hitter`, `Swing`, `Season`, `Session`, `Inning`, `Old Result` FROM `mlrgamelogs` "
    i = 0
    if len(args) > 2:
        hitterID = args[2]
        query = query + "WHERE `Hitter ID` = " + hitterID
    query = query + " AND `Season` LIKE 'I%'"
    #####################################
    # GO THROUGH THE VARIOUS SITUATIONS #
    #####################################
    ################
    # BASES EMPTY  #
    ################
    if situation.lower() == "empty": 
        sitch = "with bases empty"
        query = query + " AND OBC = 0"
    #################
    # BASES LOADED  #
    #################
    elif situation.lower() == "loaded":
        sitch = "with bases loaded"
        query = query + " AND OBC = 7"
    #######################
    # RUNNERS ON CORNERS  #
    #######################    
    elif situation.lower() == "corners": 
        sitch = "with runners on the corners"
        query = query + " AND OBC = 5"
    #########
    # RISP  #
    #########    
    elif situation.lower() == "risp": 
        sitch = "with runners in scoring position"
        query = query + " AND OBC > 1"
    ##########################
    # DEFAULT - no situation #
    ##########################
    elif situation.lower() == "all": # just show them all
        sitch = ""
    #print(query)
    # LET'S GO GRAB THE RESULTS OF THE QUERY
    mydb = mysql.connector.connect(
        host="mysqlhost",
        user="mysqluser",
        password="mysqluserpassword",
        database="mysqldatabase"
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    mycursor.close()
    res = len(myresult)
    lastname = res - 1
    if res > 0: # there were matches
        # Grab player name for chart
        hitter = myresult[lastname][0]
        # Slurp them up
        for p in myresult:
            situationalpitch.append(myresult[i][1])
            season.append(str(myresult[i][2]))
            session.append(str(myresult[i][3]))
            inning.append(myresult[i][4])
            result.append(myresult[i][5])
            i = i + 1
        situationalpitch.reverse()
        season.reverse()
        session.reverse()
        inning.reverse()
        # partial list of all situational pitches - limited to # pitches in args
        limpitch  = []
        
        j = 0
        if numberofpitches > i:
            numberofpitches = i
        for t in range(numberofpitches):
            #print("t: " + str(t))
            if j <= t:
                xlegend.append(str(season[t]) + "." + str(session[t]) + "\n" +  inning[t] + "\nS: " + str(situationalpitch[t]))
                limpitch.append(situationalpitch[t])
                j = j + 1

        limpitch.reverse()
        xlegend.reverse()

        title = "MiLR: Last " + str(numberofpitches) + " swings by " + hitter + " " + sitch
        data1 = limpitch
        x_axis = xlegend
        fig=plt.figure(figsize=(len(limpitch)/1.5,5)) #Creates a new figure
        ax1=fig.add_subplot(111) #Plot with: 1 row, 1 column, first subplot.
        pitch = ax1.plot(data1,'bo-',label='Swing')
        plt.xticks(range(len(data1)), x_axis, size='small')
        ax1.set_ylim(0,1050)
        plt.setp(ax1.get_xticklabels(), visible=True)
        plt.suptitle(title, y=1.0, fontsize=17)
        ## GRIDLINES FOR EASIER READING
        plt.hlines(0, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(200, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(400, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(600, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(800, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        plt.hlines(1000, 0, len(data1), color='#b3b3b3', linestyle='dashed', label='', data=None)
        ## END GRIDLINES
        fig.subplots_adjust(top=.92,bottom=0.2)
        fig.tight_layout()
        plt.savefig("images/sitch.png",bbox_inches='tight')
        with open('images/sitch.png', 'rb') as fp:
            f=discord.File(fp, filename='images/sitch.png')
        await ctx.send(file=f)
    else:
        await ctx.send("This player has not had a big league PA yet.")


bot.run(TOKEN)