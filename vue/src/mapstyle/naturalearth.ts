/**
 * Shaded relief
 */

import type { LayerSpecification, SourceSpecification } from "maplibre-gl";

const naturalearth = "naturalearth";
const source: SourceSpecification = {
  maxzoom: 6,
  type: 'raster',
  tiles: [
    'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
  ],
  tileSize: 256,
  attribution: '© OpenStreetMap contributors',
};
export const sources = { naturalearth: source };

export const layers: LayerSpecification[] = [
  {
    id: "naturalearth",
    type: "raster",
    source: naturalearth,
    maxzoom: 6,
    paint: {
      "raster-opacity": [
        "interpolate",
        ["exponential", 1.5],
        ["zoom"],
        0,
        0.6,
        6,
        0.1,
      ],
    },
  },
];
