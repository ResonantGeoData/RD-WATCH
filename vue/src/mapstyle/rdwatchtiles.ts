/**
 * RD-WATCH vector tiles
 */

import type {
  DataDrivenPropertyValueSpecification,
  FilterSpecification,
  LayerSpecification,
  SourceSpecification,
} from "maplibre-gl";
import type { MapFilters } from "../store";

import { annotationColors, observationText, siteText } from "./annotationStyles";

// function buildSearchFilters(filters: MapFilters) {
//   const filter: FilterSpecification = ["all"];
//   if (filters.groundtruth) {
//     Object.entries(filters).forEach(([key, value]) => {
//       if (value !== undefined && key !== "groundtruth") {
//         filter.push([
//           "any",
//           ["in", ["get", key], value],
//           ["get", "groundtruth"],
//         ]);
//       }
//     });
//     if (filter.length === 1) {
//       filter.push(["get", "groundtruth"]);
//     }
//   } else {
//     Object.entries(filters).forEach(([key, value]) => {
//       if (value !== undefined && key !== "groundtruth") {
//         filter.push([["in", ["get", key], value]]);
//       }
//     });
//   }
//   return filter;
// }

const buildTextOffset = (type: 'site' | 'observation', filters: MapFilters): [number, number] => {
  if (filters.showSiteOutline && type === 'site') {
    return [0, 0.5];
  } else if (filters.showSiteOutline && type === 'observation') {
    return [0, -0.5];
  }
  return [0, 0];
}

export const buildObservationFilter = (
  timestamp: number,
  filters: MapFilters
): FilterSpecification => {
  const filter: FilterSpecification = [
    "all",
    [
      "in",
      ["get", "configuration_id"],
      [
        "literal",
        filters.configuration_id?.length ? filters.configuration_id : [""],
      ],
    ],
    [
      "in",
      ["get", "region_id"],
      ["literal", filters.region_id?.length ? filters.region_id : [""]],
    ],
    ["<=", ["get", "timemin"], timestamp],
    [
      "any",
      ["!", ["to-boolean", ["get", "timemax"]]],
      [">", ["get", "timemax"], timestamp],
    ],
  ];

  // Add any filters set in the UI
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && typeof value === "string") {
      filter.push(["in", ["get", key], ["literal", value]]);
    }
  });
  return filter;
};

export const buildSiteFilter = (
  timestamp: number,
  filters: MapFilters
): FilterSpecification => {
  const filter: FilterSpecification = [
    "all",
    [
      "in",
      ["get", "configuration_id"],
      [
        "literal",
        filters.configuration_id?.length ? filters.configuration_id : [""],
      ],
    ],
    [
      "any",
      // When the site_polygon attribute is present, that indicates that there are no
      // observations associated with this model run and that the main site polygon
      // should be rendered regardless of timestamp
      ["get", "site_polygon"],
      ["<=", ["get", "timemin"], timestamp],
    ],
    ["literal", !!filters.showSiteOutline],
  ];

  // Add any filters set in the UI
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && typeof value === "string") {
      filter.push(["in", ["get", key], ["literal", value]]);
    }
  });

  return filter;
};

export const buildRegionFilter = (
  filters: MapFilters
): FilterSpecification => {
  const filter: FilterSpecification = [
    "literal", !!filters.showRegionPolygon,
  ];

  return filter;
};

const rdwatchtiles = "rdwatchtiles";
const urlRoot = `${location.protocol}//${location.host}`;


const buildObservationThick = (filters: MapFilters): DataDrivenPropertyValueSpecification<number>  => {
  // If this observation is a grouth truth, make the width 4. Otherwise, make it 2.
 return[ "case",
  ["get", "groundtruth"],
  4,
  ["==", ["get", "siteeval_id"],
  filters.hoverSiteId ? filters.hoverSiteId : ''],
  6,
  2,
];
}

const buildObservationFill = (
  timestamp: number,
  filters: MapFilters
): DataDrivenPropertyValueSpecification<string> => {
  return [
    "case",
    ["get", "groundtruth"],
    !!filters.groundTruthPattern ? "diagonal-right" : "",
    ["!=", ["get", "groundtruth"], true],
    !!filters.otherPattern ? "diagonal-left" : "",
    "",
  ];
};

const source: SourceSpecification = {
  type: "vector",
  tiles: [`${urlRoot}/api/vector-tile/{z}/{x}/{y}.pbf`],
  minzoom: 0,
  maxzoom: 14,
};
export const sources = { rdwatchtiles: source };

export const layers = (
  timestamp: number,
  filters: MapFilters
): LayerSpecification[] => [
  {
    id: "observations-fill",
    type: "fill",
    source: rdwatchtiles,
    "source-layer": "observations",
    paint: {
      "fill-color": (annotationColors(filters)),
      "fill-opacity": 1,
      "fill-pattern": buildObservationFill(timestamp, filters),
    },
    filter: buildObservationFilter(timestamp, filters),
  },
  {
    id: "observations-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "observations",
    paint: {
      "line-color": annotationColors(filters),
      "line-width": buildObservationThick(filters),
    },
    filter: buildObservationFilter(timestamp, filters),
  },
  {
    id: "observations-text",
    type: "symbol",
    source: rdwatchtiles,
    "source-layer": "observations",
    layout: {
      "text-anchor": "center",
      "text-font": ["Roboto Regular"],
      "text-max-width": 5,
      "text-size": 12,
      "text-allow-overlap": true,
      "text-offset": buildTextOffset('observation', filters),
      "text-field": observationText,
    },
    paint: {
      "text-color": annotationColors(filters),
    },
    filter: buildObservationFilter(timestamp, filters),
  },
  {
    id: "regions-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "regions",
    paint: {
      "line-color": annotationColors(filters),
      "line-width": 2,
    },
    filter: buildRegionFilter(filters),
  },
  {
    id: "sites-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "sites",
    paint: {
      "line-color": annotationColors(filters),
      "line-width": 2,
    },
    filter: buildSiteFilter(timestamp, filters),
  },
  {
    id: "sites-text",
    type: "symbol",
    source: rdwatchtiles,
    "source-layer": "sites",
    layout: {
      "text-anchor": "center",
      "text-font": ["Roboto Regular"],
      "text-max-width": 5,
      "text-size": 12,
      "text-allow-overlap": true,
      "text-offset": buildTextOffset('site', filters),
      "text-field": siteText,
    },
    paint: {
      "text-color": annotationColors(filters),
    },
    filter: buildSiteFilter(timestamp, filters),
  },
];
