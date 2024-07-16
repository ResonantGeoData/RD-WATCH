# Satellite Image Retrieval

The RDWATCH system relies on a [STAC API](https://stacspec.org/en) to query for visual satellite images stored in the [COG (Cloud Optimized GeoTIFF)](https://www.cogeo.org/) format.  After searching for these images based on a spatial and temporal filter it will download them for display.  These COG files are stored in S3 buckets and the STAC API provides the S3 URL to the file.

