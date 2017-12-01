import pandas as pd


# TODO migrate existing analyses + start new ones

# fixture



# player
# pid -> analysis
THRES_LONG = 50  # minutes considered 'long'-game
def calc_ppgs(pid, dict_player):
  print('Analyzing %s'%pid)

  stats = {
    'ppg_naive': 0.,
    'ppg_long': 0.,
  }

  if not dict_player:
    return stats

  history_fixtures = dict_player.get('history', [dict()])  # [gw1, gw2, ...]
  df_hist = pd.DataFrame(history_fixtures)

  # key-stats
  df_ks = df_hist[['minutes', 'total_points', 'bps']]
  # print(df_ks)
  n_games_played = len(df_ks[df_ks['minutes'] > 0])
  pt_total = df_ks['total_points'].sum()

  # long-games key-stats
  df_ks_long = df_ks[df_ks['minutes'] >= THRES_LONG]
  # print(df_ks_long)
  n_games_long = len(df_ks_long)
  pt_long = df_ks_long['total_points'].sum()

  # ppg_naive
  if n_games_played > 0:
    ppg_naive = round(pt_total/n_games_played, 1)
  else:
    ppg_naive = 0.0
  print('Naive PPG = %s / %s ~= %s'%(pt_total, n_games_played, ppg_naive))
  stats['ppg_naive'] = ppg_naive
  # full ppg
  if n_games_long > 0:
    ppg_long = round(pt_long/n_games_long, 1)
  else:
    ppg_long = 0.0
  print('Long PPG = %s / %s ~= %s'%(pt_long, n_games_long, ppg_long))
  stats['ppg_long'] = ppg_long

  return stats


