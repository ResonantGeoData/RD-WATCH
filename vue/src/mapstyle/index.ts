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
import { EnabledSiteObservations, KeyedModelRun, MapFilters, SatelliteData, siteObsSatSettings } from "../store";
import { buildImageLayerFilter, buildImageSourceFilter } from "./images";
import { Map } from "maplibre-gl";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters,
  satellite: SatelliteData,
  enabledSiteObservations: EnabledSiteObservations[],
  settings: siteObsSatSettings,
  modelRunIds: number[],
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...openmaptilesSources,
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...buildImageSourceFilter(timestamp, enabledSiteObservations, settings),
    ...buildRdwatchtilesSources(modelRunIds),
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
    ...buildImageLayerFilter(timestamp, enabledSiteObservations, settings),
    ...rdwatchtilesLayers(timestamp, filters, modelRunIds),
  ],
});
