import {
  layers as naturalearthLayers,
  sources as naturalearthSources,
} from "./naturalearth";
import {
  layers as openmaptilesLayers,
  sources as openmaptilesSources,
} from "./openmaptiles";
import {
  layers as rdwatchtilesLayers,
  sources as rdwatchtilesSources,
} from "./rdwatchtiles";
import type { StyleSpecification } from "maplibre-gl";

export const style = (
  timestamp: number,
  filters: Record<string, number>
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...openmaptilesSources,
    ...rdwatchtilesSources,
  },
  sprite: "https://tiles.mcovalt.com/sprites/osm-liberty",
  glyphs: "https://tiles.mcovalt.com/fonts/{fontstack}/{range}.pbf",
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "rgb(239,239,239)" },
    },
    ...naturalearthLayers,
    ...openmaptilesLayers,
    ...rdwatchtilesLayers(timestamp, filters),
  ],
});
