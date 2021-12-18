from datetime import datetime

from watch_helpers import post_stac_items_from_server

if __name__ == '__main__':
    min_date = datetime(2013, 1, 1)  # Arbitrarily chosen
    max_date = datetime.today()
    host_url = 'https://landsatlook.usgs.gov/stac-server/'

    collection = 'landsat-c2l1'
    print(collection)
    post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)

    collection = 'landsat-c2l2-sr'
    print(collection)
    post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)

    # host_url = 'https://api.smart-stac.com/'
    # collection = 'smart-landsat-c2l1'
    # post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)
    #
    # collection = 'smart-landsat-c2l2-sr'
    # post_stac_items_from_server(host_url, collection, min_date=min_date, max_date=max_date)
