"""Arma index.html (página completa para GitHub Pages) desde pipeline/app.src.html + app.js + leaflet.min.css.
Uso, desde la raíz del repositorio:  python3 pipeline/build_page.py"""
import os
d = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(d, 'app.src.html'), encoding='utf-8').read()
s = src.replace('/*LEAFLET_CSS*/', open(os.path.join(d, 'leaflet.min.css'), encoding='utf-8').read()).replace('/*APP_JS*/', open(os.path.join(d, 'app.js'), encoding='utf-8').read())
t = s[s.index('<title>'):s.index('</title>') + 8]; body = s.replace(t, '', 1)
head = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n' + t +
        '\n<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
open('index.html', 'w', encoding='utf-8').write(head + body + '\n</body>\n</html>\n')
print('index.html listo')
