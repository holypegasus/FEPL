# -*- coding: UTF-8 -*-
import csv, json, os
from configobj import ConfigObj
# from util.unicode_csv_rw import DictUnicodeWriter


CONFIG_PATH = './config.ini'

CONF = ConfigObj(CONFIG_PATH)

gameweek = int(CONF['curr_gameweek'])
# keys
OWNED = 'O'
FIRST_NAME = 'I'
WEB_NAME = 'web_name'
TEAM = 'team'
PLAYER_TYPE = 'T'
VApM = 'VA/M'
POINTS = 'pt'
GAMES = 'g'
PpG = 'p/g'
MINUTES = 'min'
MpG = 'min/g'
PRICE = 'price'
SELECTED = '%'
# filters
# TODO func-ize filter
TYPE_ALL = 'ALL'
MINUTES_THD = 0.5*(gameweek-1)*90.0
MIN_P_GAME_THD = 50.0  # minutes/game


def get_my_players(conf):
  ptyp8fn8ln = set()
  for pos, player_names in conf['owned'].items():
    for player_name in player_names:
      if '_' in player_name:
        first_name, last_name = player_name.split('_')
      else:
        first_name, last_name = '', player_name
      # ptyp8fn8ln.add((pos, first_name, last_name.decode('utf8')))
      ptyp8fn8ln.add((pos, first_name, last_name))
  return ptyp8fn8ln


def own(ptyp, fn, ln, _my_ptyp8fn8ln):
  if (ptyp, fn, ln) in _my_ptyp8fn8ln or (ptyp, '', ln) in _my_ptyp8fn8ln:
    return 'x'
  else:
    return ''


def gen_pds():
  _my_ptyp8fn8ln = get_my_players(CONF)
  pds = []  # player-dicts
  for p in PLAYERS:
    first_name = p.get('first_name').split()[0][0]
    web_name = p.get('web_name')
    team = TEAMS[p.get('team')]
    p_type = PLAYER_TYPES.get(p.get('element_type'))[0][0]
    total_pts = p.get('total_points')
    ppg = float(p.get('points_per_game', 0.0))  # points/game
    n_games = int(round(total_pts / ppg)) if ppg!=0.0 else 0
    ppgar = ppg - BASE_PTS  # points/game above-replacement
    price = p.get('now_cost')/10.0
    vapm = round(ppgar / price, 2)  # value-added/game
    minutes = p.get('minutes')
    min_p_game = round(minutes / n_games) if n_games!=0 else 0
    selected_by_percent = float(p.get('selected_by_percent'))
    owned = own(p_type, first_name, web_name, _my_ptyp8fn8ln)

    pd = {  # player dict
      OWNED: owned,
      TEAM: team,
      FIRST_NAME: first_name,
      WEB_NAME: web_name,
      PLAYER_TYPE: p_type,
      VApM: vapm,
      PRICE: price,
      PpG: ppg,
      POINTS: total_pts,
      GAMES: n_games,
      MINUTES: minutes,
      MpG: min_p_game,
      SELECTED: selected_by_percent,
    }
    pds.append(pd)
  return pds


OUTPUT_KS = [OWNED, FIRST_NAME, WEB_NAME, TEAM, PLAYER_TYPE, VApM, POINTS, GAMES, PpG, MINUTES, MpG, PRICE, SELECTED]
def write_pds(pds, sort_key=VApM, filter_type=TYPE_ALL):   
  # filter
  filtered_pds = [pd for pd in pds if (
    (filter_type==TYPE_ALL or filter_type == pd[PLAYER_TYPE])
    and pd[MINUTES] >= MINUTES_THD
    and pd[MpG] >= MIN_P_GAME_THD
  )]
  # Meta stats
  n_pds = len(filtered_pds)
  sort_key_avg = round(sum(pd[sort_key] for pd in filtered_pds) / n_pds, 2)
  print('%s:\n\t%s players\n\tavg-%s: %s'%(filter_type, n_pds, sort_key, sort_key_avg))
  # Insert avg-marker row
  row_avg = {k: sort_key_avg if k==sort_key else '~'*len(k) for k in OUTPUT_KS}
  filtered_pds.append(row_avg)
  # write
  clean_sort_key = sort_key.replace('/', 'p')
  outf_name = '%s/%s_%s.csv'%(OUT_PARENT_DIR, filter_type, clean_sort_key)
  with open(outf_name, 'w', encoding='utf8') as outf:
    # wrtr = DictUnicodeWriter(outf, OUTPUT_KS)
    wrtr = csv.DictWriter(outf, OUTPUT_KS)
    wrtr.writeheader()
    # unicode_pds = [{k: unicode(v) for (k, v) in pd.items()} for pd in filtered_pds]
    unicode_pds = [{k: v for (k, v) in pd.items()} for pd in filtered_pds]
    presorted_pds = sorted(unicode_pds, key=lambda pd: float(pd[sort_key]), reverse=True)
    wrtr.writerows(presorted_pds)
    # truncate final new-line to facilitate auto-csv-rendering in Github
    outf.truncate(outf.tell() - len(os.linesep)*2)



# analuaxes
BASE_PTS = 2.0
SORT_KEYS = [VApM, PpG]
# Get data from local copy
with open('inputs/%s/bootstrap.json'%gameweek, 'r', encoding='utf8') as inf:
  data = json.load(inf)

N_MGRs = data.get('total-players')
TEAMS = {t['id']: str(t['short_name']) for t in data.get('teams')}
PLAYERS = data.get('elements')
PLAYER_TYPES = {t['id']: str(t['singular_name_short']) for t in data.get('element_types')}  # e.g. 0 -> 'GKP'

if __name__ == '__main__':
  ALL_TYPES = [TYPE_ALL] + [pt[0] for pt in PLAYER_TYPES.values()]
  OUT_PARENT_DIR = 'outputs/%s'%(gameweek)
  if not os.path.exists(OUT_PARENT_DIR):
    os.makedirs(OUT_PARENT_DIR)

  for sk in SORT_KEYS:
    print('Sort-key: %s'%sk)
    for ft in ALL_TYPES:
      write_pds(pds=gen_pds(), sort_key=sk, filter_type=ft)

