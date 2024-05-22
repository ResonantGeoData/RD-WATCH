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
import { EnabledSiteOverviews,  MapFilters, SatelliteData, siteOverviewSatSettings } from "../store";
import { buildImageLayerFilter, buildImageSourceFilter } from "./images";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters,
  satellite: SatelliteData,
  enabledSiteImages: EnabledSiteOverviews[],
  settings: siteOverviewSatSettings,
  modelRunIds: string[],
  randomKey=''
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...buildImageSourceFilter(timestamp, enabledSiteImages, settings),
    ...buildRdwatchtilesSources(timestamp, modelRunIds, randomKey),
    ...openmaptilesSources(filters),
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
    ...buildImageLayerFilter(timestamp, enabledSiteImages, settings),
    ...rdwatchtilesLayers(timestamp, filters, modelRunIds),
  ],
});
