# Vocabulary and Terms

RDWATCH and the underlying SMART project have numerous Domain specific language and data structures.  This page helps define common terms.

## Background

RDWATCH is meant to display geometry (polygons/points) in a geospatial and temporal context with annotations on an interactive map.  Geometry can exist for a single point in time (SiteObservation) or for a time interval (Site).  The original purpose for RDWATCH was to compare Construction states (Site Preparation, Active Construction, Post Construction) for polygons with a GroundTruth.  This was to inspect the accuracy of algorithms that are meant to detect these states from Satellite Images.

## Analyst Mode

This mode is made for reviewing the results of algorithms and comparing them with ground truth

## Annotator Mode

This mode allows for modification of Sites and Site Observations.  This includes modifying the *Status*, *Time/Time Range* or the *Polygon*.  These sites/site Observations can be approved or rejected and the geoJSON can be exported.

## Data Hierarchy

- *Region*: A polygon indicating an area on the globe where Model Runs can be located
- *Performer*: A Name for an organization/individual/group that creates a Model Run.
- *GroundTruth*: A Model Run in a Region that contains Groundtruth Sites and Site Observations for comparison with non GroundTruth Model Runs
- *Model Run*: a collection of Sites that contain Site Observations.  ModelRuns are identified with a *title* and have a *Region* as well as a *Performer*.  Model Runs are filtered by their Region, Performer or if they are *GroundTruth*
- *Site*: A Point or Polygon that extends over a Range of time.  The Site also has it's own State annotation that indicates information about the Site (positive, negative, ignore, syse,_conmfirmed).  It has a start date and an end date.  These dates can be `null` if the Start Date and End Date are unknown.  These dates are used in RDWATCH to filter and display the Sites.  A Site is a parent to zero or more Site Observations.
- *Site Observation*:  A Point or Polygon that is associated with a specific point in time.  It has a date as well as a state (Site Preparation, Active Construction, Post Construction).  A Site Observation is always associated with a Site.

## Satellite Images

The RDWATCH system relies on a [STAC API](https://stacspec.org/en) to query for visual satellite images stored in the [COG (Cloud Optimized GeoTIFF)](https://www.cogeo.org/) format.  After searching for these images based on a spatial and temporal filter it will download them for display.  These COG files are stored in S3 buckets and the STAC API provides the S3 URL to the file.

### Region Satellite Mode

This mode will convert a specificif COG image into a tile server so that a whole region can be displayed at once.  This defaults to utilizing Sentinel 2 (S2) for the image source.  In the settings it can be modified to WorldView (WV) but the download would take more time.

### Satellite Site Chipping

There is an option to download individual images around the region of a Site Polygon.  This still uses the STAC API to get the COG files, but then takes those files and crops them to an area around the polygon and stores them in MinIO/S3 for faster access when compared to accessing a COG.

### Satellite Sources

- Simple Sources
    - **S2: Sentinel 2**
    - **L8: LandSat 8**
    - **PL: PlanetLabs**
    - These simple sources are lower resolution and may have a higher frequency of images across a given time range.  This is why in the download settings there is a **Day Limit** that can be used to limit it so only one image is downloaded every X days.
- PanSharpened
    - **WV**: WorldView
    - Pansharpening is a post process that occurs if there are multiple images that can be referenced.  This combines the images and creates a higher resolution image.
    - The day limits aren't applied to WorldView images because they aren't as frequent as the other sources and having the higher resolution is beneficial.

## Future SmartFlow Documentation
