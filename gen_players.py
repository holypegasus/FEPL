# -*- coding: UTF-8 -*-
import csv, json, os
from util.unicode_csv_rw import DictUnicodeWriter


# Get data from local copy
with open('inputs/bootstrap.json', 'rb') as inf:
  data = json.load(inf)


N_MGRs = data.get('total-players')
TEAMS = {t['id']: str(t['short_name']) for t in data.get('teams')}
PLAYERS = data.get('elements')
PLAYER_TYPES = {t['id']: str(t['singular_name_short']) for t in data.get('element_types')}  # e.g. 0 -> 'GKP'
# keys
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
TYPE_ALL = 'ALL'
MINUTES_THD = 90.0*6  # minutes-played: max 3420
MIN_P_GAME_THD = 30.0  # minutes/game
# analuaxes
BASE_PTS = 2.0
SORT_KEY = VApM



def gen_pds():
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

    pd = {  # player dict
      FIRST_NAME: first_name,
      WEB_NAME: web_name,
      TEAM: team,
      PLAYER_TYPE: p_type,
      VApM: vapm,
      POINTS: total_pts,
      GAMES: n_games,
      PpG: ppg,
      MINUTES: minutes,
      MpG: min_p_game,
      PRICE: price,
      SELECTED: selected_by_percent,
    }
    pds.append(pd)
  return pds


OUTPUT_KS = [FIRST_NAME, WEB_NAME, TEAM, PLAYER_TYPE, VApM, POINTS, GAMES, PpG, MINUTES, MpG, PRICE, SELECTED]
def write_pds(pds, filter_type=TYPE_ALL):   
  # filter
  filtered_pds = [pd for pd in pds if (
    (filter_type==TYPE_ALL or filter_type == pd[PLAYER_TYPE])
    and pd[MINUTES] >= MINUTES_THD
    and pd[MpG] >= MIN_P_GAME_THD
  )]
  # Meta stats
  n_pds = len(filtered_pds)
  avg_vapm = round(sum(pd[VApM] for pd in filtered_pds) / n_pds, 2)
  print '%s:\n\t%s players\n\tavg-VA/M: %s'%(filter_type, n_pds, avg_vapm)
  # Insert avg-marker row
  row_avg = {k: avg_vapm if k==VApM else '~'*len(k) for k in OUTPUT_KS}
  filtered_pds.append(row_avg)
  # write
  outf_name = 'outputs/stats_%s.csv'%(filter_type)
  with open(outf_name, 'w') as outf:
    wrtr = DictUnicodeWriter(outf, OUTPUT_KS)
    wrtr.writeheader()
    unicode_pds = [{k: unicode(v) for (k, v) in pd.iteritems()} for pd in filtered_pds]
    presorted_pds = sorted(unicode_pds, key=lambda pd: float(pd[SORT_KEY]), reverse=True)
    wrtr.writerows(presorted_pds)
    # truncate final new-line to facilitate auto-csv-rendering in Github
    outf.truncate(outf.tell() - len(os.linesep)*2)



if __name__ == '__main__':
  ALL_TYPES = [TYPE_ALL] + [pt[0] for pt in PLAYER_TYPES.values()]
  for ft in ALL_TYPES:
    write_pds(pds=gen_pds(), filter_type=ft)

