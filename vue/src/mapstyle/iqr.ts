import { FilterSpecification, LayerSpecification, SourceSpecification } from "maplibre-gl";
import { ApiService, IQROrderedResultItem } from "../client/services/ApiService";
import { ImageBBox, MapFilters, siteOverviewSatSettings } from "../store";
import { annotationColors } from "./annotationStyles";
import { buildCircleRadius, buildObservationFill, buildObservationFillOpacity, buildObservationThick } from "./rdwatchtiles";

const urlRoot = `${location.protocol}//${location.host}`;

function unflattenXYXYBounds(arrBounds: [number, number, number, number]) {
  const [xmin, ymin, xmax, ymax] = arrBounds;
  return [
    [xmin, ymax],
    [xmax, ymax],
    [xmax, ymin],
    [xmin, ymin],
  ];
}

export function buildIQRImageSources(results: IQROrderedResultItem[]): Record<string, SourceSpecification> {
  return results
    .filter((item): item is IQROrderedResultItem & { image_url: string } => !!item.image_url)
    .reduce((sources, item) => {
      const sourceId = `iqrSiteImageSource_${item.site_id}`;
      return {
        ...sources,
        [sourceId]: {
          type: 'image',
          url: item.image_url,
          coordinates: (item.image_bbox ? unflattenXYXYBounds(item.image_bbox) : [[0,0], [0,0], [0,0], [0,0]]) as ImageBBox,
        },
      };
  }, {});
}

export function buildIQRImageLayers(results: IQROrderedResultItem[], settings: siteOverviewSatSettings): LayerSpecification[] {
  return results
    .filter((item): item is IQROrderedResultItem & { image_url: string } => !!item.image_url)
    .map((item) => {
      const layerId = `iqrSiteImageLayer_${item.site_id}`;
      const sourceId = `iqrSiteImageSource_${item.site_id}`;
      return {
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: {
          'raster-fade-duration': 0,
          'raster-opacity': settings.imageOpacity / 100,
        },
      };
    });
}

const buildIQRObservationFilter = (
  timestamp: number,
  filters: MapFilters
): FilterSpecification => {
  const filter: FilterSpecification = [
    "all",
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

export const buildIQRSiteFilter = (
  timestamp: number,
  filters: MapFilters
): FilterSpecification => {
  const filter: FilterSpecification = [
    "all",
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

export const buildIQRSiteVectorSources = (timestamp: number, iqrSessionId: string, randomKey='') => {
  const source = `iqrSiteVectorTileSource_${iqrSessionId}`;
  return {
    [source]:  {
      type: "vector",
      tiles: [`${urlRoot}${ApiService.getApiPrefix()}/iqr/${iqrSessionId}/vector-tile/{z}/{x}/{y}.pbf/?${randomKey}`],
      minzoom: 0,
      maxzoom: 14,
    }
  } as Record<string, SourceSpecification>;
};

export const buildIQRSiteVectorLayers = (
  timestamp: number,
  filters: MapFilters,
  iqrSessionId: string,
): LayerSpecification[] => {
  const results: LayerSpecification[] = [
    {
      id: `iqr-observations-fill-${iqrSessionId}`,
      type: "fill",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `observations-${iqrSessionId}`,
      paint: {
        "fill-color": annotationColors(filters, 'observations'),
        "fill-opacity": buildObservationFillOpacity(filters, 'observations'),
        "fill-pattern": (!filters.proposals || (!filters.proposals.accepted && !filters.proposals.rejected))
          ? buildObservationFill(timestamp, filters)
          : undefined,
      },
      filter: buildIQRObservationFilter(timestamp, filters),
    },
    {
      id: `iqr-observations-outline-${iqrSessionId}`,
      type: "line",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `observations-${iqrSessionId}`,
      paint: {
        "line-color": annotationColors(filters),
        "line-width": buildObservationThick(filters, 'observation'),
      },
      filter: buildIQRObservationFilter(timestamp, filters),
    },
    {
      id: `iqr-sites-outline-${iqrSessionId}`,
      type: "line",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `sites-${iqrSessionId}`,
      paint: {
        "line-color": annotationColors(filters),
        "line-width": buildObservationThick(filters, 'site'),
      },
      filter: buildIQRSiteFilter(timestamp, filters),
    },
    {
      id: `iqr-sites-points-outline-${iqrSessionId}`,
      type: "circle",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `sites_points-${iqrSessionId}`,
      paint: {
        "circle-color": annotationColors(filters),
        "circle-radius": buildCircleRadius(filters, 'site'),
      },
      filter: buildIQRSiteFilter(timestamp, filters),
    },
    {
      id: `iqr-observations-points-outline-${iqrSessionId}`,
      type: "circle",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `observations_points-${iqrSessionId}`,
      paint: {
        "circle-color": annotationColors(filters),
        "circle-radius": buildCircleRadius(filters, 'observation'),
      },
      filter: buildIQRObservationFilter(timestamp, filters),
    },
    {
      id: `iqr-sites-fill-${iqrSessionId}`,
      type: "fill",
      source: `iqrSiteVectorTileSource_${iqrSessionId}`,
      "source-layer": `sites-${iqrSessionId}`,
      paint: {
        "fill-color": annotationColors(filters, 'sites'),
        "fill-opacity": buildObservationFillOpacity(filters, 'sites'),
        "fill-pattern": (!filters.proposals || (!filters.proposals.accepted && !filters.proposals.rejected))
          ? buildObservationFill(timestamp, filters)
          : undefined,
      },
      filter: buildIQRSiteFilter(timestamp, filters),
    },
  ];

  return results;
};
