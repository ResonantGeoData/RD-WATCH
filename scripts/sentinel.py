from watch_helpers import post_stac_items_from_server

host_url = 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l1c/items'
collection = 'sentinel-s2-l1c'
post_stac_items_from_server(host_url, collection)

host_url = 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a/items'
collection = 'sentinel-s2-l2a'
post_stac_items_from_server(host_url, collection)
