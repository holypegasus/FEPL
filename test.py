# coding: utf-8

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
    print((pos, first_name, last_name))#.decode('utf8')))

    ptyp8fn8ln.add((pos, first_name, last_name))

# print(ptyp8fn8ln)