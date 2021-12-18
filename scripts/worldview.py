from watch_helpers import post_stac_items_from_s3_iter

if __name__ == '__main__':
    bucket = 'smart-imagery'
    prefix = 'worldview-nitf/'
    collection = 'WorldView'
    region = 'us-west-2'

    post_stac_items_from_s3_iter(bucket, prefix, collection, region=region)
