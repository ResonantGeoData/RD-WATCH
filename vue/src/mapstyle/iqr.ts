import { FilterSpecification, LayerSpecification, SourceSpecification } from "maplibre-gl";
import { ApiService, IQROrderedResultItem } from "../client/services/ApiService";
import { ImageBBox, MapFilters, siteOverviewSatSettings } from "../store";
import { annotationColors } from "./annotationStyles";
import { buildCircleRadius, buildObservationFill, buildObservationFillOpacity, buildObservationThick } from "./rdwatchtiles";

const urlRoot = `${location.protocol}//${location.host}`;
const CLUSTER_SOURCE_ID = 'iqrSiteImageClusterSource'
const CLUSTER_LAYER_ID = 'iqrSiteImageClusterLayer'

function unflattenXYXYBounds(arrBounds: [number, number, number, number]) {
  const [xmin, ymin, xmax, ymax] = arrBounds;
  return [
    [xmin, ymax],
    [xmax, ymax],
    [xmax, ymin],
    [xmin, ymin],
  ];
}

function xyxyBoundsCenter(xyxy: [number, number, number, number]) {
  const [xmin, ymin, xmax, ymax] = xyxy;
  return [
    (xmax + xmin) / 2,
    (ymax + ymin) / 2,
  ];
}

export function buildIQRImageSources(results: IQROrderedResultItem[]): Record<string, SourceSpecification> {
  const imageSources = results
    .filter((item): item is IQROrderedResultItem & { image_url: string } => !!item.image_url)
    .reduce((sources, item) => {
      const sourceId = `iqrSiteImageSource_${item.site_id}`;
      const clusterSourceId = `iqrSiteImageClusterSource_${item.site_id}`;
      // TODO just don't show these sources if the image bbox doesn't exist
      const imageBbox = item.image_bbox ? unflattenXYXYBounds(item.image_bbox) : [[0,0], [0,0], [0,0], [0,0]];
      const imageCenter = item.image_bbox ? xyxyBoundsCenter(item.image_bbox) : [0, 0];
      return {
        ...sources,
        [sourceId]: {
          type: 'image',
          url: item.image_url,
          coordinates: imageBbox as ImageBBox,
        },
        [clusterSourceId]: {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [
              {
                type: 'Feature',
                geometry: {
                  type: 'Point',
                  coordinates: imageCenter,
                },
              }
            ],
          },
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 5,
        },
      };
  }, {});

  const clusterSource = {
    type: 'geojson',
    data: {
      type: 'FeatureCollection',
      features: results
        .filter((item): item is IQROrderedResultItem & { image_bbox: [number, number, number, number] } => !!item.image_bbox)
        .map((item) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: xyxyBoundsCenter(item.image_bbox),
          },
        })),
    },
    cluster: true,
    clusterMaxZoom: 11,
    clusterRadius: 50,
  };

  return {
    ...imageSources,
    [CLUSTER_SOURCE_ID]: clusterSource,
  };
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

export function buildIQRClusterLayers(): LayerSpecification[] {
  return [
    {
      id: CLUSTER_LAYER_ID,
      type: 'circle',
      source: CLUSTER_SOURCE_ID,
      filter: ['has', 'point_count'],
      paint: {
        // thresholds: 10, 50
        'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6',
            10,
            '#f1f075',
            50,
            '#f28cb1'
        ],
        'circle-radius': [
            'step',
            ['get', 'point_count'],
            20,
            10,
            30,
            50,
            40
        ]
      }
    },
    {
      id: `${CLUSTER_LAYER_ID}_counts`,
      type: 'symbol',
      source: CLUSTER_SOURCE_ID,
      filter: ['has', 'point_count'],
      layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['Roboto Regular'],
          'text-size': 12,
      },
    },
  ];
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
