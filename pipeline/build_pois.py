"""Comercios y generadores de tráfico desde el export HOT/OSM de HDX (actualización mensual).
Fuente: https://data.humdata.org/dataset/hotosm_gtm_points_of_interest
Salida: pois.js  {giros: {COD: [[lat, lon, marca, nombre], ...]}, gens: [[lat, lon, tipo, nombre], ...], fecha}
"""
import json, re, sys
from shapely.geometry import shape

SRC = sys.argv[1] if len(sys.argv) > 1 else 'data/hot/points_of_interest.geojson'
d = json.load(open(SRC))

# giro -> (amenity/shop values)
GIRO_TAGS = {
    'SUP': {'shop': ['supermarket', 'wholesale', 'hypermarket'], 'amenity': ['marketplace']},
    'FAR': {'amenity': ['pharmacy'], 'shop': ['chemist']},
    'RAP': {'amenity': ['fast_food']},
    'RES': {'amenity': ['restaurant', 'cafe']},
    'GAS': {'amenity': ['fuel']},
    'FER': {'shop': ['hardware', 'doityourself', 'paint', 'trade']},
    'CON': {'shop': ['convenience']},
    'BAN': {'amenity': ['bank']},
    'ROP': {'shop': ['clothes', 'shoes', 'second_hand']},
    'PAN': {'shop': ['bakery', 'pastry']},
}
GEN_TAGS = {('shop', 'mall'): 'M', ('amenity', 'marketplace'): 'K', ('amenity', 'school'): 'E',
            ('amenity', 'university'): 'E', ('amenity', 'college'): 'E', ('amenity', 'hospital'): 'O',
            ('amenity', 'clinic'): 'O', ('amenity', 'bus_station'): 'U'}
# marcas: (regex sobre nombre en minúsculas, clave)
BRANDS = {
    'SUP': [(r'walmart', 'WM'), (r'pa[ií]z', 'PZ'), (r'maxi ?despensa|maxidespensa', 'MX'), (r'desp[ae]n[sz]a|dispensa', 'DF'),
            (r'econo ?s[uú]per', 'ES'), (r'la ?torre', 'LT'), (r's[uú]per ?24', 'S24'), (r's[uú]pero? del barrio', 'SB'),
            (r'bodeg[oó]na', 'LB'), (r'carolina', 'CH'), (r'pricesmart', 'PS'), (r'^suma\b|supermercados? suma', 'SU'),
            (r'super ?fresh', 'MF'), (r'multimayoreo', 'MM')],
    'FAR': [(r'galeno', 'GAL'), (r'cruz verde', 'CV'), (r'batres', 'BAT'), (r'carolina', 'CH'), (r'simi', 'SIM'),
            (r'meykos', 'MEY'), (r'comunidad', 'COM'), (r'del ahorro', 'AHO'), (r'fayco', 'FAY'), (r'herdez', 'HER')],
    'RAP': [(r'mc ?donald', 'MCD'), (r'campero', 'CAM'), (r'pinulito', 'PIN'), (r'granjero', 'GRA'), (r'burger king', 'BK'),
            (r'domino', 'DOM'), (r'taco bell', 'TB'), (r'little caesar', 'LC'), (r'subway', 'SUB'), (r'pollolandia', 'PLL'),
            (r'wendy', 'WEN'), (r'\bkfc\b', 'KFC'), (r'papa john', 'PJ'), (r'pizza hut', 'PH'), (r'dunkin', 'DUN'), (r"carl'?s", 'CJ')],
    'RES': [(r'starbucks', 'STB'), (r'barista', 'BAR'), (r'san mart[ií]n', 'SMA'), (r'pizza hut', 'PH'), (r'macarone', 'MAC'),
            (r'cebollines', 'CEB'), (r'sarita', 'SAR'), (r'la estancia', 'EST'), (r'pollo campero', 'CAM')],
    'GAS': [(r'shell', 'SHE'), (r'puma', 'PUM'), (r'texaco', 'TEX'), (r'\buno\b', 'UNO'), (r'don arturo', 'DAR'),
            (r'pacific', 'PAC'), (r'blue oil', 'BLU')],
    'FER': [(r'cemaco', 'CEM'), (r'novex', 'NOV'), (r'\bepa\b', 'EPA'), (r'ferromax', 'FMX'), (r'celasa', 'CEL'),
            (r'construf[aá]cil', 'CFA'), (r'setema', 'SET')],
    'CON': [(r's[uú]per ?24', 'S24'), (r'select', 'SEL'), (r'texaco|star ?mart', 'TEX'), (r'puma', 'PUM'), (r'oxxo', 'OXX')],
    'BAN': [(r'cajero|atm', 'ATM'), (r'banrural|desarrollo rural', 'BRU'), (r'\bbam\b|agromercantil', 'BAM'),
            (r'industrial', 'BI'), (r'g ?& ?t|g&t', 'GYT'), (r'bantrab|trabajadores', 'BTR'), (r'azteca', 'AZT'),
            (r'inmobiliario', 'INM'), (r'antigua', 'ANT'), (r'citi', 'CIT'), (r'\bbac\b|credomatic', 'BAC'),
            (r'inter ?banco', 'INT'), (r'prom[eé]rica', 'PRO'), (r'\bchn\b|cr[eé]dito hipotecario', 'CHN')],
    'ROP': [(r'megapaca', 'MPC'), (r'payless', 'PAY'), (r"bulock", 'BUL'), (r'skechers', 'SKE'), (r'price shoes', 'PSH'),
            (r'\badoc\b', 'ADO')],
    'PAN': [(r'pavailler', 'PAV'), (r'holandesa', 'HOL'), (r'isopan', 'ISO'), (r'san mart[ií]n', 'SMA'), (r'xelapan', 'XEL'),
            (r'[aá]nfora', 'ANF'), (r'panadely', 'PDL'), (r'superpan', 'SPN'), (r'patsy', 'PAT')],
}
REV = {}
for g, t in GIRO_TAGS.items():
    for k, vals in t.items():
        for v in vals: REV.setdefault((k, v), []).append(g)

out = {g: [] for g in GIRO_TAGS}; gens = []; seen = set()
for f in d['features']:
    p = f['properties']; geom = f['geometry']
    if geom is None: continue
    if geom['type'] == 'Point': lo, la = geom['coordinates'][:2]
    else:
        c = shape(geom).representative_point(); lo, la = c.x, c.y
    if not (13.5 < la < 18.2 and -92.4 < lo < -88.0): continue
    name = (p.get('name') or '').strip()
    nl = name.lower()
    for k in ('amenity', 'shop'):
        v = p.get(k)
        if not v: continue
        gt = GEN_TAGS.get((k, v))
        if gt:
            key = ('G', gt, round(la, 4), round(lo, 4))
            if key not in seen:
                seen.add(key); gens.append([round(la, 5), round(lo, 5), gt, name[:40]])
        for g in REV.get((k, v), []):
            b = ''
            for rx, code in BRANDS.get(g, []):
                if re.search(rx, nl): b = code; break
            if not b and v in ('wholesale',): b = '_W'
            if not b and v in ('marketplace',): b = '_K'
            if not b and v in ('doityourself',): b = '_D'
            key = (g, b or nl, round(la, 3), round(lo, 3))
            if key in seen: continue
            seen.add(key)
            out[g].append([round(la, 5), round(lo, 5), b, name[:40]])

import os
fecha = None
rd = os.path.join(os.path.dirname(SRC), 'README.txt')
if os.path.exists(rd):
    m = re.search(r'Snapshot:\s*(\S+)', open(rd).read())
    if m: fecha = m.group(1)
open('pois.js', 'w', encoding='utf-8').write('window.SP=' + json.dumps({'giros': out, 'gens': gens, 'fecha': fecha}, ensure_ascii=False, separators=(',', ':')) + ';')
print({g: len(v) for g, v in out.items()}, 'gens', len(gens))
from collections import Counter
for g in out:
    c = Counter(x[2] for x in out[g]); print(g, c.most_common(8))
