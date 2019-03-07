#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import csv, datetime, json, os

from configobj import ConfigObj

import analyze
import get_data
from get_data import CONF
GAMEWEEK = int(CONF['curr_gameweek'])


def get_watchlist(conf):  # set([ (pos, first_name, last_name) ])
  def get_names_first8last(player_name):
    if '_' in player_name:
      name_first, name_last = player_name.split('_')
    else:
      name_first, name_last = '', player_name
    return name_first, name_last

  def get__by_section(section):
    pos_fn_ln2sect = dict()
    for pos, player_names in conf[section].items():
      for player_name in player_names:
        name_first, name_last = get_names_first8last(player_name)
        key = (pos, name_first, name_last)
        pos_fn_ln2sect[key] = section
    return pos_fn_ln2sect

  players_owned = get__by_section('owned')
  players_monit = get__by_section('monit')
  # if in both, owned overrides
  players_watched = {**players_monit, **players_owned}
  return players_watched
WATCHLIST = get_watchlist(CONF)

# annotate watchlisted players
def watch(pos, fn, ln, watchlist):
  key_fn8ln = (pos, fn, ln)
  key_ln = (pos, '', ln)
  key = key_ln if key_ln in watchlist else key_fn8ln

  section = watchlist.get(key)  # owned | monit
  mark = section[0] if section else ''
  # print((key, mark))
  return mark


# keys TODO -> namedtuple
WATCHED = 'W'
FIRST_NAME = 'I'
WEB_NAME = 'web_name'
TEAM = 'team'
PLAYER_TYPE = 'T'
VApM = 'VA/M'
VApML = 'VA/ML'  # G60
POINTS = 'pt'
GAMES = 'g'
PpG = 'p/g'
PpGL = 'p/gl'  # G60
FORM = 'form'
MINUTES = 'min'
MinPct = 'm%'  # % of possible minutes played
MpG = 'm/g'
PRICE = 'px'
SELECTED = '%'
NET_TRANSFER = 'txn'
GROWTH_FACTOR = 'gf'
# compute Player-DictS
TYP2MIN_PRICE = {
  'G': 4.0,
  'D': 4.0,
  'M': 4.5,
  'F': 4.5,
  }
CACHE = dict()  # TMP pid -> analyses
BASE_PTS = 2.0
def gen_pds(n_mgrs, teams, players, player_types, dict_player_detail):
  # TODO enrich w/ player detail data 
  pds = []  # player-dicts
  for p in players:
    # TODO refactor data-get & analysis
    _id = p.get('id')
    if _id in CACHE:
      _analyses = CACHE.get(_id)
    else:
      try:
        _analyses = analyze.calc_ppgs(_id, dict_player_detail.get(_id))
      except:
        _analyses = {'ppg_long': 0.}
      CACHE[_id] = _analyses

    ppg_long = _analyses.get('ppg_long', 0.)
    ###
    first_name = p.get('first_name').split()[0][0]
    web_name = p.get('web_name')
    team = teams[p.get('team')]
    p_type = player_types.get(p.get('element_type'))[0][0]
    form = float(p.get('form'))
    price = p.get('now_cost')/10.0
    total_pts = p.get('total_points')
    ppg = float(p.get('points_per_game', 0.0))  # points/game
    n_games = int(round(total_pts / ppg)) if ppg!=0.0 else 0
    _ppgar = ppg - BASE_PTS  # points/game above-replacement
    vapm = round(_ppgar / price, 2)  # value-added/game/million
    _ppglar = ppg_long - BASE_PTS
    vapml = round(_ppglar / price, 2)
    _typ_min_price = TYP2MIN_PRICE.get(p_type)
    _price_above_min = price - _typ_min_price + 0.5
    vapmar = round(_ppgar / _price_above_min, 2)  # value-added/game/million above-replacement
    minutes = p.get('minutes')
    minute_percent = round(p.get('minutes')/((GAMEWEEK-1)*90) *100)
    min_p_game = round(minutes / n_games) if n_games!=0 else 0
    selected_by_percent = float(p.get('selected_by_percent'))
    watched = watch(p_type, first_name, web_name, WATCHLIST)
    net_transfer = p.get('transfers_in_event') - p.get('transfers_out_event')
    growth_factor = 0. if selected_by_percent==0. else round(net_transfer / n_mgrs * 100 / selected_by_percent * 100)

    pd = {  # player dict
      WATCHED: watched,
      TEAM: team,
      FIRST_NAME: first_name,
      WEB_NAME: web_name,
      PLAYER_TYPE: p_type,
      FORM: form,
      VApM: vapm,
      VApML: vapml,
      PRICE: price,
      PpG: ppg,
      PpGL: ppg_long,
      POINTS: total_pts,
      GAMES: n_games,
      MINUTES: minutes,
      MinPct: minute_percent,
      MpG: min_p_game,
      SELECTED: selected_by_percent,
      NET_TRANSFER: net_transfer,
      GROWTH_FACTOR: growth_factor,
      }
    pds.append(pd)
  return pds

def now_str():  return datetime.datetime.now().strftime('%m%d%H')

# filters - OR ie satisfy any to remain
# TODO func-ize filter
# inj/susp
TYPE_ALL = 'ALL'
THRES_TIME = 0.65 # avg-minutes-played per game-played
THRES_FORM = 4.0 # player form: avg score from games in last 30 days ?
# -> filtered player dicts: [dict]
def filter_pds(pds, filter_type, cols):
  filtered_pds = [
    dict((k, v) for k, v in pd.items() if k in cols) for pd in pds if 
    all([
      filter_type==TYPE_ALL or filter_type == pd[PLAYER_TYPE],
      any([
        watch(pd[PLAYER_TYPE], pd[FIRST_NAME], pd[WEB_NAME], WATCHLIST),
        pd[MINUTES] >= THRES_TIME*(GAMEWEEK-1)*90.0,
        pd[FORM] >= THRES_FORM,
        ])
      ])
    ]
  return filtered_pds


# This drives output csv header-order
OUTPUT_KS = [WATCHED, FIRST_NAME, WEB_NAME, TEAM, PLAYER_TYPE, PRICE, MinPct, VApM, VApML, PpG, PpGL, FORM, SELECTED, NET_TRANSFER, GROWTH_FACTOR, now_str()]
def write_pds(out_parent_dir, pds, sort_key=VApM, filter_type=TYPE_ALL):   
  # filter
  filtered_pds = filter_pds(pds, filter_type, set(OUTPUT_KS))
  # Meta stats
  n_pds = len(filtered_pds)
  sort_key_avg = round(sum(pd[sort_key] for pd in filtered_pds) / n_pds, 2)
  print('%s:\n\t%s players\n\tavg-%s: %s'%(filter_type, n_pds, sort_key, sort_key_avg))
  # Insert avg-marker row
  row_avg = {k: sort_key_avg if k==sort_key else '~'*len(k) for k in OUTPUT_KS}
  filtered_pds.append(row_avg)
  # write
  clean_sort_key = sort_key.replace('/', 'p')
  outf_name = '%s/%s_%s.csv'%(out_parent_dir, filter_type, clean_sort_key)
  with open(outf_name, 'w', encoding='utf8') as outf:
    # write csv
    wrtr = csv.DictWriter(outf, OUTPUT_KS)
    wrtr.writeheader()
    # unicode_pds = [{k: v for (k, v) in pd.items()} for pd in filtered_pds]
    presorted_pds = sorted(filtered_pds, key=lambda pd: float(pd[sort_key]), reverse=True)
    wrtr.writerows(presorted_pds)
    # truncate final new-line to facilitate auto-csv-rendering in Github
    outf.truncate(outf.tell() - len(os.linesep)*2)


def run(refresh):
  get_data.get_typ_data(typ='bootstrap', refresh=True)

  # ALL_TYPES = [TYPE_ALL] + [pt[0] for pt in PLAYER_TYPES.values()]
  out_parent_dir = 'outputs/%s'%(GAMEWEEK)
  if not os.path.exists(out_parent_dir):
    os.makedirs(out_parent_dir)

  # analuaxes
  SORT_KEYS = [VApM, PpG]
  # Get data from local copy
  with open('inputs/%s/bootstrap.json'%GAMEWEEK, 'r', encoding='utf8') as inf:
    data = json.load(inf)

  n_mgrs = data.get('total-players')
  teams = {t['id']: str(t['short_name']) for t in data.get('teams')}
  players = data.get('elements')
  player_types = {t['id']: str(t['singular_name_short'])
    for t in data.get('element_types')}  # e.g. 0 -> 'GKP'

  # TODO separate url-get from local-read
  dict_player_detail = get_data.read_all_player_data(refresh=refresh)

  TYP2SORT_KEY = {
    TYPE_ALL: NET_TRANSFER,
    'G': VApML,
    'D': VApML,
    'M': PpGL,
    'F': PpGL,
    }

  for typ, sk in TYP2SORT_KEY.items():
    print('Type: %s; Sort-key: %s'%(typ, sk))
    write_pds(out_parent_dir, 
      pds=gen_pds(n_mgrs, teams, players, player_types, dict_player_detail),
      sort_key=sk, filter_type=typ)



if __name__ == '__main__':
  refresh = False
  # refresh = True
  run(refresh)


