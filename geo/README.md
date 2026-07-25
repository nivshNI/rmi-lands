# Settlement coordinates

`settlements.json` maps Hebrew locality names to `[lat, lon]` for 1365 Israeli
localities. It is a trimmed form (name + point only) of `cities.geojson` from
[yuvadm/geolocations-il](https://github.com/yuvadm/geolocations-il), which in
turn derives from data.gov.il open data.

It is bundled rather than fetched at runtime so the monitor stays a single API
call and the map builds offline.

Names that this dataset does not cover — regional councils (`מ.א. …`) and a
handful of spelling variants — are handled by `MANUAL_COORDS` in `geocode.py`.
Anything still unresolved falls back to its RMI region centroid and is marked
as approximate on the map rather than silently dropped.

To refresh:

```bash
curl -sS https://raw.githubusercontent.com/yuvadm/geolocations-il/master/cities.geojson \
  -o /tmp/il.geojson
python3 - <<'PY'
import json
g = json.load(open('/tmp/il.geojson'))
out = {}
for f in g['features']:
    name = f['properties']['name'].strip()
    lon, lat = f['geometry']['coordinates']
    if name and name not in out:
        out[name] = [round(lat, 5), round(lon, 5)]
json.dump(out, open('geo/settlements.json', 'w'), ensure_ascii=False, indent=0, sort_keys=True)
print('wrote', len(out))
PY
```
