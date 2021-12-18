from datetime import datetime

from watch_helpers import post_stac_items_from_server

if __name__ == '__main__':
    min_date = datetime(2015, 12, 31)  # First available found
    max_date = datetime.today()
    host_url = 'https://earth-search.aws.element84.com/v0/'

    collection = 'sentinel-s2-l1c'
    post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)

    collection = 'sentinel-s2-l2a'
    post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)
