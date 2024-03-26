import json

ft_search = json.loads('["and one", "shooting foul", "foul on the shot", "chance for", "and get fouled!", "foul strategy", "intentional foul", "fouling tactic", "strategically fouling", "fouling on purpose"]')
to_search = json.loads('["easy layup", "steal and score", "smooth layup", "composed layup", "uncontested layup", "effortless layup", "easy two points"]')
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
    for lines in messages:
        offense = ""
        defense = ""
        result = ""
        lines = lines["content"].split("\n")
        while "" in lines:
            lines.remove("")
        for j in lines:
            words = j.split(" ")

            if words[0] == 'Batter' and words[1] == 'number:' and words[2].isdigit():
                offense = words[2]
            elif words[0] == 'Bowler' and words[1] == 'number:' and words[2].isdigit():
                defense = words[2]
        print(defense + "\t" + offense)