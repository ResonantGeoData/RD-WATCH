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

import {
  annotationColors,
  observationText,
  siteText,
} from "./annotationStyles";

import {ApiService} from "../client";

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

const buildTextOffset = (
  type: "site" | "observation",
  filters: MapFilters
): [number, number] => {
  if (filters.showSiteOutline && type === "site") {
    return [0, 0.5];
  } else if (filters.showSiteOutline && type === "observation") {
    return [0, -0.5];
  }
  return [0, 0];
};

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
      ["get", "region"],
      ["literal", filters.regions?.length ? filters.regions : [""]],
    ],
    [
      "any",
      ["!", ["to-boolean", ["get", "timemin"]]],
      ["<=", ["get", "timemin"], timestamp],
    ],
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
      ["literal", !!filters.showSiteOutline],
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

export const buildRegionFilter = (filters: MapFilters): FilterSpecification => {
  const filter: FilterSpecification = ["literal", !!filters.showRegionPolygon];

  return filter;
};

const urlRoot = `${location.protocol}//${location.host}`;

const buildObservationThick = (
  filters: MapFilters
): DataDrivenPropertyValueSpecification<number> => {
  // If this observation is a grouth truth, make the width 4. Otherwise, make it 2.
  return [
    "case",
    [
      "==",
      ["get", "siteeval_id"],
      filters.hoverSiteId ? filters.hoverSiteId : "",
    ],
    6,
    ["get", "groundtruth"],
    4,
    2,
  ];
};

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

export const buildSourceFilter = (modelRunIds: number[]) => {
  const results: Record<string, SourceSpecification> = {};
  modelRunIds.forEach((id) => {
    const source = `vectorTileSource_${id}`;
    results[source] = {
      type: "vector",
      tiles: [`${urlRoot}${ApiService.apiPrefix}/model-runs/${id}/vector-tile/{z}/{x}/{y}.pbf/`],
      minzoom: 0,
      maxzoom: 14,
    };
  });
  return results;
};

export const buildLayerFilter = (
  timestamp: number,
  filters: MapFilters,
  modelRunIds: number[]
): LayerSpecification[] => {
  let results: LayerSpecification[] = [];
  modelRunIds.forEach((id) => {
    results = results.concat([
      {
        id: `observations-fill-${id}`,
        type: "fill",
        source: `vectorTileSource_${id}`,
        "source-layer": `observations-${id}`,
        paint: {
          "fill-color": annotationColors(filters),
          "fill-opacity": 1,
          "fill-pattern": buildObservationFill(timestamp, filters),
        },
        filter: buildObservationFilter(timestamp, filters),
      },
      {
        id: `observations-outline-${id}`,
        type: "line",
        source: `vectorTileSource_${id}`,
        "source-layer": `observations-${id}`,
        paint: {
          "line-color": annotationColors(filters),
          "line-width": buildObservationThick(filters),
        },
        filter: buildObservationFilter(timestamp, filters),
      },
      {
        id: `regions-outline-${id}`,
        type: "line",
        source: `vectorTileSource_${id}`,
        "source-layer": `regions-${id}`,
        paint: {
          "line-color": annotationColors(filters),
          "line-width": 2,
        },
        filter: buildRegionFilter(filters),
      },
      {
        id: `sites-outline-${id}`,
        type: "line",
        source: `vectorTileSource_${id}`,
        "source-layer": `sites-${id}`,
        paint: {
          "line-color": annotationColors(filters),
          "line-width": 2,
        },
        filter: buildSiteFilter(timestamp, filters),
      },
    ]);
    if (filters.showText) {
      results = results.concat([{
        id: `sites-text-${id}`,
        type: "symbol",
        source: `vectorTileSource_${id}`,
        "source-layer": `sites-${id}`,
        layout: {
          "text-anchor": "center",
          "text-font": ["Roboto Regular"],
          "text-max-width": 5,
          "text-size": 12,
          "text-allow-overlap": true,
          "text-offset": buildTextOffset("site", filters),
          "text-field": siteText,
        },
        paint: {
          "text-color": annotationColors(filters),
        },
        filter: buildSiteFilter(timestamp, filters),
      },
      {
        id: `observations-text-${id}`,
        type: "symbol",
        source: `vectorTileSource_${id}`,
        "source-layer": `observations-${id}`,
        layout: {
          "text-anchor": "center",
          "text-font": ["Roboto Regular"],
          "text-max-width": 5,
          "text-size": 12,
          "text-allow-overlap": true,
          "text-offset": buildTextOffset("observation", filters),
          "text-field": observationText,
        },
        paint: {
          "text-color": annotationColors(filters),
        },
        filter: buildObservationFilter(timestamp, filters),
      }]);

    }
  });
  return results;
};
