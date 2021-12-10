from watch_helpers import post_stac_items_from_s3_iter

bucket = 'kitware-smart-watch-data'
prefix = 'processed/ta1/drop1/coreg_and_brdf/'
collection = 'drop1/coreg_and_brdf'
region = 'us-west-2'
post_stac_items_from_s3_iter(bucket, prefix, collection, region=region)

bucket = 'kitware-smart-watch-data'
prefix = 'processed/ta1/drop1/mtra/'
collection = 'drop1/mtra'
region = 'us-west-2'
post_stac_items_from_s3_iter(bucket, prefix, collection, region=region)
