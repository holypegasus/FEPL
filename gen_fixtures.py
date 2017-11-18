import csv, json, os
from configobj import ConfigObj


CONFIG_PATH = './config.ini'

CONF = ConfigObj(CONFIG_PATH)

gameweek = int(CONF['curr_gameweek'])
# Get data from local
INF_TPL = 'inputs/'+str(gameweek)+'/%s.json'
TEAMS_PATH = INF_TPL%'teams'
FIXTURES_PATH = INF_TPL%'fixtures'



def gen_teams():
  with open(TEAMS_PATH, 'rb') as team_inf:
    td = {t['id']: t for t in json.load(team_inf)}
    return td


def gen_team_fixtures(td):
  tfd = {t['short_name']: [] for t in td.values()}
  with open(FIXTURES_PATH, 'rb') as fixture_inf:
    fixtures = json.load(fixture_inf)
    for f in fixtures:
      team_h_id, team_h_difficulty = f['team_h'], f['team_h_difficulty']
      team_h_name = td[team_h_id]['short_name']
      team_a_id, team_a_difficulty = f['team_a'], f['team_a_difficulty']
      team_a_name = td[team_a_id]['short_name']
      tfd[team_h_name].append(team_h_difficulty)
      tfd[team_a_name].append(team_a_difficulty)
  return tfd


DEFAULT_DECAY = 0.5
def decay_avg(ns, r=DEFAULT_DECAY):
  avg = sum(n*r**i for i, n in enumerate(ns)) / sum(r**i for i in xrange(len(ns)))
  return round(avg, 2)

# print 'test ordering'
# print decay_avg([2,2,2,2,3])
# print decay_avg([2,2,2,3,2])
# print decay_avg([2,2,3,2,2])
# print decay_avg([2,3,2,2,2])
# print decay_avg([3,2,2,2,2])
# print 'test identity'
# print decay_avg([2,2,2,2,2])  # same
# print 'test_scaling'
# print decay_avg([2,2,2,2,4])
# print decay_avg([2,2,2,4,2])
# print decay_avg([2,2,4,2,2])
# print decay_avg([2,4,2,2,2])
# print decay_avg([4,2,2,2,2])

def rank_fixture(tf, curr_gw, look_ahead):
  scoped_fixtures = tf[curr_gw:curr_gw+look_ahead]
  avg = decay_avg(scoped_fixtures)
  return avg, scoped_fixtures


def gen_ranked_fixtures(tfd, curr_gw, look_ahead):
  rfs = []
  for k, tf in tfd.iteritems():
    t0avg, t0fixtures = rank_fixture(tf, curr_gw, look_ahead)
    t1avg, t1fixtures = rank_fixture(tf, curr_gw+1, look_ahead)
    rfs.append(([k, t0avg, t0fixtures[0], t1avg] + t1fixtures))
  return rfs


# keys
TEAM = 'team'

def write_fixture_ranks(tfd, curr_gw=1, look_ahead=5):
  T0AVG = '%s~%s_avg'%(curr_gw, curr_gw+look_ahead-1)
  T1AVG = '%s~%s_avg'%(curr_gw+1, curr_gw+1+look_ahead-1)
  hdrs = [TEAM, T0AVG, curr_gw, T1AVG] + [i for i in xrange(curr_gw+1, curr_gw+1+look_ahead)]

  OUT_PARENT_DIR = 'outputs/%s'%curr_gw
  if not os.path.exists(OUT_PARENT_DIR):
    os.makedirs(OUT_PARENT_DIR)
  outf_path = '%s/%s'%(OUT_PARENT_DIR, 'fixture_ranks.csv')
  with open(outf_path, 'wb') as outf:
    wrtr = csv.DictWriter(outf, hdrs)
    wrtr.writeheader()

    if curr_gw:  # natural_number -> 0-index
      curr_gw -= 1
    rfs = gen_ranked_fixtures(tfd, curr_gw, look_ahead)
    rfd = [dict(zip(hdrs, rf)) for rf in rfs]

    presorted_rfs = sorted(rfd, key=lambda rf: float(rf[T0AVG]))
    wrtr.writerows(presorted_rfs)
    # truncate final new-line to facilitate auto-csv-rendering in Github
    outf.truncate(outf.tell() - len(os.linesep)*2)


if __name__ == '__main__':
  LOOK_AHEAD = 5

  td = gen_teams()
  tfd = gen_team_fixtures(td)
  write_fixture_ranks(tfd, gameweek, LOOK_AHEAD)