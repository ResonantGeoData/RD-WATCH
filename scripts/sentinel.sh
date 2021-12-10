#! sh
set -x

./manage.py watch_stac_server \
  https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l1c/items
  --collection "sentinel-s2-l1c" \
  > scripts/logs/ingest_s2_l1c_$(date "+%y-%m-%d_%H.%M.%S").txt


./manage.py watch_stac_server \
  https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a/items
  --collection "sentinel-s2-l2a" \
  > scripts/logs/ingest_s2_l2a_$(date "+%y-%m-%d_%H.%M.%S").txt

set +x
