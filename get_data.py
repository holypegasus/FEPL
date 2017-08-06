import json, urllib2


# Get data from web API
URL_TPL = 'https://fantasy.premierleague.com/drf/%s'
types = [
  'bootstrap',  # overall
  'fixtures',
  'teams'
]
OUTF_TPL = 'inputs/%s.json'


for t in types:
  html = urllib2.urlopen(URL_TPL%t)
  data = json.load(html)
  with open(OUTF_TPL%t, 'wb') as outf:
    json.dump(data, outf)


