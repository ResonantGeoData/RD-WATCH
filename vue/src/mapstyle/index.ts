import {
  layers as naturalearthLayers,
  sources as naturalearthSources,
} from "./naturalearth";
import {
  layers as openmaptilesLayers,
  sources as openmaptilesSources,
} from "./openmaptiles";
import {
  buildSourceFilter as buildRdwatchtilesSources,
  buildLayerFilter as rdwatchtilesLayers,
} from "./rdwatchtiles";
import {
  buildSourceFilter as buildSatelliteSourceFilter,
  layers as satelliteLayers,
} from "./satellite-image";
import type { StyleSpecification } from "maplibre-gl";
import { EnabledSiteObservations,  MapFilters, SatelliteData, siteObsSatSettings } from "../store";
import { buildImageLayerFilter, buildImageSourceFilter } from "./images";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters,
  satellite: SatelliteData,
  enabledSiteObservations: EnabledSiteObservations[],
  settings: siteObsSatSettings,
  modelRunIds: string[],
  randomKey=''
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...openmaptilesSources(filters),
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...buildImageSourceFilter(timestamp, enabledSiteObservations, settings),
    ...buildRdwatchtilesSources(modelRunIds, randomKey),
  },
  sprite: `${tileServerURL}/sprites/osm-liberty`,
  glyphs: `${tileServerURL}/fonts/{fontstack}/{range}.pbf`,
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "rgb(220,220,220)" },
    },
    ...naturalearthLayers,
    ...openmaptilesLayers(filters),
    ...satelliteLayers(timestamp, satellite),
    ...buildImageLayerFilter(timestamp, enabledSiteObservations, settings),
    ...rdwatchtilesLayers(timestamp, filters, modelRunIds),
  ],
});
