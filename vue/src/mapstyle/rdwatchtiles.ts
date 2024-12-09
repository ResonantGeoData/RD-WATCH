/**
 * RD-WATCH vector tiles
 */

import type {
  DataDrivenPropertyValueSpecification,
  ExpressionSpecification,
  FilterSpecification,
  LayerSpecification,
  SourceSpecification,
} from "maplibre-gl";
import type { MapFilters } from "../store";
import { state } from "../store";

import {
  annotationColors,
  observationText,
  scoringColors,
  siteText,
} from "./annotationStyles";
import { ApiService } from '../client/services/ApiService';

const buildTextOffset = (
  type: "site" | "observation",
  filters: MapFilters
): [number, number] => {
  if (filters.drawSiteOutline && type === "site") {
    return [0, 0.5];
  } else if (filters.drawSiteOutline && type === "observation") {
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
  const hasGroundTruth = filters.drawObservations?.includes('groundtruth');
  const hasModel = filters.drawObservations?.includes('model');
  if (!hasGroundTruth && hasModel) {
    filter.push([
        "any",
        ["==", ["get", "groundtruth"], false]
      ]
    );
  } else if (!hasModel && hasGroundTruth) {
    filter.push([
      "any",
      ["==", ["get", "groundtruth"], true]
    ]);
  } else if (!hasModel && !hasGroundTruth) {
    return false;
  }
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
  ];

  if (filters.siteTimeLimits) {
    filter.push(
      [
        'all',
        [
          "case",
          ["==", ["to-boolean", ["get", "timemin"]], false], true,
          ["<=", ["get", "timemin"], timestamp], true,
          false
        ],
        [
          "case",
          ["==", ["to-boolean", ["get", "timemax"]], false], true,
          [">", ["get", "timemax"], timestamp], true,
          false,
        ],
      ]
    );
  }
  if (filters.editingGeoJSONSiteId) {
    filter.push(
      [
        'all',
        [
          "case",
          ["==", ["get", "id"], filters.editingGeoJSONSiteId], false,
          true
        ],
      ]
    )
  }

  const hasGroundTruth = filters.drawSiteOutline?.includes('groundtruth');
  const hasModel = filters.drawSiteOutline?.includes('model');
  if (!filters.drawSiteOutline && !filters.scoringColoring) {
    return false;
  }
  // Scoring:  we need to draw ground truth and sites but filter based on simple/detailed coloring props
  if (filters.scoringColoring) {
    filter.push([
      "any",
      ["get", "site_polygon"],
      ["literal", true],
      ]
    );

    // Next filter on the color_code being either simple or detailed
    const filtered = Object.values(scoringColors).filter((item) => (item.simple && filters.scoringColoring === 'simple') || (item.detailed && filters.scoringColoring === 'detailed'))
    const renderColorCodes = filtered.map((item) => item.id)
    // Now we only display items with matching colorcode;
    const colorModeFilter = [];
    colorModeFilter.push('any');
    for (const [modelRunId, colorCodeMapping] of Object.entries(state.modelRunColorCodeMappings)) {
      for (const [siteId, colorCode] of Object.entries(colorCodeMapping)) {
        colorModeFilter.push([
          'all',
          ['==', ['get', 'base_site_id'], siteId],
          ['==', ['get', 'configuration_id'], modelRunId],
          ['literal', renderColorCodes.includes(colorCode)]
        ]);
      }
    }
    filter.push(colorModeFilter as ExpressionSpecification);

    return filter;

  }

  if (hasModel) {
    filter.push([
      "any",
      // When the site_polygon attribute is present, that indicates that there are no
      // observations associated with this model run and that the main site polygon
      // should be rendered regardless of timestamp
      ["get", "site_polygon"],
      ["literal", !!filters.drawSiteOutline],
      ]
    )
  }

  if (!hasGroundTruth && hasModel) {
    filter.push([
        "any",
        ["==", ["get", "groundtruth"], false]
      ]
    );
  } else if (!hasModel && hasGroundTruth) {
    filter.push([
      "any",
      ["==", ["get", "groundtruth"], true]
    ]);
  } else if (!hasModel && !hasGroundTruth && !filters.scoringColoring) {
    return false;
  }

  return filter;
};

export const buildRegionFilter = (filters: MapFilters): FilterSpecification => {
  const filter: FilterSpecification = ["literal", !!filters.drawRegionPoly];

  return filter;
};

const urlRoot = `${location.protocol}//${location.host}`;

export const buildObservationThick = (
  filters: MapFilters,
  siteObs: 'site' | 'observation'
): DataDrivenPropertyValueSpecification<number> => {
  // If this observation is a grouth truth, make the width 4. Otherwise, make it 2.
  const idVal = siteObs === 'site' ? 'id' : 'siteeval_id'
  return [
    "case",
    [
      "==",
      ["get", idVal],
      filters.hoverSiteId ? filters.hoverSiteId : "",
    ],
    6,
    ["get", "groundtruth"],
    4,
    2,
  ];
};

export const buildCircleRadius = (
  filters: MapFilters,
  siteObs: 'site' | 'observation'
): DataDrivenPropertyValueSpecification<number> => {
  // If this observation is a grouth truth, make the width 4. Otherwise, make it 2.
  const idVal = siteObs === 'site' ? 'id' : 'siteeval_id'
  return [
    "case",
    [
      "==",
      ["get", idVal],
      filters.hoverSiteId ? filters.hoverSiteId : "",
    ],
    12,
    ["get", "groundtruth"],
    10,
    8,
  ];
};

export const buildObservationFillOpacity = (filters: MapFilters, fillProposals?: 'sites' | 'observations'): DataDrivenPropertyValueSpecification<number> | number =>  {
  if (filters.proposals && (filters.proposals.accepted?.length || filters.proposals.rejected?.length)) {
    const result = [];
    const idKey = fillProposals === 'sites' ? 'id' : 'siteeval_id'
    result.push('case');
    result.push(['in', ['get', idKey], ['literal', filters.proposals.accepted]])
    result.push(0.25);
    result.push(['in', ['get', idKey], ['literal', filters.proposals.rejected]])
    result.push(0.25);
    if (filters.groundTruthPattern) {
      result.push(['get', "groundtruth"])
      result.push(0.45);
    }

    result.push(0);
    return result as DataDrivenPropertyValueSpecification<number>;
  }
  else if (filters.groundTruthPattern) {
    const result = [];
    result.push('case');
    result.push(['get', "groundtruth"])
    result.push(0.45);
    result.push(0.45);
    return result as DataDrivenPropertyValueSpecification<number>;
  } else if (filters.proposals) {
    return 0;
  }


  return 1;
}

export const buildObservationFill = (
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

// Nudge is used to refresh vector tiles when modified by proposal view
export const buildSourceFilter = (timestamp: number, modelRunIds: string[], regionIds: number[], randomKey='') => {
  const results: Record<string, SourceSpecification> = {};
  modelRunIds.forEach((id) => {
    const source = `vectorTileSource_${id}`;
    results[source] = {
      type: "vector",
      tiles: [`${urlRoot}${ApiService.getApiPrefix()}/model-runs/${id}/vector-tile/{z}/{x}/{y}.pbf/?${randomKey}`],
      minzoom: 0,
      maxzoom: 14,
    };
  });
  if (!ApiService.isScoring()) {
    regionIds.forEach((id) => {
    const source = `vectorTileRegionSource_${id}`;
    results[source] = {
      type: "vector",
      tiles: [`${urlRoot}${ApiService.getApiPrefix()}/regions/${id}/vector-tile/{z}/{x}/{y}.pbf/`],
      minzoom: 0,
      maxzoom: 14,
    };
    });
  }
  return results;
};

export const buildLayerFilter = (
  timestamp: number,
  filters: MapFilters,
  modelRunIds: string[],
  regionIds: number[],
): LayerSpecification[] => {
  let results: LayerSpecification[] = [];
  modelRunIds.forEach((id) => {

    const observationSpec: LayerSpecification =       {
      id: `observations-fill-${id}`,
      type: "fill",
      source: `vectorTileSource_${id}`,
      "source-layer": `observations-${id}`,
      paint: {
        "fill-color": annotationColors(filters, 'observations'),
        "fill-opacity": buildObservationFillOpacity(filters, 'observations'),
      },
      filter: buildObservationFilter(timestamp, filters),
    };
    if (observationSpec.paint && (!filters.proposals || (!filters.proposals.accepted && !filters.proposals.rejected))) {
      observationSpec.paint['fill-pattern'] = buildObservationFill(timestamp, filters);
    }
    results.push(observationSpec);

    results = results.concat([
      {
        id: `observations-outline-${id}`,
        type: "line",
        source: `vectorTileSource_${id}`,
        "source-layer": `observations-${id}`,
        paint: {
          "line-color": annotationColors(filters),
          "line-width": buildObservationThick(filters, 'observation'),
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
          "line-width": buildObservationThick(filters, 'site'),
        },
        filter: buildSiteFilter(timestamp, filters),
      },
      // Site fill is added for Hover Popup to work on the area inside the polygon
    ]);

    results.push({
      id: `sites-points-outline-${id}`,
      type: "circle",
      source: `vectorTileSource_${id}`,
      "source-layer": `sites_points-${id}`,
      paint: {
        "circle-color": annotationColors(filters),
        "circle-radius": buildCircleRadius(filters, 'site'),
      },
      filter: buildSiteFilter(timestamp, filters),
    });

    results.push({
      id: `observations-points-outline-${id}`,
      type: "circle",
      source: `vectorTileSource_${id}`,
      "source-layer": `observations_points-${id}`,
      paint: {
        "circle-color": annotationColors(filters),
        "circle-radius": buildCircleRadius(filters, 'observation'),
      },
      filter: buildObservationFilter(timestamp, filters),
    });
    const siteFill: LayerSpecification =   {
      id: `sites-fill-${id}`,
      type: "fill",
      source: `vectorTileSource_${id}`,
      "source-layer": `sites-${id}`,
      paint: {
        "fill-color": annotationColors(filters, 'sites'),
        "fill-opacity": buildObservationFillOpacity(filters, 'sites'),
      },
      filter: buildSiteFilter(timestamp, filters),
    };
    if (siteFill.paint && (!filters.proposals || (!filters.proposals.accepted && !filters.proposals.rejected))) {
      siteFill.paint['fill-pattern'] = buildObservationFill(timestamp, filters);
    }
    results.push(siteFill);


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
  regionIds.forEach((id) => {
    if (!ApiService.isScoring()) {
      results.push( {
        id: `baseregions-outline-${id}`,
        type: "line",
        source: `vectorTileRegionSource_${id}`,
        "source-layer": `regions-${id}`,
        paint: {
          "line-color": annotationColors(filters),
          "line-width": 2,
        },
        filter: buildRegionFilter(filters),
      });
    }
  });
  return results;
};
