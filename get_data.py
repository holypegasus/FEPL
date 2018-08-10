#!/usr/bin/env python3

import json, os, requests

import pandas as pd
from configobj import ConfigObj


CONFIG_PATH = 'config.ini'
CONF = ConfigObj(CONFIG_PATH)
gameweek = CONF['curr_gameweek']
DIR_INPUT_GW = os.path.join('inputs', gameweek)
DIR_OUTPUT_GW = os.path.join('outputs', gameweek)


# Get data from web API
URL_BASE = 'https://fantasy.premierleague.com/drf/%s'
types = [
  'bootstrap',  # overall
  'fixtures',
  'teams'
]


def _setup_dirs():
  if not os.path.exists(DIR_INPUT_GW):
    os.makedirs(DIR_INPUT_GW)
    DIR_PLAYERS = os.path.join(DIR_INPUT_GW, 'players')
    os.makedirs(DIR_PLAYERS)
    print('Done setting up %s & %s!'%(DIR_INPUT_GW, DIR_PLAYERS))
  if not os.path.exists(DIR_OUTPUT_GW):
    os.makedirs(DIR_OUTPUT_GW)
    print('Done setting up %s!'%(DIR_OUTPUT_GW))


def _html2json(url):
  html = requests.get(url).text
  data = json.loads(html)
  print("len(json('%s')): %s"%(url, len(data)))
  return data


# get player-json from URL
# optionally write to file
def get_player_data(pid, write_output=False):
  URL_PLAYER = 'https://fantasy.premierleague.com/drf/element-summary/%s'%pid
  dict_player = _html2json(URL_PLAYER)
  # optional write
  if write_output:
    outf_path = os.path.join(DIR_INPUT_GW, 'players', str(pid)) + '.json'
    with open(outf_path, 'w', encoding='utf8') as outf:
      json.dump(dict_player, outf)
  
  return dict_player


PATH_ALL_PLAYERS = os.path.join(DIR_INPUT_GW, 'all_player_details') + '.json'
def get_all_player_data():
  dict_players = []
  n_players = len(get_typ_data('bootstrap').get('elements'))
  # TODO get n_footballers from bootstrap intead of trying until end ?
  for pid in range(1, n_players+1):
    print(pid)
    try:
      dict_players.append(get_player_data(pid))
    except Exception as e:
      print(e)

  with open(PATH_ALL_PLAYERS, 'w', encoding='utf8') as outf:
    json.dump(dict_players, outf)

  return dict_players


def read_player_data(pid):
  outf_path = os.path.join(DIR_INPUT_GW, 'players', str(pid)) + '.json'
  with open(outf_path, 'r', encoding='utf8') as outf:
    dict_player = json.load(outf)
    return dict_player


def read_all_player_data(refresh=False):
  if refresh or not os.path.exists(PATH_ALL_PLAYERS):
    dict_players = get_all_player_data()
  else:
    with open(PATH_ALL_PLAYERS, 'r', encoding='utf8') as inf:
      dict_players = json.load(inf)

  pid2player = dict()
  for pid, dict_player in enumerate(dict_players):
    # players are 1-indexed
    pid2player[pid+1] = dict_player
  return pid2player


def get_typ_data(typ, refresh=False):
  data = _html2json(url=URL_BASE%typ)
  outf_path = os.path.join(DIR_INPUT_GW, typ) + '.json'
  if refresh or not os.path.isfile(outf_path):
    _setup_dirs()
    with open(outf_path, 'w', encoding='utf8') as outf:
      json.dump(data, outf)
      print('Written to %s !'%outf_path)

  return data


def get_all_data():
  for typ in types:
    get_typ_data(typ)



if __name__ == '__main__':
  # test individual gets

  # get_all_data()

  # get_typ_data(typ='bootstrap')

  """player-detail json-map
    player
      'history_past',
        TODO past-season characteristic perf analysis
      'fixtures_summary',
      'explain',
      'history_summary',
      'fixtures',
      'history'
        gw1
          minutes
          total_points
          bps
          ...
        ...
  """
  pid_test = 326
  # dict_player = get_player_data(pid_test, write_output=True)  # Son Heung-Min
  # dict_player = read_player_data(pid_test)
  dict_players = read_all_player_data()
  dict_player = dict_players.get(pid_test, dict())
  player_fixture_history = dict_player.get('history', [dict()])  # [gw1, gw2, ...]
  df_hist = pd.DataFrame(player_fixture_history)
  # key-stats
  df_ks = df_hist[['minutes', 'total_points', 'bps']]
  print(df_ks)
  n_games_played = len(df_ks[df_ks['minutes'] > 0])
  pt_total = df_ks['total_points'].sum()
  ppg_naive = round(pt_total/n_games_played, 1)
  print('Naive PPG = %s / %s ~= %s'%(pt_total, n_games_played, ppg_naive))
  # long-games key-stats
  thres_long = 60  # minutes considered 'long'-game
  df_ks_long = df_ks[df_ks['minutes'] >= 60]
  print(df_ks_long)
  n_games_long = len(df_ks_long)
  pt_long = df_ks_long['total_points'].sum()
  ppg_long = round(pt_long/n_games_long, 1)
  print('Long PPG = %s / %s ~= %s'%(pt_long, n_games_long, ppg_long))



