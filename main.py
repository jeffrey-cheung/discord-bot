#import config
import discord
import random
import requests
import io
import os
import matplotlib.pyplot as plt

from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!help':
        await message.channel.send(
            "```\n" +
            "!help      prints this message\n" +
            "!hype      HYPE\n" +
            "!pitches   [league] [playerId] [optional:numberOfPitches]\n" +
            "!random    random number between 1-1000\n" +
            "```"
        )

    if message.content.startswith('!pitches'):
        params = message.content[9:].split()
        if(len(params) < 2 or len(params) > 3):
            await message.channel.send(
               "```\n" +
               "!pitches [league] [playerId] [optional:numberOfPitches]\n" +
               "```"
            )
            return
        league = params[0].upper()
        pitcherid = params[1]
        N = 50
        if (len(params) == 3):
            N = int(params[2])
        player = (requests.get("https://www.swing420.com/api/players/id/" + pitcherid)).json()
        response = (requests.get("https://www.swing420.com/api/plateappearances/pitching/" + league + "/" + pitcherid)).json()

        pitches = []
        for x in response:
            if (x['pitch'] != 0) & (x['swing'] != 0) & (x['session'] != 0):
                pitches.append(x['pitch'])
        pitches = pitches[-N:]

        N = len(pitches)
        list_of_numbers = list(range(1, N+1))

        plt.title(player['playerName'] + ' last ' + str(N) + " pitches in " + str(league))
        plt.ylim(0, 1000)
        plt.xlim(0, N+1)
        plt.grid(True)
        plt.plot(list_of_numbers, pitches, marker='o', linestyle='dashed', linewidth=1, markersize=7)
        plt.savefig('graph.png')
        plt.close()

        with open('graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')

        await message.channel.send(file=image)
        os.remove('graph.png')

    if message.content == '!hype':
        await message.channel.send(random.choice(hype_list))

    if message.content == '!random':
        await message.channel.send(random.randint(1, 1000))

hype_list = [
    "https://tenor.com/view/scuba-dive-dolphin-gif-9675090",
    "https://tenor.com/view/ok-scuba-diving-under-water-swimming-exploring-gif-11835155",
    "https://tenor.com/view/free-driving-wil-dasovich-scuba-diving-swimming-deep-diving-gif-25457081",
    "https://tenor.com/view/current-scubadiving-notroublesjustbubbles-ntjb-gif-23024747",
    "https://cdn.discordapp.com/attachments/1030138801986732134/1030142511013974036/image0.gif",
    "https://tenor.com/view/vizil%C5%91-b%C5%B1v%C3%A1r-b%C5%B1v%C3%A1rbuli-nemjosszbuvar-nemj%C3%B6sszb%C5%B1v%C3%A1r-gif-25724207",
    "https://tenor.com/view/dive-tub-summer-gif-5789350",
    "https://tenor.com/view/the-book-of-pooh-pooh-scuba-diving-gear-swimming-gear-snorkeling-gif-22305904",
    "https://cdn.discordapp.com/attachments/1030138801986732134/1030154255740457023/200w.gif",
    "https://tenor.com/view/fish-dance-swim-scuba-shark-gif-16183268",
    "https://tenor.com/view/pump-pump-it-pump-it-up-gif-22218192",
    "https://tenor.com/view/snorkel-swimming-driving-ship-gif-10705072",
    "https://tenor.com/view/shummer-death_dive-dive-fail-failed-dive-dive-gif-12569456"
]

keep_alive()
client.run(os.getenv("TOKEN"))