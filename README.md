


# RD-WATCH

<img width="1857" alt="Screenshot 2024-02-17 at 3 40 47 PM" src="https://github.com/ResonantGeoData/RD-WATCH/assets/146527/a2c3431b-2d0a-4295-b302-5d4e08c84b84">


## Introduction

RDWATCH (**R**esonantGeo**D**ata **WATCH**) is a modern web application that offers easy access to a wide range of remote sensing imagery, as well as AI-generated outputs, to aid in the detection of global scale changes. RDWATCH enhances the AI workflow by providing monitoring, annotating, and visualizing capabilities within a geospatial context. The web interface of RDWATCH prioritizes user experience and performance for different user groups, including analysts, annotators, and algorithm developers. It enables analysts to thoroughly examine model outputs, allows annotators to work within a geospatial context, and assists developers in comparing results with ground truth to identify potential model failures.


# RDWATCH Features

## For Developers

-  **Scalable and Modular Architecture**: Built on top of widely used Django web framework and open source geospatial technologies in a architecture that is flexible and extensible.

-  **Efficient Data Management**: RDWATCH provides domain specific data models that provide fast search across data types.

-  **Advanced Technology Stack**: Leverage dynamic vector tiles, open standards like STAC, and open-source software (MapLibre, Vue.js) on AWS for scalability.

## For Annotators and Analysts

-  **Enhanced Workflow**: Interfaces for efficient monitoring, annotating, and visualizing geospatial data within a geospatial context.

-  **Interactive Visualizations**: Dynamic observation of data changes over time, directly in the web interface, enhancing the annotation process.

-  **Exporting Capabilities**: Easily export model outputs and imagery, facilitating collaboration and sharing in formats like GIF and GeoJSON.

## Getting Started

To install the CLI:
```bash
pip  install  rdwatch-cli  --find-links  https://resonantgeodata.github.io/RD-WATCH/
```


## Documentation

* [Development](https://github.com/ResonantGeoData/RD-WATCH/blob/main/DEVELOPMENT.md)

* [Data Ingestion](https://github.com/ResonantGeoData/RD-WATCH/blob/main/INGESTION.md)


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
