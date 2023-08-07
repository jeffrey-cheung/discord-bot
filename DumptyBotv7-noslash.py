# DumptyBot.py for Redditball API features
# NEW:
# !player to replace the old Umpty command   5/2 - moved to Dumpty on 5/9
# !ranges to replace the old Umpty command   5/6 - moved to Dumpty on 5/9
# .franges in parallel with .ranges, but using player names rather than player IDs  5/13
# .franges - changed to using old Umpty semicolon delineator and renamed to .ranges (replaced it) 5/17
# .bavg - new lookup for stat, showing histogram for league + location of player on histogram - removed on 11/12/22
#
# v3:
#   Modified fuzzy name searches to first look for an exact match (ie: "Cal") in .player and .ranges commands  5/19
# .showme - new command to develop a scatterplot comparing two stats. Could  be nonsense. 5/21
# .stats - started on replacement command (will include graphs like what's in .bavg)  5/23
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
# v5:
# Added multi-season stats options


import os
import discord, pygsheets
import matplotlib.pyplot as plt
import numpy as np
import mysql.connector
import statistics

from discord.ext import commands
from dotenv import load_dotenv
from matplotlib.ticker import FormatStrFormatter

if not os.path.exists("images"):
    os.mkdir("images")



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True
intents.members = True
intents.all()

bot = commands.Bot(command_prefix='.', description='Dumpty Bot', case_insensitive=True, intents=intents)
channel = bot.get_channel(676223227869003776)# 791753595434303519

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='player', help=".player <Player Name, Discord ID or Reddit ID>")
async def player(ctx, *, arg):
    
    if arg == None:
        await ctx.send("Usage: .player <Player Name, Discord ID or Reddit ID>")
    else:
        mydb = mysql.connector.connect(
            host="mysqlhost",
            user="mysqluser", # user="jdutton_mlrbrew",
            password="mysqluserpassword", # password="BottomsUp!",
            database="mysqluserdatabase"
        )
        mycursor = mydb.cursor()
        mycursor_exact = mydb.cursor()
        pname  = arg
        query  = "SELECT * FROM `mlrplayers` WHERE `PlayerName` LIKE \"%" + pname + "%\" OR `DiscordID` LIKE \"%" + arg + "%\" OR `RedditID` LIKE \"%" + arg + "%\""
        query_exact = "SELECT * FROM `mlrplayers` WHERE `PlayerName` = \"" + pname + "\" OR `DiscordID` = \"" + arg + "\" OR `RedditID` = \"" + arg + "\""
        #print(query_exact)
        # QUERY FIELDS:
        #    0          1        2         3            4       5   6   7   8    9       10     11       12      13
        # PlayerID	PlayerName	Team	RedditID	DiscordID	BT	PT	PB	H	Pos1	Pos2	Pos3	MLRTeam	FormatNo 
        mycursor_exact.execute(query_exact)
        myresult_exact = mycursor_exact.fetchall()
        mycursor_exact.close()
            

        mycursor.execute(query)
        myresult = mycursor.fetchall()
        mycursor.close()
        if len(myresult) > 1 and len(myresult_exact) == 0: # Not an exact match, but multiple fuzzy matches
            await ctx.send(str(len(myresult)) + " matches. Please chose one: ")
            for id in myresult:
                await ctx.send(id[1])
        elif len(myresult) == 0: # not even a fuzzy match
            await ctx.send("No matches. Check your spelling.")
        else:
            ############################################ 
            # Grab their MLR Team Name and team colors #
            ############################################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                pteam = myresult_exact[0][12]
            else:
                pteam = myresult[0][12]
            pteamshort = pteam
            if pteam == "":
                pteam = "None" # MLRTeam
                pteamshort = pteam
                pcolor = "0x000000" # Color - black for no team
            else:
                query2 = "SELECT `TeamName`, `Color` FROM `mlrparkfactors` WHERE `Team` = \"" + pteam + "\""
                mycursor2 = mydb.cursor()
                mycursor2.execute(query2)
                myresult2 = mycursor2.fetchall()
                mycursor2.close()
                pteam = myresult2[0][0] # MLRTeam
                pcolor = "0x" + myresult2[0][1] # Color - team color from logos
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                ptitle = myresult_exact[0][1] # PlayerName
            else:
                ptitle = myresult[0][1] # PlayerName
            pcolor = int(pcolor,16) # Put it in the correct format for embeds
            purl= "http://www.mlrbrewers.com/logos/" + pteamshort.lower() + ".png"
            
            #########################
            # Grab their discord ID #
            #########################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                pdisc = myresult_exact[0][4] # DiscordID
            else:
                pdisc = myresult[0][4] # DiscordID
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                if len(myresult_exact[0][4]) == 0: # DiscordID
                    pdisc = "N/A"
            else:
                if len(myresult[0][4]) == 0: # DiscordID
                    pdisc = "N/A"

            ########################
            # Grab their Reddit ID #
            ########################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                predd = myresult_exact[0][3] # RedditID
                if len(myresult_exact[0][3]) == 0: # RedditID
                    predd = "N/A"
            else:
                predd = myresult[0][3] # RedditID
                if len(myresult[0][3]) == 0: # RedditID
                    predd = "N/A"

            ########################
            # Grab their positions #
            ########################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                pposition = myresult_exact[0][9] #Pos1
                if len(myresult_exact[0][10]) > 0: #Pos2
                    pposition = pposition + "/" + myresult[0][10] # Pos2
                    if len(myresult_exact[0][11]) > 0: # Pos3
                        pposition = pposition + "/" + myresult[0][11] # Pos3
                ppt = myresult_exact[0][6] # PTName (Pitching Type, written out)
                if len(myresult_exact[0][6]) == 0: # PTName
                    ppt = "N/A"
                ppb = myresult_exact[0][7] # PBName (Pitching Bonus, written out)
                if len(myresult_exact[0][7]) == 0: # PBName
                    ppb = "N/A  "
            else: # fuzzy match
                pposition = myresult[0][9] #Pos1
                if len(myresult[0][10]) > 0: #Pos2
                    pposition = pposition + "/" + myresult[0][10] # Pos2
                    if len(myresult[0][11]) > 0: # Pos3
                        pposition = pposition + "/" + myresult[0][11] # Pos3
                ppt = myresult[0][6] # PTName (Pitching Type, written out)
                if len(myresult[0][6]) == 0: # PTName
                    ppt = "N/A"
                ppb = myresult[0][7] # PBName (Pitching Bonus, written out)
                if len(myresult[0][7]) == 0: # PBName
                    ppb = "N/A  "

            ###########################
            # Grab their batting type #
            ###########################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                pbt = myresult_exact[0][5]
                if pbt == "":
                    pbt = "N/A" # Batting Type
                else:
                    query2 = "SELECT `BTName` FROM `mlrbatting` WHERE `BT` = \"" + pbt + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    pbt = myresult2[0][0] # Batting Type, written out
            else:
                pbt = myresult[0][5]
                if pbt == "":
                    pbt = "N/A" # Batting Type
                else:
                    query2 = "SELECT `BTName` FROM `mlrbatting` WHERE `BT` = \"" + pbt + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    pbt = myresult2[0][0] # Batting Type, written out

            ############################
            # Grab their pitching type #
            ############################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                ppt = myresult_exact[0][6]
                if ppt == "":
                    ppt = "N/A" # Pitching Type
                else:
                    query2 = "SELECT `PTName` FROM `mlrpitching` WHERE `PT` = \"" + ppt + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    ppt = myresult2[0][0] # Bitching Type, written out
            else:
                ppt = myresult[0][6]
                if ppt == "":
                    ppt = "N/A" # Pitching Type
                else:
                    query2 = "SELECT `PTName` FROM `mlrpitching` WHERE `PT` = \"" + ppt + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    ppt = myresult2[0][0] # Bitching Type, written out

            #############################
            # Grab their pitching bonus #
            #############################
            if len(myresult_exact) > 0: # go with the exact match results if there was one
                ppb = myresult_exact[0][7]
                if ppb == "":
                    ppb = "N/A" # Pitching Bonus 
                else:
                    query2 = "SELECT `PBName` FROM `mlrpitchingbonus` WHERE `PBType` = \"" + ppb + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    ppb = myresult2[0][0] # Pitching Bonus Type, written out
            else:
                ppb = myresult[0][7]
                if ppb == "":
                    ppb = "N/A" # Pitching Bonus 
                else:
                    query2 = "SELECT `PBName` FROM `mlrpitchingbonus` WHERE `PBType` = \"" + ppb + "\""
                    mycursor2 = mydb.cursor()
                    mycursor2.execute(query2)
                    myresult2 = mycursor2.fetchall()
                    mycursor2.close()
                    ppb = myresult2[0][0] # Pitching Bonus Type, written out

            if len(myresult_exact) > 0: # go with the exact match results if there was one
                embed=discord.Embed(title=myresult_exact[0][1], color=pcolor)
            else: 
                embed=discord.Embed(title=myresult[0][1], color=pcolor)
            embed.set_thumbnail(url=purl)
            embed.add_field(name="Discord Name", value=pdisc, inline=True)
            embed.add_field(name="Reddit Name", value=predd, inline=True)
            embed.add_field(name="Team", value=pteam, inline=True)
            embed.add_field(name="Batting Type", value=pbt, inline=True)
            embed.add_field(name="Hand", value=myresult[0][8], inline=True)
            embed.add_field(name="Position", value=pposition, inline=True)
            embed.add_field(name="Pitching Type", value=ppt, inline=True)
            embed.add_field(name="Pitching Bonus", value=ppb, inline=True)
            embed.add_field(name="Player ID", value=myresult[0][0], inline=True)
            await ctx.send(embed=embed)
        mycursor.close()
    
@bot.command(name='ranges', help=".ranges Batter Name;Pitcher Name;Home Team Abbreviation [option: ;IFI]")
async def ranges(ctx, *, arg): # same as .player command

    args = arg.split(";")
    
    if len(args) < 3: # minimum batter name, pitcher name and park
        await ctx.send("Usage: .ranges Batter Name;Pitcher Name;Home Team Abbreviation [option: ;IFI]")
    else:
        mydb = mysql.connector.connect(
            host="mysqlhost",
            user="mysqluser",
            password="mysqluserpassword",
            database="mysqldatabase"
        )
        mycursor = mydb.cursor()
        mycursor_exact = mydb.cursor()        
        if (len(args)) > 4:
            await ctx.send("Usage: .ranges Batter Name;Pitcher Name;Home Team Abbreviation [option: ;IFI]")
        else:
            if (len(args)) == 4: # and args[3].upper() == "IFI":
                ifiarg = args[3].upper()
                ifiarg = ifiarg.strip()
                if ifiarg == "IFI":
                    ifi = True
            else: 
                ifi = False
            bname = args[0] # int(args[0])
            bname = bname.strip() # strip out leading/trailing spaces
            pname = args[1] #int(args[1])
            pname = pname.strip() # strip out leading/trailing spaces
            park  = args[2] #args[2]
            park  = park.strip() # strip out leading/trailing spaces
            minors = True # change to False if they put this in a major-league park
            majors = ['ARI','ATL', 'BAL', 'BOS', 'CHC', 'CIN', 'CLE', 'COL', 'CWS', 'DET', 'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'MTL', 'NYM', 'NYY', 'OAK', 'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR']
            for item in majors:
                if park.upper() == item:
                    minors = False
            ###########################################################################################################
            ## BEFORE WE PULL BATTER AND PITCHER DATA, NEED TO APPLY FUZZY LOGIC TO NAME AND HELP THEM GET ONE MATCH ##
            ###########################################################################################################
            ## LOOK UP PITCHER ID BASED ON NAME TYPED IN ##
            ###############################################
            batter  = ""
            pitcher = ""
            query = "SELECT DISTINCT `PlayerName`, `PlayerID` FROM `mlrplayers` WHERE `PlayerName` LIKE \"%" + pname + "%\""
            mycursor.execute(query)
            myresult = mycursor.fetchall()

            query_exact = "SELECT DISTINCT `PlayerName`, `PlayerID` FROM `mlrplayers` WHERE `PlayerName` LIKE \"" + pname + "\""
            mycursor_exact.execute(query_exact)
            myresult_exact = mycursor_exact.fetchall()

            if len(myresult) == 0 and len(myresult_exact) == 0: # Neither an exact match, nor fuzzy matches
                await ctx.send("Pitcher name not found. Please check spelling.")
            else:
                if len(myresult_exact) == 1 or len(myresult) == 1: # An exact match
                    if len(myresult_exact) == 1:
                        pitcher = myresult_exact[0][1]
                    else:
                        pitcher = myresult[0][1]
                else: # All other options (in this case, multiple fuzzy matches)
                    await ctx.send(str(len(myresult)) + " possible matches pitcher. Chose which player is pitching:")
                    for id in myresult:
                        await ctx.send(id[0])
            ##############################################
            ## LOOK UP BATTER ID BASED ON NAME TYPED IN ##
            ##############################################
            query = "SELECT DISTINCT `PlayerName`, `PlayerID` FROM `mlrplayers` WHERE `PlayerName` LIKE \"%" + bname + "%\""
            mycursor.execute(query)
            myresult = mycursor.fetchall()

            query_exact = "SELECT DISTINCT `PlayerName`, `PlayerID` FROM `mlrplayers` WHERE `PlayerName` LIKE \"" + bname + "\""
            mycursor_exact.execute(query_exact)
            myresult_exact = mycursor_exact.fetchall()

            if len(myresult) == 0 and len(myresult_exact) == 0: # Neither an exact match, nor fuzzy matches
                await ctx.send("Batter name not found. Please check spelling.")
            else:
                if len(myresult_exact) == 1 or len(myresult) == 1: # An exact match
                    if len(myresult_exact) == 1:
                        batter = myresult_exact[0][1]
                    else:
                        batter = myresult[0][1]
                else: # All other options (in this case, multiple fuzzy matches)
                    await ctx.send(str(len(myresult)) + " possible matches batter. Chose which player is batting:")
                    for id in myresult:
                        await ctx.send(id[0])
            
            #################################################
            ## LOOK UP PARK BASED ON ABBREVIATION TYPED IN ##
            #################################################
            park = park.strip()
            query = "SELECT DISTINCT `Team` FROM `mlrparkfactors` WHERE `Team` LIKE \"%" + park + "%\""
            mycursor.execute(query)
            myresult = mycursor.fetchall()
            parkname = ""

            if len(myresult) == 0:
                await ctx.send("Home team abbreviation not found. Please check again.")
            else:
                parkname = myresult[0]


            if pitcher != "" and batter !="" and parkname != "":
                ##############################################
                ## OK FUZZY LOGIC HAS ONE MATCH, GOOD TO GO ##
                ##############################################
                query_batter = "SELECT `PlayerName`, `H`, `Pos1`, `BT` FROM `mlrplayers` WHERE `PlayerID`=" + str(batter)
                query_pitcher = "SELECT `PlayerName`, `H`, `Pos1`, `PT`, `PB` FROM `mlrplayers` WHERE `PlayerID`=" + str(pitcher)
                query_park = "SELECT `ParkName`, `HR`, `3B`, `2B`, `1B`, `BB` FROM `mlrparkfactors` WHERE `Team`=\"" + park.upper() + "\""
                mydb = mysql.connector.connect(
                    host="mlrbrewers.com",
                    user="jdutton_mlrbrew",
                    password="BottomsUp!",
                    database="jdutton_mlrbrewers"
                )
                mycursor_b = mydb.cursor()
                mycursor_b.execute(query_batter)
                myresult_b = mycursor_b.fetchall()
                mycursor_b.close()
                batter_name = myresult_b[0][0]
                batter_pos = myresult_b[0][2]
                batter_hand = myresult_b[0][1]
                batting_type = myresult_b[0][3]

                mycursor_p = mydb.cursor()
                mycursor_p.execute(query_pitcher)
                myresult_p = mycursor_p.fetchall()
                mycursor_p.close()
                pitcher_name = myresult_p[0][0]
                pitching_type = myresult_p[0][3]
                pitcher_pos = myresult_p[0][2]
                pitcher_hand = myresult_p[0][1]
                pitcher_bonustype = myresult_p[0][4]

                mycursor_park = mydb.cursor()
                mycursor_park.execute(query_park)
                myresult_park = mycursor_park.fetchall()
                mycursor_park.close()
                park_name = myresult_park[0][0]
                #print(myresult_park)

                message = batter_name + " batting against " + pitcher_name + "\nAt " + park_name + " (" + park.upper() + ")"
                if ifi == True:
                    message = message + "\nInfield in."
                if pitching_type == "": # no pitching type set, so use "POS" by default until one is assigned (requires DB update)
                    pitching_type = "POS"


                ################################################
                # GRAB PITCHING BASELINE by Pitching Type (PT) #
                ################################################
                query_pitching = "SELECT `HR`, `3B`, `2B`, `1B`, `BB`, `FO`, `K`, `PO`, `RGO`, `LGO` FROM `mlrpitching` WHERE `PT`=\"" + str(pitching_type.upper()) + "\""
                mycursor_pitching = mydb.cursor()
                mycursor_pitching.execute(query_pitching)
                myresult_pitching = mycursor_pitching.fetchall()
                mycursor_pitching.close()
                ###########################################################
                # Baseline pitching stats: No bonus and POS pitching type #
                ###########################################################
                pb_HR  = 0
                pb_3B  = 0
                pb_2B  = 0
                pb_1B  = 0
                pb_BB  = 0
                pb_FO  = 0
                pb_K   = 0
                pb_PO  = 0
                pb_RGO = 0
                pb_LGO = 0
                pitching_HR  = 18
                pitching_3B  = 1
                pitching_2B  = 22
                pitching_1B  = 47
                pitching_BB  = 31
                pitching_FO  = 55
                pitching_K   = 11
                pitching_PO  = 27
                pitching_RGO = 20
                pitching_LGO = 19
                pitcher_warning = ""
                ##############
                ## MLR GAME ##
                ##############
                if minors == False: # major league game, so over-write baseline with pitching type and bonus type numbers, if they have them set
                    if (pitcher_pos == "P" or pitcher_pos == "PH") and pitching_type != "":
                        pitching_HR  = myresult_pitching[0][0]
                        pitching_3B  = myresult_pitching[0][1]
                        pitching_2B  = myresult_pitching[0][2]
                        pitching_1B  = myresult_pitching[0][3]
                        pitching_BB  = myresult_pitching[0][4]
                        pitching_FO  = myresult_pitching[0][5]
                        pitching_K   = myresult_pitching[0][6]
                        pitching_PO  = myresult_pitching[0][7]
                        pitching_RGO = myresult_pitching[0][8]
                        pitching_LGO = myresult_pitching[0][9]
                        #######################################################################################
                        # same-handedness for a pitcher in the majors = they get a bonus (if one is assigned) #
                        #######################################################################################
                        if pitcher_bonustype != "" and pitcher_hand == batter_hand:
                            query_pitchingbonus = "SELECT `HR`, `3B`, `2B`, `1B`, `BB`, `FO`, `K`, `PO`, `RGO`, `LGO` FROM `mlrpitchingbonus` WHERE `PBType`=\"" + str(myresult_p[0][4].upper()) + "\""
                            mycursor_pb = mydb.cursor()
                            mycursor_pb.execute(query_pitchingbonus)
                            myresult_pb = mycursor_pb.fetchall()
                            mycursor_pb.close()
                            pb_HR  = myresult_pb[0][0]
                            pb_3B  = myresult_pb[0][1]
                            pb_2B  = myresult_pb[0][2]
                            pb_1B  = myresult_pb[0][3]
                            pb_BB  = myresult_pb[0][4]
                            pb_FO  = myresult_pb[0][5]
                            pb_K   = myresult_pb[0][6]
                            pb_PO  = myresult_pb[0][7]
                            pb_RGO = myresult_pb[0][8]
                            pb_LGO = myresult_pb[0][9]
                        else:
                            pitcher_warning = pitcher_warning + " Pitching bonus missing: using no bonus."
                ###############
                ## MiLR GAME ##
                ###############
                else: # minor league game
                    # If they have a Pitching type set, use that (otherwise stick with the default POS type)
                    if pitching_type != "":
                        pitching_HR  = myresult_pitching[0][0]
                        pitching_3B  = myresult_pitching[0][1]
                        pitching_2B  = myresult_pitching[0][2]
                        pitching_1B  = myresult_pitching[0][3]
                        pitching_BB  = myresult_pitching[0][4]
                        pitching_FO  = myresult_pitching[0][5]
                        pitching_K   = myresult_pitching[0][6]
                        pitching_PO  = myresult_pitching[0][7]
                        pitching_RGO = myresult_pitching[0][8]
                        pitching_LGO = myresult_pitching[0][9]
                    else:
                        pitcher_warning = pitcher_warning + " Pitching type missing: using Position player."
                    # If they have a pitching bonus set and it's same-handed matchup, use that (otherwise stick with the default 0 bonus)
                    if pitcher_bonustype != "" and batter_hand == pitcher_hand:
                            query_pitchingbonus = "SELECT `HR`, `3B`, `2B`, `1B`, `BB`, `FO`, `K`, `PO`, `RGO`, `LGO` FROM `mlrpitchingbonus` WHERE `PBType`=\"" + str(myresult_p[0][4].upper()) + "\""
                            mycursor_pb = mydb.cursor()
                            mycursor_pb.execute(query_pitchingbonus)
                            myresult_pb = mycursor_pb.fetchall()
                            mycursor_pb.close()
                            pb_HR  = myresult_pb[0][0]
                            pb_3B  = myresult_pb[0][1]
                            pb_2B  = myresult_pb[0][2]
                            pb_1B  = myresult_pb[0][3]
                            pb_BB  = myresult_pb[0][4]
                            pb_FO  = myresult_pb[0][5]
                            pb_K   = myresult_pb[0][6]
                            pb_PO  = myresult_pb[0][7]
                            pb_RGO = myresult_pb[0][8]
                            pb_LGO = myresult_pb[0][9]
                    if pitcher_bonustype == "":
                        pitcher_warning = pitcher_warning + " Pitching bonus missing: using no bonus."
                ############################################
                # DONE WITH PITCHING TYPE AND BONUS SETUPS #
                ############################################

                ##############################################
                # GRAB BATTING BASELINE by Batting Type (BT) #
                ##############################################
                query_batting = "SELECT `HR`, `3B`, `2B`, `1B`, `BB`, `FO`, `K`, `PO`, `RGO`, `LGO` FROM `mlrbatting` WHERE `BT`=\"" + batting_type.upper() + "\""
                mycursor_batting = mydb.cursor()
                mycursor_batting.execute(query_batting)
                myresult_batting = mycursor_batting.fetchall()
                mycursor_batting.close()
                batting_HR  = myresult_batting[0][0]
                batting_3B  = myresult_batting[0][1]
                batting_2B  = myresult_batting[0][2]
                batting_1B  = myresult_batting[0][3]
                batting_BB  = myresult_batting[0][4]
                batting_FO  = myresult_batting[0][5]
                batting_K   = myresult_batting[0][6]
                batting_PO  = myresult_batting[0][7]
                batting_RGO = myresult_batting[0][8]
                batting_LGO = myresult_batting[0][9]
                if (minors == False) and (batter_pos == "P"):  # pitchers hitting in the majors get Pitcher hitting type, regardless of their profile
                    batting_HR  = 8
                    batting_3B  = 2
                    batting_2B  = 8
                    batting_1B  = 16
                    batting_BB  = 21
                    batting_FO  = 20
                    batting_K   = 85
                    batting_PO  = 20
                    batting_RGO = 35
                    batting_LGO = 35
                    
                matchup_HR  = pitching_HR  + batting_HR  + pb_HR  # baseline HR
                matchup_3B  = pitching_3B  + batting_3B  + pb_3B  # baseline 3B
                matchup_2B  = pitching_2B  + batting_2B  + pb_2B  # baseline 2B
                matchup_1B  = pitching_1B  + batting_1B  + pb_1B  # baseline 1B
                matchup_BB  = pitching_BB  + batting_BB  + pb_BB  # baseline BB
                matchup_FO  = pitching_FO  + batting_FO  + pb_FO  # baseline FO
                matchup_K   = pitching_K   + batting_K   + pb_K   # baseline K
                matchup_PO  = pitching_PO  + batting_PO  + pb_PO  # baseline PO
                matchup_RGO = pitching_RGO + batting_RGO + pb_RGO # baseline RGO
                matchup_LGO = pitching_LGO + batting_LGO + pb_LGO # baseline LGO

                pf_HR = (myresult_park[0][1]-1)*matchup_HR # HR bonus/penalty for this park
                pf_HR = int(round(pf_HR,0))
                pf_3B = (myresult_park[0][2]-1)*matchup_3B # 3B bonus/penalty for this park
                pf_3B = int(round(pf_3B,0))
                pf_2B = (myresult_park[0][3]-1)*matchup_2B # 2B bonus/penalty for this park
                pf_2B = int(round(pf_2B,0))
                pf_1B = (myresult_park[0][4]-1)*matchup_1B # 1B bonus/penalty for this park
                pf_1B = int(round(pf_1B,0))
                pf_BB = (myresult_park[0][5]-1)*matchup_BB # BB bonus/penalty for this park
                pf_BB = int(round(pf_BB,0))
                tpark = pf_HR + pf_3B + pf_2B + pf_1B + pf_BB
                pf_FO  = 0
                pf_K   = 0
                pf_PO  = 0
                pf_RGO = 0
                pf_LGO = 0
                tparkalloc = abs(tpark)
                while tparkalloc > 0:
                    if abs(tpark)%5 == 1:
                        pf_FO  = pf_FO  - int(tpark/abs(tpark))
                    if abs(tpark)%5 == 2:
                        pf_FO  = pf_FO  - int(tpark/abs(tpark))
                        pf_K   = pf_K   - int(tpark/abs(tpark))
                    if abs(tpark)%5 == 3:
                        pf_FO  = pf_FO  - int(tpark/abs(tpark))
                        pf_K   = pf_K   - int(tpark/abs(tpark))
                        pf_PO  = pf_PO  - int(tpark/abs(tpark))
                    if abs(tpark)%5 == 4:
                        pf_FO  = pf_FO  - int(tpark/abs(tpark))
                        pf_K   = pf_K   - int(tpark/abs(tpark))
                        pf_PO  = pf_PO  - int(tpark/abs(tpark))
                        pf_RGO = pf_RGO - int(tpark/abs(tpark))
                    if abs(tpark)%5 == 0:
                        pf_FO  = pf_FO  - int(tpark/abs(tpark))
                        pf_K   = pf_K   - int(tpark/abs(tpark))
                        pf_PO  = pf_PO  - int(tpark/abs(tpark))
                        pf_RGO = pf_RGO - int(tpark/abs(tpark))
                        pf_LGO = pf_LGO - int(tpark/abs(tpark))
                    tparkalloc = tparkalloc - 5
            
                ####################
                # Infield In Rules #
                ####################
                ifi_HR  = 0
                ifi_3B  = 0
                ifi_2B  = 0
                if ifi == True:
                    ifi_1B = 18
                else:
                    ifi_1B  = 0
                ifi_BB  = 0
                ifi_FO  = 0
                ifi_K   = 0
                ifi_PO  = 0
                if ifi == True:
                    ifi_RGO = -9
                    ifi_LGO = -9
                else:
                    ifi_RGO = 0
                    ifi_LGO = 0

                lower_HR  = 0
                range_HR  = matchup_HR  + pf_HR  + ifi_HR
                upper_HR  = lower_HR + range_HR - 1

                lower_3B  = upper_HR + 1
                range_3B  = matchup_3B  + pf_3B  + ifi_3B
                upper_3B  = lower_3B + range_3B - 1

                lower_2B  = upper_3B + 1
                range_2B  = matchup_2B  + pf_2B  + ifi_2B
                upper_2B  = lower_2B + range_2B - 1

                lower_1B  = upper_2B + 1
                range_1B  = matchup_1B  + pf_1B  + ifi_1B
                upper_1B  = lower_1B + range_1B - 1

                lower_BB  = upper_1B + 1
                range_BB  = matchup_BB  + pf_BB  + ifi_BB
                upper_BB  = lower_BB + range_BB - 1

                lower_FO  = upper_BB + 1
                range_FO  = matchup_FO  + pf_FO  + ifi_FO
                upper_FO  = lower_FO + range_FO - 1

                lower_K   = upper_FO + 1
                range_K   = matchup_K   + pf_K   + ifi_K
                upper_K   = lower_K + range_K - 1

                lower_PO  = upper_K + 1
                range_PO  = matchup_PO  + pf_PO  + ifi_PO
                upper_PO  = lower_PO + range_PO - 1

                lower_RGO = upper_PO + 1
                range_RGO = matchup_RGO + pf_RGO + ifi_RGO
                upper_RGO = lower_RGO + range_RGO -1

                lower_LGO = upper_RGO + 1
                range_LGO = matchup_LGO + pf_LGO + ifi_LGO
                upper_LGO = 500

                embed=discord.Embed(title=message, color=0xfec52e)
                to_from_HR = str(int(lower_HR)) + " - " + str(int(upper_HR))
                embed.add_field(name="HR", value=to_from_HR, inline=True)
                to_from_3B = str(int(lower_3B)) + " - " + str(int(upper_3B))
                embed.add_field(name="3B", value=to_from_3B, inline=True)
                to_from_2B = str(int(lower_2B)) + " - " + str(int(upper_2B))
                embed.add_field(name="2B", value=to_from_2B, inline=True)
                to_from_1B = str(int(lower_1B)) + " - " + str(int(upper_1B))
                embed.add_field(name="1B", value=to_from_1B, inline=True)
                to_from_BB = str(int(lower_BB)) + " - " + str(int(upper_BB))
                embed.add_field(name="BB", value=to_from_BB, inline=True)
                to_from_FO = str(int(lower_FO)) + " - " + str(int(upper_FO))
                embed.add_field(name="FO", value=to_from_FO, inline=True)
                to_from_K = str(int(lower_K)) + " - " + str(int(upper_K))
                embed.add_field(name="K", value=to_from_K, inline=True)
                to_from_PO = str(int(lower_PO)) + " - " + str(int(upper_PO))
                embed.add_field(name="PO", value=to_from_PO, inline=True)
                to_from_RGO = str(int(lower_RGO)) + " - " + str(int(upper_RGO))
                embed.add_field(name="RGO", value=to_from_RGO, inline=True)
                to_from_LGO = str(int(lower_LGO)) + " - " + str(int(upper_LGO))
                embed.add_field(name="LGO", value=to_from_LGO, inline=True)
                await ctx.send(embed=embed)
            # END OF MATCHED AND VALID BATTER/PITCHER/PARK
        # END OF CHECKING WHETHER BATTER, PITCHER and PARK ARE GIVEN, SEPARATED BY SEMICOLON

@bot.command(name='showme', help=".showme <league> <\"hitting\" or \"pitching\"> <stat1> \"vs\" <stat2> [optional: \"for\" <Player Name>]")
async def player(ctx, *, arg):

    args = arg.split(" ")
    numargs = len(args)
    cat         = ['Player', 'G', 'PA', 'AB', 'H', '1B', '2B', '3B', 'HR', 'TB', 'R', 'RBI', 'K', 'Auto K', 'BB', 'SA', 'SB', 'AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'wOBA', 'iwOBA', 'wOBA+', 'wRAA', 'iwRAA', 'wSB', 'DP Opps', 'DP', 'DP %', 'DP+', 'wRDP', 'wRDP+', 'BsR', 'BsR+', 'wRC', 'wRC+', 'DPA', 'WPA', 'WAR', 'WAR+', 'G-P', 'GS', 'IP', 'BF', 'AB-P', 'ER', 'SA', 'SB', 'H-P', '1B-P', '2B-P', '3B-P', 'HR-P', 'BB-P', 'Auto BB', 'FO-P', 'K-P', 'PO-P', 'DP-P', 'DP Opps-P', 'DP %-P', 'GO-P', '300+', '400+', 'IP+', 'H+', 'ERA', 'ERA+', 'WHIP', 'WHIP+', 'BB/6', 'K/6', 'GO/6', '300+/BF', '400+/BF', 'D/BF', 'wOBA Against', 'wOBA+ Against', 'AVG Against', 'FIP', 'pWPA', 'pWAR', 'W', 'L', 'SV', 'Team', 'Batting','Pitching', 'Hand']
    hcat        = ['      ', 'G', 'PA', 'AB', 'H', '1B', '2B', '3B', 'HR', 'TB', 'R', 'RBI', 'K', 'Auto K', 'BB', 'SA', 'SB', 'AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'wOBA', 'iwOBA', 'wOBA+', 'wRAA', 'iwRAA', 'wSB', 'DP Opps', 'DP', 'DP %', 'DP+', 'wRDP', 'wRDP+', 'BsR', 'BsR+', 'wRC', 'wRC+', 'DPA', 'WPA', 'WAR', 'WAR+']
    pcat        = ['      ', ' ', '  ', '  ', ' ', '  ', '  ', '  ', '  ', '  ', ' ', '   ', ' ', '      ', '  ', '  ', '  ', '   ', '   ', '   ', '   ', '    ', '    ', '     ', '     ', '    ', '     ', '   ', '       ', '  ', '    ', '   ', '    ', '     ', '   ', '    ', '   ', '    ', '   ', '   ', '   ', '    ', 'G',   'GS', 'IP', 'BF', 'AB',   'ER', 'SA', 'SB', 'H',   '1B',   '2B',   '3B',   'HR',   'BB',   'Auto BB', 'FO',   'K',   'PO',   'DP',   'DP Opps-P', 'DP %',   'GO',   '300+', '400+', 'IP+', 'H+', 'ERA', 'ERA+', 'WHIP', 'WHIP+', 'BB/6', 'K/6', 'GO/6', '300+/BF', '400+/BF', 'D/BF', 'wOBA Against', 'wOBA+ Against', 'AVG Against', 'FIP', 'pWPA', 'pWAR', 'W', 'L', 'SV', 'Team', 'Batting','Pitching', 'Hand']

    tickspacing = [       1,  1,   1,    1,    1,    1,    1,    1,    1,   2,    1,   1,     1,   1,        1,     1,    1,   .2,      .2,    .2,   .2,     .2,    .1,       .1,     .1,      .1,       .1,    .1,      1,      1,   .1,      1,      .2,    .2,      .2,     .2,    .5,    .5,     100,  1,     .2,    .2,     1,   1,    1,    5,    5,    1,   1,    1,    1,    1,    1,   1,    1,    1,      1,         1,    1,   1,    1,       1,        .1,   1,    1,      1,      5,     1,    .2,     .2,     .1,    .1,     1,       1,     1,      1,         1,         100,             .1,               .1,        .1,      1,      .5,     .1,    1,   1,   1,        1,        1,         1,       1]    
    if numargs < 4 or numargs == 5: # 4 = "showme mlr war vs ops", 5 = "showme mlr war vs ops for" (missing player name)
        await ctx.send("Example: .showme MLR hitting OPS vs WAR for Some Batter")
    else:
        league  = args[0]
        hitting_or_pitching = args[1] # "hitting or pitching"
        xstat   = args[2]
        vs      = args[3]
        ystat   = args[4]
        # "for" = args[5] (optional)
        pname = ""
        i   = 0
        xin = 0
        yin = 0
        message = ""
        if hitting_or_pitching.upper() == "PITCHING":
            for stat in pcat: # Use the column matches for the pitching categories
                if xstat.upper() == stat.upper():
                    xin = i
                if ystat.upper() == stat.upper():
                    yin = i
                i = i + 1
        else: # assume they meant hitting (even if they didn't - will vet/stop the script below)
            for stat in hcat: # Use the column matches for the hitting categories
                if xstat.upper() == stat.upper():
                    xin = i
                if ystat.upper() == stat.upper():
                    yin = i
                i = i + 1

        if hitting_or_pitching.upper()  != "HITTING" and hitting_or_pitching.upper() != "PITCHING":
            message = ".showme <league> <\"hitting\" or \"pitching\"> <stat1> \"vs\" <stat2> [optional: \"for\" <Player Name>]"
            await ctx.send(message)
        elif xin == 0 and yin == 0: # didn't give us the names of a column/stat from the sheets list
            message = "Sorry but I don't have " + hitting_or_pitching.lower() + " stats called " + xstat + " and " + ystat + "."
            await ctx.send(message)
        elif xin == 0 and yin != 0: # first stat is invalid
            message = "Sorry but I don't have a  " + hitting_or_pitching.lower() + " stat called " + xstat + "." 
            await ctx.send(message)
        elif yin == 0 and xin != 0: # second stat is invalid
            message = "Sorry but I don't have a  " + hitting_or_pitching.lower() + " stat called " + ystat + "." 
            await ctx.send(message)
        elif league.upper() != "MLR":
            message = "Sorry, only providing stats for MLR (not " + league.upper() + ") right now."
            await ctx.send(message)
        elif args[3].upper()  != "VS":
            message = ".showme <league> <\"hitting\" or \"pitching\"> <stat1> \"vs\" <stat2> [optional: \"for\" <Player Name>]"
            await ctx.send(message)
        else: 
            # OK STATS REQUESTED ARE GOOD, CONTINUE (and they specified a valid league and typed "vs")
            if numargs > 6:
                # They gave a player name, so let's connect it all back together from any split up
                namearg = args
                namearg.pop(0)
                namearg.pop(0)
                namearg.pop(0)
                namearg.pop(0)
                namearg.pop(0)
                namearg.pop(0)
                pname = " ".join(namearg)
                await ctx.send("One moment, while I pull up "  + xstat.upper() + " vs " + ystat.upper() + " for " + pname + " and all of " + league.upper())
            else:
                await ctx.send("One moment, while I pull up " + xstat.upper() + " vs " + ystat.upper()  + " for all of " + league.upper() )
            
            client = pygsheets.authorize('client_secret.json')
            token = "10pQGKuqO7GEBcQ3-Wr5boPFVw0ehj9PXAFaAaQ2jVC0" # My sheet copy of gamelogs/with importrange
            sheet = client.open_by_key(token)
            mlrstats = sheet.worksheet_by_title('MLRStats7')
            rows = mlrstats.rows
            cols = mlrstats.cols
            leaguex = []
            leaguey = []
            avg  = [] # col 18
            oba  = [] # col 19
            slg  = [] # col 20
            ops  = [] # col 21
            opsp = [] # col 22 (OPS+)
            war  = [] # col 41
            warp = [] # col 42 (WAR+)
            ttx = 0
            tty = 0

            i       = 0
            myindex = 0
            for row in mlrstats:
                statline = ""
                if i > 1: # was: 0
                    if pname != "" and row[0].upper() == pname.upper(): # they gave a name, and we matched it here, so make note of which row
                        myindex = i -2 # was - 1
                    if abs(float(row[xin])) != 0: # xin is column index of the first stat we want
                        leaguex.append(float(row[xin]))
                    else:
                        leaguex.append(0)

                    if abs(float(row[yin])) != 0: # yin is column index of second the stat we want
                        leaguey.append(float(row[yin]))
                    else:
                        leaguey.append(0)
                i = i + 1
            tick_spacingx = tickspacing[xin] #.2
            tick_spacingy = tickspacing[yin] #.2
            lenx = len(leaguex)
            leny = len(leaguey)
            minx = min(leaguex)
            maxx = max(leaguex)
            minops = min(leaguey)
            maxops = max(leaguey)
            fig, ax = plt.subplots() # new
            stattype = ""
            medx = float(statistics.median(leaguex))
            medy = float(statistics.median(leaguey))
            stattype = "median"
            if myindex != 0: # there was a match of a player's name somewhere
                ax.plot(leaguex[0:myindex-1], leaguey[0:myindex-1], 'r.') # all pairs before the player
                ax.plot(leaguex[myindex+1:], leaguey[myindex+1:], 'r.') # all pairs after the player
                title = pname + " " + xstat.upper() + ": " + str(leaguex[myindex]) + "  " + ystat.upper() + ": " + str(leaguey[myindex])
                ax.plot(leaguex[myindex], leaguey[myindex], 'bo', label=title) # print out JUST this player's dot by itself
                ax.legend()
            else:
                await ctx.send("Sorry, couldn't find a player named " + pname + ".")
                ax.plot(leaguex, leaguey, 'r.')
            ax.set_xlabel(xstat.upper())
            ax.set_ylabel(ystat.upper())
            charttitle = xstat.upper() + " vs " + ystat.upper() + " (" + league.upper() +" " + stattype + ": "
            charttitle = charttitle + "{thex:.3f}".format(thex=medx)
            charttitle = charttitle + " vs {they:.3f}".format(they=medy)
            charttitle = charttitle + ")"
            ax.set_title( charttitle )
            fig.tight_layout()
            plt.savefig("images/showme.png",bbox_inches='tight')
            with open('images/showme.png', 'rb') as fp:
                f=discord.File(fp, filename='images/showme.png')
                await ctx.send(file=f)
            plt.close()

@bot.command(name='stats', help=".stats <League> <Season#> [<Player Name>]")
async def stats(ctx, *, arg):

    args = arg.split(" ")
    numargs = len(args)
    
    season = ""
    player = ""
    league = ""
    mlrsheetname  = "MLRStats"
    milrsheetname = "MILRStats"

    if numargs < 2: # gotta spell it out
        await ctx.send("Usage: .stats <League> <Season#> [<Player Name>]")
    else: # We got enough to go on (at least the league and season)
        league = args[0]
        season = args[1]
        if season.upper() == "8": 
            season = "8"
        elif season.upper() == "7": 
            season = "7"
        elif season.upper() == "6": # Let them know only MLR S6 for now
            season = "6"
        elif season.upper() == "5":
            season = "5"
        elif season.upper() == "4":
            season = "4"
        elif season.upper() == "3":
            season = "3"
        elif season.upper() == "2":
            season = "2"
        else:
            await ctx.send("I don't know a S" + season.upper() + ". Showing S7 stats instead.")
            season = "7"
        if numargs == 2: # they didn't specify a player name, so assume they meant themselves and look up by Discord Name#Discriminator
            league = args[0]
            season = args[1]
            name = ctx.message.author.name
            discrim = ctx.message.author.discriminator
            discordid = name + "#" + discrim
            mydb = mysql.connector.connect(
                host="mysqlhost",
                user="mysqluser",
                password="mysqluserpassword",
                database="mysqldatabase"
            )
            mycursor = mydb.cursor()
            query = "SELECT `PlayerName` FROM `mlrplayers` WHERE `DiscordID` LIKE \"%" + discordid + "%\""
            mycursor.execute(query)
            myresult = mycursor.fetchall()
            mycursor.close()
            if len(myresult) == 0:
                await ctx.send("Can't find " + discordid + " in the stats records. Try giving a player name instead.")
            else:
                player = myresult[0][0] # snag the first one, now use that to look up stats on the sheets
        else: # they gave us all the args, inlcuding a player name, so use that name
            name = args
            name.pop(0)
            name.pop(0)
            player = " ".join(name)
        ##############################################################################################################################
        ## OK let's grab their stats from the sheets. Will pick up BA OBP SLG and OPS, along with PAs for everyone, and this player ##
        ## and provide the information in written response as per historical use of Umpty, plus also provide 4 graphs showing where ##
        ## this player is in the league's histogram, along with league median for each stat. Fancy!                                 ##
        ##############################################################################################################################
        # PA  = index 2
        # AVG = index 17
        # OBP = index 18
        # SLG = index 19
        # OPS = index 20
        client    = pygsheets.authorize('client_secret.json')
        token    = "10pQGKuqO7GEBcQ3-Wr5boPFVw0ehj9PXAFaAaQ2jVC0" # My sheet copy of gamelogs/with importrange
        sheet    = client.open_by_key(token)
        mlrsheetname = mlrsheetname + season.upper()
        milrsheetname = milrsheetname + season.upper()
        if league.upper() == "MLR":
            mlrstats = sheet.worksheet_by_title(mlrsheetname)
        else:
            mlrstats = sheet.worksheet_by_title(milrsheetname)
        rows     = mlrstats.rows
        cols     = mlrstats.cols
        leaguex  = []
        leaguey  = []
        pa       = [] # index 2
        avg      = [] # index 17
        obp      = [] # index 18
        slg      = [] # index 19
        ops      = [] # index 20
        i        = 0
        myindex  = 0
        xin      = 0
        yin      = 0
        mypa     = 0
        myavg    = 0
        myobp    = 0
        myslg    = 0
        myops    = 0
        for row in mlrstats:
            statline = ""
            if i > 1:
                if player != "" and row[0].upper() == player.upper(): # we matched the given/assumed player name here, so make note of which row
                    myindex = i - 1
                    mypa = float(row[2])
                    myavg = float(row[17])
                    myobp = float(row[18])
                    myslg = float(row[19])
                    myops = float(row[20])
                # SLURP UP PAs
                if abs(float(row[2])) > 0: # xin is column index of the first stat we want
                    pa.append(float(row[2]))
                # SLURP UP AVG
                if abs(float(row[17])) > 0: # xin is column index of the first stat we want
                    avg.append(float(row[17]))
                # SLURP UP OBP
                if abs(float(row[18])) > 0: # xin is column index of the first stat we want
                    obp.append(float(row[18]))
                # SLURP UP SLG
                if abs(float(row[19])) > 0: # xin is column index of the first stat we want
                    slg.append(float(row[19]))
                # SLURP UP OPS
                if abs(float(row[20])) > 0: # xin is column index of the first stat we want
                    ops.append(float(row[20]))
            i = i + 1
        # DONE SLURPING
        med_avg = float(statistics.median(avg))
        med_obp = float(statistics.median(obp))
        med_slg = float(statistics.median(slg))
        med_ops = float(statistics.median(ops))
        if myindex == 0: # didn't match a player name
            # Let's use league median to chose which bar is red in the subplots
            myavg = med_avg
            myobp = med_obp
            myslg = med_slg
            myobp = med_obp
        tickspacing = .2
        fig, ((BA, OBP), (SLG, OPS)) = plt.subplots(nrows=2, ncols=2)

        num_bins = 100

        ######################################
        ## SUBPLOT AXIS FOR BATTING AVERAGE ##
        ######################################
        n, bins, ba_patches = BA.hist(avg, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "AVG"
        if myindex !=0:
            title = "AVG: {theavg:.3f}".format(theavg=myavg)
        textstr = "League " + r'$\mathrm{median}=%.3f$' % (med_avg, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        BA.text(0.42, 0.90, textstr, transform=BA.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        BA.set_title(title, color='r')
        BA.set_ylabel("# Players", color='b')
        BA.set_xticks(np.arange(0, 1.001, .1))
        BA.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        BA.tick_params(axis='x', rotation=45)
        if myavg != 0: # we matched to a player, here's their average
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            i = 0
            for i, rectangle in enumerate(ba_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myavg)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            ba_patches[index_of_bar_to_label].set_color('r')
        ##########################
        ## SUBPLOT AXIS FOR OBP ##
        ##########################
        n, bins, obp_patches = OBP.hist(obp, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "OBP"
        if myindex != 0:
            title = "OBP: {theobp:.3f}".format(theobp=myobp)
        textstr = "League " + r'$\mathrm{median}=%.3f$' % (med_obp, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        OBP.text(.42, 0.90, textstr, transform=OBP.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        OBP.set_title(title, color='r')
        OBP.set_xticks(np.arange(0, 1.001, .1))
        OBP.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        OBP.tick_params(axis='x', rotation=45)
        if myobp != 0: # we matched to a player, here's their OBP
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(obp_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myobp)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            obp_patches[index_of_bar_to_label].set_color('r')
        ##########################
        ## SUBPLOT AXIS FOR SLG ##
        ##########################
        n, bins, slg_patches = SLG.hist(slg, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "SLG"
        if myindex != 0:
            title = "SLG: {theslg:.3f}".format(theslg=myslg)
        textstr = "League " + r'$\mathrm{median}=%.3f$' % (med_slg, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        SLG.text(.42, 0.90, textstr, transform=SLG.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        SLG.set_title(title, color='r')
        SLG.set_ylabel("# Players", color='b')
        SLG.set_xticks(np.arange(0, max(slg)+.001, max(slg)/10))
        SLG.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        SLG.tick_params(axis='x', rotation=45)
        if myslg != 0: # we matched to a player, here's their SLG
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(slg_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myslg)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            slg_patches[index_of_bar_to_label].set_color('r')
        ##########################
        ## SUBPLOT AXIS FOR OPS ##
        ##########################
        n, bins, ops_patches = OPS.hist(ops, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "OPS"
        if myindex != 0:
            title = "OPS: {theops:.3f}".format(theops=myops)
        textstr = "League " + r'$\mathrm{median}=%.3f$' % (med_ops, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        OPS.text(.42, 0.90, textstr, transform=OPS.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        OPS.set_title(title, color='r')
        OPS.set_xticks(np.arange(0, max(ops)+.001, max(ops)/10))
        OPS.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        OPS.tick_params(axis='x', rotation=45)
        if myops != 0: # we matched to a player, here's their OPS
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(ops_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myops)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            ops_patches[index_of_bar_to_label].set_color('r')
        ##########################
        # SAVE THE 4-plot figure #
        ##########################
        fig.subplots_adjust(hspace=.5)
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        if myindex !=0:
            title = player + " stats for " + league + " S" + season + " (" + str(mypa) + " PAs)"
        else: # didn't match a player
            title = league + " S" + season + " stats"
            message = "Couldn't find a player named \"" + player + "\". Please check the spelling. Here's the entire league though:"
            await ctx.send(message)
        fig.suptitle(title)
        plt.savefig("images/stats.png",bbox_inches='tight')
        with open('images/stats.png', 'rb') as fp:
            f=discord.File(fp, filename='images/stats.png')
            await ctx.send(file=f)
        plt.close()
        
            
@bot.command(name='pstats', help=".pstats <League> <Season#> [<Player Name>]")
async def pstats(ctx, *, arg):

    args = arg.split(" ")
    numargs = len(args)
    
    season = ""
    player = ""
    league = ""
    mlrsheetname  = "MLRStats"
    milrsheetname = "MILRStats"

    if numargs < 2: # gotta spell it out
        #discid = ctx.message.author.mention
        await ctx.send("Usage: .pstats <League> <Season#> [<Player Name>]")
    else: # We got enough to go on (at least the league and season)
        league = args[0]
        season = args[1]
        if season.upper() == "7": 
            season = "7"
        elif season.upper() == "6": # Let them know only MLR S6 for now
            #await ctx.send("Currently only showing stats for S6. More historial stats to come.")
            season = "6"
        elif season.upper() == "5":
            season = "5"
        elif season.upper() == "4":
            season = "4"
        elif season.upper() == "4":
            season = "3"
        elif season.upper() == "2":
            season = "2"
        else:
            await ctx.send("I don't know a S" + season.upper() + ". Showing S7 stats instead.")
            season = "7"
        if numargs == 2: # they didn't specify a player name, so assume they meant themselves and look up by Discord Name#Discriminator
            league = args[0]
            season = args[1]
            name = ctx.message.author.name
            discrim = ctx.message.author.discriminator
            discordid = name + "#" + discrim
            mydb = mysql.connector.connect(
                host="mysqlhost",
                user="mysqluser",
                password="mysqluserpassword",
                database="mysqldatabase"
            )
            mycursor = mydb.cursor()
            query = "SELECT `PlayerName` FROM `mlrplayers` WHERE `DiscordID` LIKE \"%" + discordid + "%\""
            mycursor.execute(query)
            myresult = mycursor.fetchall()
            mycursor.close()
            if len(myresult) == 0:
                await ctx.send("Can't find " + discordid + " in the stats records. Try giving a player name instead.")
            else:
                player = myresult[0][0] # snag the first one, now use that to look up stats on the sheets
        else: # they gave us all the args, inlcuding a player name, so use that name
            name = args
            name.pop(0)
            name.pop(0)
            player = " ".join(name)
        ##############################################################################################################################
        ## OK let's grab their stats from the sheets. Will pick up BA OBP SLG and OPS, along with PAs for everyone, and this player ##
        ## and provide the information in written response as per historical use of Umpty, plus also provide 4 graphs showing where ##
        ## this player is in the league's histogram, along with league median for each stat. Fancy!                                 ##
        ##############################################################################################################################
        # IP   = index 44
        # ERA  = index 68
        # WHIP = index 70
        # D/BF = index 77
        client    = pygsheets.authorize('client_secret.json')
        token    = "10pQGKuqO7GEBcQ3-Wr5boPFVw0ehj9PXAFaAaQ2jVC0" # My sheet copy of gamelogs/with importrange
        sheet    = client.open_by_key(token)
        mlrsheetname = mlrsheetname + season.upper()
        milrsheetname = milrsheetname + season.upper()
        if league.upper() == "MLR":
            mlrstats = sheet.worksheet_by_title(mlrsheetname)
        else:
            mlrstats = sheet.worksheet_by_title(milrsheetname)
        rows     = mlrstats.rows
        cols     = mlrstats.cols
        leaguex  = []
        leaguey  = []
        ip       = [] # index 44
        era      = [] # index 68
        whip     = [] # index 70
        dbf      = [] # index 77
        i        = 0
        myindex  = 0
        xin      = 0
        yin      = 0
        myip     = 0
        myera    = 0
        mywhip   = 0
        mydbf    = 0
        # Different columns for previous seasons
        if season.upper() == "2":
            ipcol = 16
            eracol = 22
            whipcol = 23
            dbfcol = 28  # Not tracked in S2
        elif season.upper() == "3":
            if league.upper() == "MILR":
                ipcol = 16
            else:
                ipcol = 39
            if league.upper() == "MILR":
                eracol = 22
            else:
                eracol = 53
            if league.upper() == "MILR":
                whipcol = 23
            else:
                whipcol = 55
            if league.upper() == "MILR":
                dbfcol = 28  # Not tracked in S2
            else:
                dbfcol = 58
        elif season.upper() == "4":
            ipcol = 44
            eracol = 61
            whipcol = 63
            dbfcol = 66
        elif season.upper() == "5":
            ipcol = 44
            if league.upper() == "MILR":
                eracol = 61
            else:
                eracol = 67
            if league.upper() == "MILR":
                whipcol = 63
            else:
                whipcol = 69
            if league.upper() == "MILR":
                dbfcol = 66
            else:
                dbfcol = 76
        else:
            # Season 7 & 6 columns
            ipcol = 44
            eracol = 68
            whipcol = 70
            dbfcol = 77
        for row in mlrstats:
            statline = ""
            if i > 1: # was 0
                if player != "" and row[0].upper() == player.upper(): # we matched the given/assumed player name here, so make note of which row
                    myindex = i - 1 
                    myip   = float(row[ipcol])
                    myera  = float(row[eracol])
                    mywhip = float(row[whipcol])
                    mydbf  = float(row[dbfcol])
                # SLURP UP IP
                if abs(float(row[ipcol])) > 0: # xin is column index of the first stat we want
                    ip.append(float(row[ipcol]))
                # SLURP UP ERA
                if row[eracol] != "Inf": # some pitching ratios read "Inf" where no outs were gathered
                    if abs(float(row[eracol])) > 0: # xin is column index of the first stat we want
                        era.append(float(row[eracol]))
                # SLURP UP WHIP
                if row[whipcol] != "Inf": # some pitching ratios read "Inf" where no outs were gathered
                    if abs(float(row[whipcol])) > 0: # xin is column index of the first stat we want
                        whip.append(float(row[whipcol]))
                # SLURP UP DBF - stat didn't exist in MILR until S4, and MLR until S3
                if abs(float(row[dbfcol])) < 500: # xin is column index of the first stat we want
                    dbf.append(float(row[dbfcol]))
            i = i + 1
        # DONE SLURPING
        med_ip  = float(statistics.median(ip))
        med_era  = float(statistics.median(era))
        med_whip = float(statistics.median(whip))
        med_dbf = float(statistics.median(dbf))
        if myindex == 0: # didn't match a player name
            # Let's use league median to chose which bar is red in the subplots
            myip = med_ip
            myera = med_era
            mywhip = med_whip
            mydbf = med_dbf
        tickspacing = .2
        fig, ((IP, ERA), (WHIP, DBF)) = plt.subplots(nrows=2, ncols=2)

        num_bins = 100

        ######################################
        ## SUBPLOT AXIS FOR INNINGS PITCHED ##
        ######################################
        n, bins, ip_patches = IP.hist(ip, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "IP"
        if myindex !=0:
            title = title + ": " + str(myip)
        textstr = "League " + r'$\mathrm{median}=%.1f$' % (med_ip, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        IP.text(0.42, 0.90, textstr, transform=IP.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        IP.set_title(title, color='r')
        IP.set_ylabel("# Players", color='b')
        IP.set_xticks(np.arange(0, max(ip)+1, int(max(ip)/10)))
        IP.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        IP.tick_params(axis='x', rotation=45)
        if myip != 0: # we matched to a player, here's their average
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            i = 0
            for i, rectangle in enumerate(ip_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myip)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            ip_patches[index_of_bar_to_label].set_color('r')
        ##########################
        ## SUBPLOT AXIS FOR ERA ##
        ##########################
        n, bins, era_patches = ERA.hist(era, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "ERA"
        if myindex !=0:
            title = title + ": " + str(myera)
        textstr = "League " + r'$\mathrm{median}=%.2f$' % (med_era, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        ERA.text(.42, 0.90, textstr, transform=ERA.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        ERA.set_title(title, color='r')
        ERA.set_xticks(np.arange(0, max(era)+.1, max(era)/10))
        ERA.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ERA.tick_params(axis='x', rotation=45)
        if myera != 0: # we matched to a player, here's their OBP
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(era_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - myera)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            era_patches[index_of_bar_to_label].set_color('r')
        ###########################
        ## SUBPLOT AXIS FOR WHIP ##
        ###########################
        n, bins, whip_patches = WHIP.hist(whip, num_bins, facecolor='blue', alpha=0.5, rwidth=1)
        title = "WHIP"
        if myindex !=0:
            title = title + ": " + str(mywhip)
        textstr = "League " + r'$\mathrm{median}=%.1f$' % (med_whip, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        WHIP.text(.42, 0.90, textstr, transform=WHIP.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        WHIP.set_title(title, color='r')
        WHIP.set_ylabel("# Players", color='b')
        WHIP.set_xticks(np.arange(0, max(whip)+.1, max(whip)/10))
        WHIP.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        WHIP.tick_params(axis='x', rotation=45)
        if mywhip != 0: # we matched to a player, here's their SLG
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(whip_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - mywhip)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            whip_patches[index_of_bar_to_label].set_color('r')
        ##########################
        ## SUBPLOT AXIS FOR DBF ##
        ##########################
        n, bins, dbf_patches = DBF.hist(dbf, 40, facecolor='blue', alpha=0.5, rwidth=1)
        title = "DBF"
        if myindex !=0:
            title = title + ": " + str(mydbf)
        textstr = "League " + r'$\mathrm{median}=%.0f$' % (med_dbf, )
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        DBF.text(.42, 0.90, textstr, transform=DBF.transAxes, fontsize=8, verticalalignment='top', bbox=props)
        DBF.set_title(title, color='r')
        DBF.set_xticks(np.arange(0, max(dbf)+1, max(dbf)/10))
        DBF.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        DBF.tick_params(axis='x', rotation=45)
        if mydbf != 500: # we matched to a player, here's their OPS
            min_distance = float("inf")  # initialize min_distance with infinity
            index_of_bar_to_label = 0

            for i, rectangle in enumerate(dbf_patches):  # iterate over every bar
                tmp = abs(  # tmp = distance from middle of the bar to bar_value_to_label
                    (rectangle.get_x() + (rectangle.get_width() * (1 / 2))) - mydbf)
                if tmp < min_distance:  # we are searching for the bar with x cordinate closest to bar_value_to_label
                    min_distance = tmp
                    index_of_bar_to_label = i

            dbf_patches[index_of_bar_to_label].set_color('r')
        ##########################
        # SAVE THE 4-plot figure #
        ##########################
        fig.subplots_adjust(hspace=.5)
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        if myindex !=0:
            title = player + " stats for " + league + " S" + season
        else: # didn't match a player
            title = league + " S" + season + " stats"
            message = "Couldn't find a pitcher named \"" + player + "\". Please check the spelling. Here's the entire league though:"
            await ctx.send(message)
        fig.suptitle(title)
        plt.savefig("images/pstats.png",bbox_inches='tight')
        with open('images/pstats.png', 'rb') as fp:
            f=discord.File(fp, filename='images/pstats.png')
            await ctx.send(file=f)
        plt.close()


bot.run(TOKEN)