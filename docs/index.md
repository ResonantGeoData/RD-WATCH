# RD-WATCH Documentation

<p>
  <img height="250" width="250" style="margin-right: 50px;" src="images/General/logo.svg">
</p>

RDWATCH (ResonantGeoData WATCH) is a modern web application that offers easy access to a wide range of remote sensing imagery, as well as AI-generated outputs, to aid in the detection of global scale changes. RDWATCH enhances the AI workflow by providing monitoring, annotation, and visualization capabilities within a geospatial context. The web interface of RDWATCH prioritizes a higly ergononmic user experience and application performance for different user groups, including analysts, annotators, and algorithm developers. It enables analysts to thoroughly examine model outputs, allows annotators to work within a geospatial context, and assists developers in comparing results with ground truth to identify potential model failures.

<img height="100" width="100" style="margin-right: 50px;" src="images/General/Kitware-Logo-Stacked.png">

RDWATCH is maintained and supported by [Kitware](https://www.kitware.com).


## RDWATCH Features

## For Developers

-  **Scalable and Modular Architecture**: Built on top of the widely used Django web framework and open source geospatial technologies in an architecture that is flexible and extensible.

-  **Efficient Data Management**: Domain-specific data models enable fast search across data types.

-  **Advanced Technology Stack**: Supports dynamic vector tiles, open standards like STAC, and open-source software (MapLibre, Vue.js) on AWS for scalability.

## For Annotators and Analysts

-  **Enhanced Workflow**: Provides interfaces for efficient monitoring, annotation, and visualization of geospatial data.

-  **Interactive Visualizations**: Dynamic observation of data changes over time, directly in the web interface, enhancing the annotation process.

-  **Exporting Capabilities**: Easily export model outputs and imagery, facilitating collaboration and sharing in formats like GIF and GeoJSON.


## Documentation

* [Development](DevDocs/GettingStarted.md)

* [Data Ingestion](DevDocs/IngestingData.md)


## Related Work

* [Danesfield](https://github.com/Kitware/Danesfield-App)


## Acknowledgement

This research is based upon work supported in part by the Office of the
Director of National Intelligence (ODNI), 6 Intelligence Advanced Research
Projects Activity (IARPA), via 2021-2011000005. The views and conclusions
contained herein are those of the authors and should not be interpreted as
necessarily representing the official policies, either expressed or implied, of
ODNI, IARPA, or the U.S. Government. The U.S. Government is authorized to
reproduce and distribute reprints for governmental purposes, notwithstanding any
copyright annotation therein.

For more information, visit [RDWATCH on GitHub](https://github.com/ResonantGeoData/RD-WATCH).
