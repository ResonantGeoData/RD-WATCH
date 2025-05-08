/**
 * OpenStreetMap
 */

import type { LayerSpecification, SourceSpecification } from "maplibre-gl";
import { MapFilters } from "../store";

const openmaptiles = "openmaptiles";

const source: SourceSpecification = {
  minzoom: 0,
  maxzoom: 14,
  type: 'raster',
  tiles: [
    'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
  ],
  tileSize: 256,
  attribution: '© OpenStreetMap contributors',
};
export const defaultSources = { openmaptiles: source };
export const sources = (filters: MapFilters) => {
  if (filters.drawMap) {
    return defaultSources;
  }
  return {};
}

export const layers = (filters: MapFilters) => {
  if (filters.drawMap) {
    return defaultLayers;
  }
  return [];
}
export const defaultLayers: LayerSpecification[] = [
  {
    id: 'osm-tiles',
    type: 'raster',
    source: 'openmaptiles',
    maxzoom: 19,
  },
  
];
