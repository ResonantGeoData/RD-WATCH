import { LayerSpecification } from "maplibre-gl";
import { LocalGeoJSONFeature } from "../store";

export function localGeoJSONSources(localMapFeatures: LocalGeoJSONFeature[]) {
  return localMapFeatures.reduce((acc, feature) => {
    return {
      ...acc,
      [`local-source-${feature.id}`]: {
        type: 'geojson',
        data: feature.geojson,
      },
    }
  }, {});
}

export function localGeoJSONLayers(localMapFeatures: LocalGeoJSONFeature[]) {
  return localMapFeatures.flatMap((feature) => {
    return [
      {
        id: `local-layer-${feature.id}:fill`,
        type: 'fill',
        source: `local-source-${feature.id}`,
        layout: {
          visibility: feature.visible ? 'visible' : 'none',
        },
        paint: {
          'fill-color': '#088',
          'fill-opacity': 0.5
        },
      },
      {
        id: `local-layer-${feature.id}:outline`,
        type: 'line',
        source: `local-source-${feature.id}`,
        layout: {
          visibility: feature.visible ? 'visible' : 'none',
        },
        paint: {
          'line-color': '#055',
          'line-width': 2,
        },
      },
    ] as LayerSpecification[];
  })
}

