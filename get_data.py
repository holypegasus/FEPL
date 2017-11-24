import json, os, requests
from configobj import ConfigObj


CONFIG_PATH = './config.ini'

CONF = ConfigObj(CONFIG_PATH)

# Get data from web API
URL_TPL = 'https://fantasy.premierleague.com/drf/%s'
types = [
  'bootstrap',  # overall
  'fixtures',
  'teams'
]

gameweek = int(CONF['curr_gameweek'])
OUT_PARENT_DIR = 'inputs/%s'%gameweek
GW_OUTPUTS_DIR = 'outputs/%s'%gameweek
if not os.path.exists(OUT_PARENT_DIR):
  os.makedirs(OUT_PARENT_DIR)
if not os.path.exists(GW_OUTPUTS_DIR):
  os.makedirs(GW_OUTPUTS_DIR)

for typ in types:
  html = requests.get(URL_TPL%typ).text
  data = json.loads(html)
  print(len(data))

  outf_path = '%s/%s.json'%(OUT_PARENT_DIR, typ)
  print(outf_path)
  with open(outf_path, 'w', encoding='utf8') as outf:
    json.dump(data, outf)

