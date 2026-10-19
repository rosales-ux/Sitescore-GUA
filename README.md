# SiteScore GT

Herramienta gratuita de selección de sitios comerciales para Guatemala. Estima venta anual, score 0–100, área de influencia y perfil demográfico de cualquier punto, con un modelo de gravedad (Huff) sobre población 2025 en celdas de 500 m.

## Qué incluye

- 10 giros: supermercados, farmacias, comida rápida, restaurantes y cafés, gasolineras, ferretería, conveniencia, bancos, ropa y calzado, panaderías, más un giro propio con competidores importados por CSV.
- Coordenadas como primer paso (decimales, GMS o enlace de Google Maps).
- Perfil demográfico a 1, 2, 3 y 5 km: población 2020/2025/2030, crecimiento, hogares, edad, sexo, poder adquisitivo.
- Comparación de sitios, mapa de oportunidad y reporte PDF (Formato RV).
- Vista satelital Sentinel-2.

## Estructura

| Ruta | Contenido |
|---|---|
| `index.html` | La aplicación completa (una sola página) |
| `sitedata.js` | Población WorldPop 2020/2025/2030, municipios y zonas, edad y sexo |
| `pois.js` | Comercios y generadores de tráfico (OpenStreetMap) |
| `sat/` | Imágenes satelitales e índice |
| `pipeline/` | Scripts para regenerar los datos y la página |

## Publicar con GitHub Pages

1. Settings → Pages.
2. Source: *Deploy from a branch*. Branch: `main`, carpeta `/ (root)`. Save.
3. En uno o dos minutos la herramienta queda en `https://<usuario>.github.io/sitescore-gt/`.

Nota: GitHub Pages en repositorios privados requiere un plan de pago. Con un repositorio público, cualquiera con el enlace puede abrir la herramienta.

## Actualizar los datos

Desde la raíz del repositorio, con Python 3 y `pip install rasterio shapely numpy pillow`:

```bash
# Comercios (mensual) — export HOT de OpenStreetMap en HDX
mkdir -p data/hot && curl -L -o data/hot/poi.zip https://production-raw-data-api.s3.amazonaws.com/ISO3/GTM/points_of_interest/hotosm_gtm_points_of_interest_osm_geojson.zip
unzip -o data/hot/poi.zip -d data/hot
python3 pipeline/build_pois.py            # escribe pois.js

# Población (anual) — WorldPop R2025A 100 m, GADM 4.1, COD-PS del INE
#   data/gtm_pop_2020.tif, data/gtm_pop_2025.tif, data/gtm_pop_2030.tif
#   data/gadm2.json, data/adm2pop.csv
python3 pipeline/build_data.py            # escribe sitedata.js

# Vista satelital (opcional) — Sentinel-2 L2A vía Earth Search
python3 pipeline/build_sat.py && python3 pipeline/build_sat_pais.py   # escribe sat/

# Página — tras editar pipeline/app.js o pipeline/app.src.html
python3 pipeline/build_page.py            # escribe index.html
```

La carpeta `data/` no se sube al repositorio (archivos grandes).

## Fuentes y licencias

- Población: WorldPop (CC BY 4.0).
- Límites: GADM 4.1 (uso no comercial; para uso comercial reemplazar por geoBoundaries).
- Edad y sexo: INE Guatemala, vía HDX COD-PS.
- Comercios: © colaboradores de OpenStreetMap, ODbL. `pois.js` es una base derivada y se comparte bajo ODbL.
- Imagen: contiene datos modificados de Copernicus Sentinel-2 (2025–2026).
- Poder adquisitivo: pobreza departamental ENCOVI 2014 (INE) con ajustes propios.

Los gastos por persona, tamaños por marca y objetivos de venta son supuestos de referencia, editables en la pestaña Base de datos.
