from watch_helpers import post_stac_items_from_server

host_url = 'https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l1/items'
collection = 'landsat-c2l1'
post_stac_items_from_server(host_url, collection)

host_url = 'https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l2-sr/items'
collection = 'landsat-c2l2-sr'
post_stac_items_from_server(host_url, collection)

host_url = 'https://api.smart-stac.com/collections/landsat-c2l1/items'
collection = 'smart-landsat-c2l1'
post_stac_items_from_server(host_url, collection)

host_url = 'https://api.smart-stac.com/collections/landsat-c2l2-sr/items'
collection = 'smart-landsat-c2l2-sr'
post_stac_items_from_server(host_url, collection)
