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
import {
  buildSourceFilter as buildSatelliteSourceFilter,
  layers as satelliteLayers,
} from "./satellite-image";
import type { StyleSpecification } from "maplibre-gl";
import { EnabledSiteObservations, MapFilters, SatelliteData } from "../store";
import { buildImageLayerFilter, buildImageSourceFilter } from "./images";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters,
  satellite: SatelliteData,
  enabledSiteObservations: EnabledSiteObservations[],
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...openmaptilesSources,
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...buildImageSourceFilter(timestamp, enabledSiteObservations),
    ...rdwatchtilesSources,
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
    ...satelliteLayers(timestamp, satellite),
    ...buildImageLayerFilter(timestamp, enabledSiteObservations),
    ...rdwatchtilesLayers(timestamp, filters),
  ],
});
