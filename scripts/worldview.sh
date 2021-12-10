#! sh
set -x

./manage.py watch_s3_stac smart-imagery \
  --prefix worldview-nitf/ \
  --collection "WorldView" \
  > scripts/logs/ingest_wv_$(date "+%y-%m-%d_%H.%M.%S").txt

set +x
