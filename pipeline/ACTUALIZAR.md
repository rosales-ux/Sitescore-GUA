# SiteScore GT — cómo actualizar los datos

1. Comercios (mensual): descargar el export HOT de HDX
   https://production-raw-data-api.s3.amazonaws.com/ISO3/GTM/points_of_interest/hotosm_gtm_points_of_interest_osm_geojson.zip
   descomprimir en data/hot/ y correr `python3 build_pois.py` → site/pois.js
2. Población (anual): WorldPop R2025A, GTM 100 m constrained → data/gtm_pop_2025.tif;
   límites GADM 4.1 nivel 2 → data/gadm2.json; correr `python3 build_data.py` → site/sitedata.js
3. Página: index.html = app.src.html con /*LEAFLET_CSS*/ (leaflet 1.9.4 min.css) y /*APP_JS*/ (app.js) sustituidos.
4. Publicar index.html al mismo artifact con files: sitedata.js, pois.js.
5. Vista satelital (opcional, anual): `python3 build_sat.py` y luego `python3 build_sat_pais.py` → site/sat/*.jpg + index.json
   (Sentinel-2 L2A de Earth Search, época seca; 10 m en área metropolitana y 20 cabeceras, 160 m país).
