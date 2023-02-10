/**
 * Shaded relief
 */

import type { LayerSpecification, SourceSpecification } from "maplibre-gl";

const naturalearth = "naturalearth";
const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
const source: SourceSpecification = {
  maxzoom: 6,
  tileSize: 256,
  tiles: [`${tileServerURL}/raster/{z}/{x}/{y}.webp`],
  type: "raster",
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
