#! sh
set -x

./manage.py watch_s3_stac kitware-smart-watch-data \
  --prefix processed/ta1/drop1/coreg_and_brdf/ \
  --collection "drop1/coreg_and_brdf" \
  > scripts/logs/ingest_drop1_coreg_and_brdf_$(date "+%y-%m-%d_%H.%M.%S").txt


./manage.py watch_s3_stac kitware-smart-watch-data \
  --prefix processed/ta1/drop1/mtra/ \
  --collection "drop1/mtra" \
  > scripts/logs/ingest_drop1_mtra_$(date "+%y-%m-%d_%H.%M.%S").txt

set +x
