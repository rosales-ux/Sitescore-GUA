"""Construye la base de datos geoespacial para SiteScore GT.
Salida: data/sitedata.js  (window.SD = {...})
- Grilla de población WorldPop 2025 (100 m) agregada a 500 m, con municipio asignado
- Municipios GADM 4.1 simplificados (GeoJSON) con índice de poder adquisitivo
- Puntos de competencia / generadores (OSM, oct-2026)
"""
import json, base64, numpy as np, rasterio
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
from shapely import contains_xy

F = 5  # 100 m x 5 = 500 m
d = rasterio.open('data/gtm_pop_2025.tif')
a = d.read(1).astype('float64'); a[a < 0] = 0
H = (a.shape[0] // F) * F; W = (a.shape[1] // F) * F
b = a[:H, :W].reshape(H // F, F, W // F, F).sum(axis=(1, 3))
res = d.res[0] * F
x0, y1 = d.bounds.left, d.bounds.top
rows, cols = np.nonzero(b >= 5)
pops = b[rows, cols]
lon = x0 + (cols + 0.5) * res
lat = y1 - (rows + 0.5) * res
print('celdas', len(pops), 'pob', round(pops.sum()))
def agg(path):
    r = rasterio.open(path); assert r.shape == d.shape and abs(r.bounds.left - d.bounds.left) < 1e-9
    x = r.read(1).astype('float64'); x[x < 0] = 0
    return x[:H, :W].reshape(H // F, F, W // F, F).sum(axis=(1, 3))[rows, cols]
p20 = agg('data/gtm_pop_2020.tif'); p30 = agg('data/gtm_pop_2030.tif')
print('2020', round(p20.sum()), '2030', round(p30.sum()))

# ---- Municipios
g = json.load(open('data/gadm2.json'))
feats = g['features']
geoms = [shape(f['geometry']) for f in feats]
# ENCOVI 2014 (INE) pobreza total por departamento (%), proxy de poder adquisitivo
POV = {'Guatemala': 33.3, 'ElProgreso': 53.2, 'Sacatepéquez': 41.1, 'Chimaltenango': 66.1,
       'Escuintla': 52.9, 'SantaRosa': 54.3, 'Sololá': 80.9, 'Totonicapán': 77.5,
       'Quezaltenango': 56.0, 'Suchitepéquez': 63.8, 'Retalhuleu': 56.1, 'SanMarcos': 60.2,
       'Huehuetenango': 73.8, 'Quiché': 74.7, 'BajaVerapaz': 66.3, 'AltaVerapaz': 83.1,
       'Petén': 60.8, 'Izabal': 59.9, 'Zacapa': 55.9, 'Chiquimula': 70.6, 'Jalapa': 67.2,
       'Jutiapa': 62.7}
NAT = 59.3
def dep_idx(dep):
    p = POV.get(dep.replace(' ', '').replace('Quetzaltenango','Quezaltenango'), NAT)
    return round(((100 - p) / (100 - NAT)) ** 0.8, 2)
# Ajustes municipales área metropolitana y cabeceras (supuesto editable)
MUNI_ADJ = {'Mixco': 1.55, 'Villa Nueva': 1.25, 'Santa Catarina Pinula': 2.2, 'San José Pinula': 1.6,
            'Fraijanes': 1.7, 'Chinautla': 0.85, 'San Miguel Petapa': 1.3, 'Villa Canales': 1.0,
            'Amatitlán': 1.0, 'San Pedro Ayampuc': 0.85, 'San Juan Sacatepéquez': 0.85,
            'San Pedro Sacatepéquez': 0.9, 'Chuarrancho': 0.6, 'San Raymundo': 0.75, 'Palencia': 0.85,
            'Antigua Guatemala': 1.8, 'Jocotenango': 1.3, 'Quetzaltenango': 1.35, 'Escuintla': 1.15,
            'Cobán': 0.9, 'Huehuetenango': 1.0, 'Zacapa': 1.1, 'Chiquimula': 0.95, 'Jutiapa': 0.95,
            'Puerto Barrios': 1.05, 'Flores': 1.05, 'San Benito': 0.95, 'Mazatenango': 1.0,
            'Retalhuleu': 1.05, 'Chimaltenango': 1.0, 'Jalapa': 0.95, 'Cuilapa': 0.95, 'Salamá': 0.9,
            'Guastatoya': 1.05, 'San Marcos': 0.95, 'Santa Cruz del Quiché': 0.8, 'Sololá': 0.75,
            'Totonicapán': 0.75}
# Índice de poder adquisitivo por zona de la Ciudad de Guatemala (supuesto editable, nacional = 1.0)
ZIDX = {1:1.2,2:1.4,3:1.0,4:1.4,5:1.1,6:1.0,7:1.1,8:1.0,9:1.8,10:2.6,11:1.5,12:1.1,13:1.8,14:2.6,15:2.2,
        16:2.3,17:1.0,18:0.85,19:0.95,21:0.75,22:0.8,24:0.75,25:0.75}
import re
def pretty(n):
    m = re.match(r'ZONA(\d+)$', n)
    if m: return 'Zona ' + m.group(1)
    t = re.sub(r'(?<=[a-záéíóúñü])(?=[A-ZÁÉÍÓÚÑ])', ' ', n).split(' ')
    out = []
    for w in t:
        mm = re.match(r'^(.{3,}?)(del|de)$', w)
        if mm and w not in ('Grande', 'Verde', 'Conde', 'Valde'):
            out += [mm.group(1), mm.group(2)]
        else: out.append(w)
    r = ' '.join(out)
    FIX = {'Petapa': 'San Miguel Petapa', 'San Rafaél Piedela Cuesta': 'San Rafael Pie de la Cuesta', 'Quezaltenango': 'Quetzaltenango'}
    return FIX.get(r, r)
munis = []
for i, f in enumerate(feats):
    p = f['properties']
    dep, mun = pretty(p['NAME_1']), pretty(p['NAME_2'])
    idx = MUNI_ADJ.get(mun, dep_idx(p['NAME_1']))
    if mun.startswith('Zona '):
        idx = ZIDX.get(int(mun[5:]), 1.0)
    rp = geoms[i].representative_point()
    munis.append({'id': i, 'd': dep, 'm': mun, 'i': idx, 'la': round(rp.y, 4), 'lo': round(rp.x, 4)})


tree = STRtree(geoms)
mid = np.full(len(pops), -1, dtype=np.int32)
for gi, gm in enumerate(geoms):
    m = contains_xy(gm, lon, lat)
    mid[m & (mid < 0)] = gi
# celdas sin municipio (borde): asignar el más cercano
miss = np.nonzero(mid < 0)[0]
for k in miss:
    pt = Point(lon[k], lat[k]); mid[k] = tree.nearest(pt)
idx = np.array([munis[m]['i'] for m in mid], dtype=np.float64)

# Estructura por edad y sexo (INE/COD-PS 2024, HDX) por municipio; zonas usan el perfil de Guatemala
import csv, unicodedata
norm = lambda t: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower())
BANDS = ['00_04','05_09','10_14','15_19','20_24','25_29','30_34','35_39','40_44','45_49','50_54','55_59','60_64','65_69','70Plus']
prof, depsum = {}, {}
for r in csv.DictReader(open('data/adm2pop.csv', encoding='utf-8')):
    v = [float(r['F_' + b]) for b in BANDS] + [float(r['M_' + b]) for b in BANDS]
    prof[(norm(r['ADM1_ES']), norm(r['ADM2_ES']))] = v
    ds = depsum.setdefault(norm(r['ADM1_ES']), [0.0] * 30)
    for k in range(30): ds[k] += v[k]
AGES = []; akey = {}
miss_names = []
for m in munis:
    dk = norm(m['d']); mk = norm('Guatemala' if m['m'].startswith('Zona ') else m['m'])
    v = prof.get((dk, mk))
    if v is None:
        cand = [k for k in prof if k[0] == dk and (k[1] in mk or mk in k[1])]
        v = prof[cand[0]] if cand else None
    if v is None: v = depsum.get(dk); miss_names.append(m['m'])
    t = sum(v); sh = tuple(round(x / t, 4) for x in v)
    if sh not in akey: akey[sh] = len(AGES); AGES.append(list(sh))
    m['a'] = akey[sh]
    m['h'] = 3.8 if m['d'] == 'Guatemala' else 4.5
print('perfiles', len(AGES), 'sin match', miss_names)

# Población por municipio
mp = np.bincount(mid, weights=pops, minlength=len(munis))
for m in munis: m['p'] = int(round(mp[m['id']]))

# GeoJSON simplificado
out_f = []
for i, gm in enumerate(geoms):
    s = gm.simplify(0.004, preserve_topology=True)
    gj = mapping(s)
    def rnd(c):
        if isinstance(c[0], (float, int)): return [round(c[0], 4), round(c[1], 4)]
        return [rnd(x) for x in c]
    gj = {'type': gj['type'], 'coordinates': rnd(gj['coordinates'])}
    out_f.append({'type': 'Feature', 'properties': {'id': i}, 'geometry': gj})


b64 = lambda arr: base64.b64encode(arr.tobytes()).decode()
SD = {
  'meta': {'res': res, 'src': 'WorldPop 2025 R2025A (100 m, constrained) agregado a 500 m; GADM 4.1; ENCOVI 2014; INE/COD-PS 2024 edad y sexo',
           'n': int(len(pops)), 'pop': int(round(pops.sum()))},
  'grid': {'x0': x0, 'y1': y1}, 'r': b64(rows.astype('<u2')), 'c': b64(cols.astype('<u2')),
  'pop': b64(np.minimum(np.round(pops), 65535).astype('<u2')), 'mid': b64(mid.astype('<u2')),   'munis': munis,
  'p20': b64(np.minimum(np.round(p20), 65535).astype('<u2')), 'p30': b64(np.minimum(np.round(p30), 65535).astype('<u2')),
  'ages': AGES, 'bands': ['0–4','5–9','10–14','15–19','20–24','25–29','30–34','35–39','40–44','45–49','50–54','55–59','60–64','65–69','70+'],
  'geo': {'type': 'FeatureCollection', 'features': out_f},
}
s = 'window.SD=' + json.dumps(SD, ensure_ascii=False, separators=(',', ':')) + ';'
open('sitedata.js', 'w', encoding='utf-8').write(s)
print('size KB', len(s.encode()) // 1024)
gz = sorted(munis, key=lambda m: -m['p'])[:12]
print([(m['m'], m['p'], m['i']) for m in gz])
