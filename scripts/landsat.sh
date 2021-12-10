#! sh
set -x

./manage.py watch_stac_server \
  https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l1/items
  --collection "landsat-c2l1" \
  > scripts/logs/ingest_ls_c2l1_$(date "+%y-%m-%d_%H.%M.%S").txt

./manage.py watch_stac_server \
  https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l2-sr/items
  --collection "landsat-c2l2-sr" \
  > scripts/logs/ingest_ls_c2l2_sr_$(date "+%y-%m-%d_%H.%M.%S").txt


./manage.py watch_stac_server \
  https://api.smart-stac.com/collections/landsat-c2l1/items
  --collection "smart-landsat-c2l1" \
  > scripts/logs/ingest_smart_ls_c2l1_$(date "+%y-%m-%d_%H.%M.%S").txt


./manage.py watch_stac_server \
  https://api.smart-stac.com/collections/landsat-c2l2-sr/items
  --collection "smart-landsat-c2l2-sr" \
  > scripts/logs/ingest_smart_ls_c2l2_sr_$(date "+%y-%m-%d_%H.%M.%S").txt

set +x
