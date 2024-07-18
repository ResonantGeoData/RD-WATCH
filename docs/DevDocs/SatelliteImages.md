# Satellite Image Retrieval

The RDWATCH system relies on a [STAC API](https://stacspec.org/en) to query for visual satellite images stored in the [COG (Cloud Optimized GeoTIFF)](https://www.cogeo.org/) format.  After searching for these images based on a spatial and temporal filter it will download them for display.  These COG files are stored in S3 buckets and the STAC API provides the S3 URL to the file.

## Collections

RD-WATCH will query the STAC server for 4 sources:

- WV: WorldView
- S2: Sentinel 2
- L8: Landsat 8
- PL: Planet Labs

WorldView is treated differently from the rest of Satellite Sources.  WorldView can be pansharpened if there exists additional imagery data.  This allows a higher resolution image to be displayed when compared to the other Sources.

There is an environment variable `RDWATCH_ACCENTURE_VERSION` that is used to determine the collections that are searched when querying the STAC server.

## Code Layout

The [**pystac**](https://pystac.readthedocs.io/en/stable/) library is utilized to make queries to the STAC server.

Within the **./rdwatch/core/utils** directory contains helper tools for Querying the STAC server and processing the resulting images.

In the root of that folder is a `stac_search.py` which is used for S2,L8,PL image sources.
The Collections to search for images are specified [here](https://github.com/ResonantGeoData/RD-WATCH/blob/58ab08d3d5ef7905295b9cec53b0e7a73c0dd5d6/rdwatch/core/utils/stac_search.py#L59-L62)

```
if settings.ACCENTURE_VERSION is not None:
    COLLECTIONS['S2'].append(f'ta1-s2-acc-{settings.ACCENTURE_VERSION}')
    COLLECTIONS['L8'].append(f'ta1-ls-acc-{settings.ACCENTURE_VERSION}')
    COLLECTIONS['PL'].append(f'ta1-pd-acc-{settings.ACCENTURE_VERSION}')
```

### Querying STAC

Within **./rdwatch/core/utils/satellite_bands.py** file is the main function `get_bands`.  This function performs a STAC Query for a time range and a bounding box utilizing **pystac**.  The results are typically verbose so it is paginated with 100 results at a time.  It iterates over these times and returns all 'visual' images that match the query.  If the results match a visual band image they are returned as a `Band` class.  This `Band` class contains the following information:

- **constellation**: source of image (S2, L8, PL)
- **spectrum**: Information about the spectrum the band captures (μm)
- **level**: processing level 
- **timestamp**: date of the satellite image
- **bbox**: bounding box associated with the image
- **uri**: Typically contains the S3 URL for the COG that contains the image
- **cloudcover**: optional value that will extract metadata to indicate the amount of cloud cover in the image
- **collection**: The collection this image was retrieved from

### WorldView Differences

Within the **./rdwatch/core/utils** folder there are two folders labeled **worldview**.

The base **worldview** folder is an older folder that was used for just rendering the source WorldView Images.
The **worldview_processed** folder contains tools to create a pansharpened version of the image buy downloading extra data.

Instead of having a `Band` class for worldview there is a `WoirldViewCapture` class in the base and a `WorldViewProcessedCapture`.
The older base **worldview** folder will probably be removed as deprecated

`WorldViewProcessedCapture` is similar to the `Band` class but contains an optional `panuri` property to indicate an additional S3 location of the extra image to create a pansharpened image.

the `get_captures` function in **worldview_process/satellite_captures.py** is similar to `get_bands` except there is a secondary process to attempt to find the `panuri` if available.

#### Pansharpening

For worldview if there is a secondary panchromatic image found it will use the [riotiler](https://cogeotiff.github.io/rio-tiler/) `pansharpening_brovy` function to increase the resolution of the image.

## Region Satellite Images

When viewing an entire region images can be turned on for the wole region.  It defaults to S2 as the source but WV can also be used.
It follows the following process:

1. A search for the region bounding box and a time range of 2010 to now will be search for the source images (either S2 or WV)
1. After a list of images are found the client is provided with this list.
1. When the satellite image is turned on the client will request the image closest to the current time in the slider.
1. This then uses the image list to grab the URI for this image directly and use it for serving tiles.  The URI is sent to the back-end along with the x/y/z tile.  The riotiler then uses range requests to S3 to get the requested tile from S3 and provide it to the client. This can be seen `raster_tile.py` file for both the default `utils` and the `worldview_processed` folders.

This process can be a bit slow when swithing between satellite images.  Once an image is loaded it is cached so subsquent loads become faster but the caching isn't that large for the system.

## Site Satellite Image Chipping

Instead of downloading and using a tile server to view images for a whole region there is a task (in each App: core/scoring) that will chip/crop the images for individual sites and save them in a Object Store like S3/MinIO.

Within **(core/scoring)/tasks/__init__.py** there are two functions called `generate_site_images_for_evaluation_run` and `generate_site_images`.  The `generatie_site_images_for_evaluation_run` calls `generate_site_images` for each site in a Model Run.  The core function that is eventually called is `get_siteobservations_images`.  This does the process of STAC Querying for images, processing them and eventually creating chips that are loaded into S3/MinIO.

## Image Chipping Parameters

- *site_id: UUID4* - The UUID for the Site to download 
- *constellation:=['WV']* - Watch satellite image sources to download.  Can be WV, S2, L8, PL or any combination
- *force=False* - Forces re-downloading images.  Useful if you change the filters (overrideDates, dayRange, noData) or if you believe the STAC Query has updated since last time you downloading images.
- *dayRange=14* - S2, L8, PL imagery can have dense temporal images.  I.E there may be 5-6 pictures in a week and the changes between them aren't significant.  This parameter will prevent images from downloading if an image already exists in the *dayRange*.
- *noData=50* - Filter to remove images that report having > *noData*% of noData in them.  It's intended to remove majority black images from the images downloaded.
- *overrideDates: None | list[datetime, datetime] = None* - if set to `None` it will utilize the site time range for downloading images +/- 30 days to add a buffer.  If the site time range is null it will use 20130101 to the present time.  The *overrideDates* can be used to extend or reduce the time range when downloading images.
- *scale: Literal['default', 'bits'] | list[int] = 'default'* - THe image bit scaling for the brightness levels can be adjusted herre.  The Default scaling is 0-10,000.  The `list[int]` allows for two custom values.  The `bits` option will use the 2% lows and 98% highs to adjust the scaling.
- *bboxScale: float = BboxScaleDefault* - a number that will be used to scale up the boundingbox of the area around the site downloaded.  I.E. a value of 1.2 will ad 20% to the bounding box of polygon when downloading the image.  If the site image source is now WorldView (WV) it will estimate the real world size and if the height or width are under 1000 meters it will add whatever is needed to get the size of the bbox to 1000 meters.  This is done because of the lower resolution of S2,L8,PL.  The more context helps identifying features in the image.
