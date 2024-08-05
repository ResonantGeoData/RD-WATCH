
# Model Run List (Left Side Panel)

## Mode Selection

Select between Analyst and Annotator Mode.
If the database is not **RDWATCH** it will display that the Source is **Scoring**.  The Database selection is persistent so reloading the page won't reset the source.  The source database can be set in the **Settings**.

## Timeline Slider

The Model Runs contain Sites and Site Observations that vary over time.  This time slider is a global setting that indicates the current time selection so the proper Site Observations and Satellite images are displayed.

The Timeline Slider start/end date are set auomatically based on the list of model runs being displayed, or the model runs that are selected.  Any other tools that adjust the current time will be reflected in this global time slider.

## Global Map/Model Run Settings

There is a row of icons that are used to adjust settings in the system.

- **==:material-road:== Base Map Visibility**: Turns on/off the base map (roads, boundaries, land vs water).  This is useful to create a screenshot without giving spatial clues as to the location of the polygons being visualized.
- **==:material-satellite-variant:== Satellite Images**: This button will download and cache the satellite timestamps initially and then allow toggling on/off region base satellite images.  The first time this is clicked there is a warning because the system will query the STAC API to find all satellite images for the region during the time period currently displayed in the **Time Slider**.  After this is complete a display of the number of Satellite Images will be displayed next to the Number of Model Runs below the ModelRun filter.  If there are images found the icon will change to **==:material-image:==** indicating that the satellite image can be turned on.  Once a satellite image is turned on the location where the number of satellite images were displayed will change to the closest timestamp of satellite image that matches the current global time set in the **Time Slider**
- **==:material-format-text:== Format Text**: This turns on text status labels for the Site and Site Observations in the Map.  It is disabled by default because the density of labels can make it difficult to see the polygons.
- **==:material-map-legend:== Map Legend**: Toggles on/off the map legend.  The map legend changes based on the type of visible annotations
- **==:material-check-decagram:== Ground Truth**: By default the ModelRun list only contains user runs.  This will show all of the GroundTruth Model runs.  GroundTruth model runs are indicated as GroundTruth when they are ingested into RDWATCH.  GroundTruth Model Runs, Sites and Site Observations are all indicated by the following icon: ==:material-check-decagram:==
- **:material-settings:== Settings**: Opens the Settings panel to adjust settings for the system.  See the **Settings** section to get more information

## ModelRun Filters

 - **Performer Filter**: this will filter model runs based on the performer
 - **Region Filter**: filters model runs by their associated region.  Regions that are user created and that are public will be included at the top of the list.  All other Regions will be in alphebetical order.  The region filter will be added to the URL and can be copied and pasted.  If pasted into a browser it will open with the filter pre-selected.

### Scoring Filters

When connected to the Scoring Database there are additional filters that are displayed

- **Mode Filter**: Filters the scoring results based on modes (**batch** or **incremental**)
- **Evaluation Filter**: When scoring a model run they are all tied to an **Evaluation Number**.  This filter will adjust the results base don this value.

## Model Run Information

Directly below the filters is small area that includes two pieces of information

-**# of Model Runs** - A small tag that indicates the number of model runs that the current filter shows
-**# of SatelliteImages / Current Satellite Image Timestamp** - If the satellite images are turned on or if there are cached a list of a satellite images this will display either the total number of satellite images found for the region.  If the image is currently turned on it will display the current timestamp for the satellite image.

## Model Run Card

Each model run card in the list can be selected by either clicking on the card or the checkbox for the card.  Once clicked on, the camera will zoom to the region for the model run and indicate it is selected by filling in the checkbox and highlight the model run card.

### Model Run Card Information

- **Title**: a descriptive title for the model run is located at the top
- **Region**: Associated region for the model run.
- **Date Coverage**: Analyzes the Sites in the listing and displays the Date Coverage for the Model Run
- **Last Updated**: The timestamp of the model run being added or updated

- **Model Run TimeSlider**: A slider that is bound to the start/end date based on the **Date Coverage**.  When moved this will adjust the global time slider.

- **==:material-map-marker-outline:== Site Number**: Number of Sites in the Model Run
- **==:material-license:== Average Score**:  Indication of the average score of the sites in the Model Run
- **Scoring Database Only**
    - **==:material-checkbox-multiple-blank:== Batch Mode**: Using scoring database this indicates batch mode
    - **==:material--trending-up:==**: ?Using scoring database this indicates incremental mode

### Model Run Actions

- **RDWATCH Database Only**
    - **==:material-download-box-outline:== Download GeoJSON**:  Downloads a Zip file that contains all of the geoJSON for the sites that are displayed.
- **==:material-image:== Satellite Image Downloading**:  Opens a dialog to begin downloading Satellite Images for all of the Sites in the model run.
