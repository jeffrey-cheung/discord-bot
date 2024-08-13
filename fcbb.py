import json

ft_search = json.loads('["resorting to fouling", "Foul on purpose", "chance to score from the line", "free throws, a chance to increase their lead", "foul on the three", "fouled on the three", "potential four-point play", "tactical foul", "a four-point play chance", "strategic foul", "and draw the foul", "contact on the", "and one", "shooting foul", "foul on the shot", "chance for", "and get fouled!", "foul strategy", "intentional foul", "fouling tactic", "strategically fouling", "fouling on purpose"]')
to_search = json.loads('["steal, a layup, and they convert the free throw", "quick layup!", "turnover into points with a swift layup", "score the layup, and sink the free throw", "layup and the free throw", "turnover with a swift layup", "a layup, and they make the free throw", "turnover with a layup and a successful free throw", "steal, score, and the free throw", "steal, layup, and the free throw", "easy layup", "steal and score", "smooth layup", "composed layup", "uncontested layup", "effortless layup", "easy two points"]')
reb_search = json.loads('["rebound", "offensive board"]')

# Opening JSON file
f = open('fake_sports_json.json')

# returns JSON object as
# a dictionary
data = json.load(f)

# Iterate through the JSON array
play = ""
offense = ""
defense = ""
result = ""

for messages in data["messages"]:
    for item in messages:
        if result != '':
            play = result
        else:
            play = ""
        offense = ""
        defense = ""
        result = ""
        for i in item["embeds"]:
            lines = i["description"].splitlines()
            while "" in lines:
                lines.remove("")
            for j in lines:
                words = j.split(" ")

                if reb_search and any(word in j.lower() for word in reb_search):
                    result = 'REB'
                elif ft_search and any(word in j.lower() for word in ft_search):
                    result = 'FT'
                elif to_search and any(word in j.lower() for word in to_search):
                    result = 'TO'
                elif play == '':
                    play = 'SHOT'

                if words[1] == 'Off:' and words[3].isdigit():
                    offense = words[3]
                elif words[1] == 'Def:' and words[3].isdigit():
                    defense = words[3]
        print(offense + "\t" + defense + "\t" + play + "\t" + result)