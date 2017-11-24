# coding: utf-8

print('TEST: parse INI')
from configobj import ConfigObj


CONFIG_PATH = './config.ini'

conf = ConfigObj(CONFIG_PATH)
print(conf)

ptyp8fn8ln = set()
for pos, player_names in conf['owned'].items():
  for player_name in player_names:
    if '_' in player_name:
      first_name, last_name = player_name.split('_')
    else:
      first_name, last_name = '', player_name
    print((pos, first_name, last_name))

    ptyp8fn8ln.add((pos, first_name, last_name))



print('TEST: get & convert URL -> HTML -> JSON')
import json, requests


html = requests.get('https://fantasy.premierleague.com/drf/bootstrap').text
print(len(html))
data = json.loads(html)
print(len(data))
