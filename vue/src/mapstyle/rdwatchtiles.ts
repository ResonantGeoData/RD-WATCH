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
    ["<=", ["get", "timemin"], timestamp],
    [
      "any",
      ["!", ["to-boolean", ["get", "timemax"]]],
      [">", ["get", "timemax"], timestamp],
    ],
  ];

  // Add any filters set in the UI
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && key !== "groundtruth") {
      filter.push(
        filters.groundtruth === undefined
          ? ["in", ["get", key], ["literal", value]]
          : [
              "any",
              ["in", ["get", key], ["literal", value]],
              ["get", "groundtruth"],
            ]
      );
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
    ["<=", ["get", "timemin"], timestamp],
  ];

  // Add any filters set in the UI
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && key !== "groundtruth") {
      filter.push(
        filters.groundtruth === undefined
          ? ["in", ["get", key], ["literal", value]]
          : [
              "any",
              ["in", ["get", key], ["literal", value]],
              ["get", "groundtruth"],
            ]
      );
    }
  });

  return filter;
};

const rdwatchtiles = "rdwatchtiles";
const urlRoot = `${location.protocol}//${location.host}`;
const observationColor: DataDrivenPropertyValueSpecification<string> = [
  "case",
  ["==", ["get", "label"], 1],
  "#1F77B4",
  ["==", ["get", "label"], 2],
  "#A020F0",
  ["==", ["get", "label"], 3],
  "#2CA02C",
  "#7F7F7F",
];

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
    id: "sites-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "sites",
    paint: {
      "line-color": "#FFA500",
      "line-width": 2,
    },
    filter: buildSiteFilter(timestamp, filters),
  },
  {
    id: "observations-fill",
    type: "fill",
    source: rdwatchtiles,
    "source-layer": "observations",
    paint: {
      "fill-color": observationColor,
      "fill-opacity": 0.05,
    },
    filter: buildObservationFilter(timestamp, filters),
  },
  {
    id: "observations-outline",
    type: "line",
    source: rdwatchtiles,
    "source-layer": "observations",
    paint: {
      "line-color": observationColor,
      "line-width": 2,
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
      "text-color": observationColor,
    },
    filter: buildObservationFilter(timestamp, filters),
  },
];
