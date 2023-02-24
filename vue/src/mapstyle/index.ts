import {
  layers as naturalearthLayers,
  sources as naturalearthSources,
  sources,
} from "./naturalearth";
import {
  layers as openmaptilesLayers,
  sources as openmaptilesSources,
} from "./openmaptiles";
import {
  layers as rdwatchtilesLayers,
  sources as rdwatchtilesSources,
} from "./rdwatchtiles";
import {
  buildSourceFilter as buildSatelliteSourceFilter,
  layers as satelliteLayers,
} from "./satellite-image";
import type { StyleSpecification } from "maplibre-gl";
import { MapFilters } from "../store";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...openmaptilesSources,
    ...rdwatchtilesSources,
    ...buildSatelliteSourceFilter(timestamp, filters)
  },
  sprite: `${tileServerURL}/sprites/osm-liberty`,
  glyphs: `${tileServerURL}/fonts/{fontstack}/{range}.pbf`,
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "rgb(239,239,239)" },
    },
    ...naturalearthLayers,
    ...openmaptilesLayers,
    ...rdwatchtilesLayers(timestamp, filters),
    ...satelliteLayers(timestamp, filters),
  ],
});
