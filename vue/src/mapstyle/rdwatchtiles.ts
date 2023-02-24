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

const rdwatchtiles = "rdwatchtiles";
const urlRoot = `${location.protocol}//${location.host}`;
const annotationColor: DataDrivenPropertyValueSpecification<string> = [
  "case",
  ["==", ["get", "label"], 1],
  "#1F77B4",
  ["==", ["get", "label"], 2],
  "#A020F0",
  ["==", ["get", "label"], 3],
  "#2CA02C",
  ["==", ["get", "label"], 4],
  "#2f4f4f",
  ["==", ["get", "label"], 5],
  "#228b22",
  ["==", ["get", "label"], 6],
  "#7f0000",
  ["==", ["get", "label"], 7],
  "#00008b",
  ["==", ["get", "label"], 8],
  "#ff8c00",
  ["==", ["get", "label"], 9],
  "#ffff00",
  ["==", ["get", "label"], 10],
  "#1e90ff",
  ["==", ["get", "label"], 11],
  "#00ffff",
  ["==", ["get", "label"], 12],
  "#ff00ff",
  ["==", ["get", "label"], 13],
  "#00ff00",
  ["==", ["get", "label"], 14],
  "#ff69b4",
  ["==", ["get", "label"], 15],
  "#ffe4c4",
  "#7F7F7F",
];
const observationWidth: DataDrivenPropertyValueSpecification<number> = [
  // If this observation is a grouth truth, make the width 4. Otherwise, make it 2.
  "case",
  ["get", "groundtruth"],
  4,
  2,
];

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
  filters: Record<string, number>
): LayerSpecification[] => [
  {
    id: "observations-fill",
    type: "fill",
    source: rdwatchtiles,
    "source-layer": "observations",
    paint: {
      "fill-color": annotationColor,
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
      "line-color": annotationColor,
      "line-width": observationWidth,
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
      "text-field": [
        "case",
        ["==", ["get", "label"], 1],
        "active_construction",
        ["==", ["get", "label"], 2],
        "post_construction",
        ["==", ["get", "label"], 3],
        "site_preparation",
        "",
      ],
    },
    paint: {
      "text-color": annotationColor,
    },
    filter: buildObservationFilter(timestamp, filters),
  },
  {
    id: "sites-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "sites",
    paint: {
      "line-color": annotationColor,
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
      "text-field": [
        "case",
        ["==", ["get", "label"], 6],
        "positive_annotated",
        ["==", ["get", "label"], 7],
        "positive_partial",
        ["==", ["get", "label"], 8],
        "positive_annotated_static",
        ["==", ["get", "label"], 9],
        "positive_partial_static",
        ["==", ["get", "label"], 10],
        "positive_pending",
        ["==", ["get", "label"], 11],
        "positive_excluded",
        ["==", ["get", "label"], 12],
        "negative",
        ["==", ["get", "label"], 13],
        "ignore",
        ["==", ["get", "label"], 14],
        "transient_positive",
        ["==", ["get", "label"], 15],
        "transient_negative",
        ["==", ["get", "label"], 16],
        "system_proposed",
        ["==", ["get", "label"], 17],
        "system_confirmed",
        ["==", ["get", "label"], 18],
        "system_rejected",
        "",
      ],
    },
    paint: {
      "text-color": annotationColor,
    },
    filter: buildSiteFilter(timestamp, filters),
  },
];
