import requests
import time

token = 'MjUyMzA0MDY3MjYxNDk3MzQ0.G8aV8p.VMsEMW4PWhlyfASWeCJPvm55zLC2GPNxJhrzIQ'
# TEN
channel = {'HVD': '1111347980851744880', 'TEN': '1111348065400533054', 'TOL': '1111348176096600064', 'UCC': '1111347848454352986', 'UGA': '1111348112011825282', 'WSU': '1111348230723223593'}

ids = [
    157651086772011009
]

for i in ids:
    time.sleep(1)
    # player = (requests.get(f"https://discord.com/api/v9/guilds/593511953952145418/messages/search?author_id={i}", headers={'Authorization': token})).json()

    # player = (requests.get(f"https://discord.com/api/v9/guilds/593511953952145418/messages/search?channel_id={channel['HVD']}&author_id={i}", headers={'Authorization': token})).json()

    player = (requests.get(f"https://discord.com/api/v9/guilds/593511953952145418/messages/search?min_id=1120246589030400000&max_id=1123145691955200000&channel_id={channel['HVD']}&author_id={i}", headers={'Authorization': token})).json()

    print(player['total_results'])
