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
import { EnabledSiteOverviews, type LocalGeoJSONFeature, MapFilters, SatelliteData, siteOverviewSatSettings } from "../store";
import { buildImageLayerFilter, buildImageSourceFilter } from "./images";
import { localGeoJSONLayers, localGeoJSONSources } from "./localgeojson";
import { IQROrderedResultItem } from "../client/services/ApiService";
import { buildIQRImageLayers, buildIQRImageSources } from "./iqr";

const tileServerURL =
  import.meta.env.VITE_TILE_SERVER_URL || "https://basemap.kitware.watch";
export const style = (
  timestamp: number,
  filters: MapFilters,
  satellite: SatelliteData,
  enabledSiteImages: EnabledSiteOverviews[],
  settings: siteOverviewSatSettings,
  modelRunIds: string[],
  regionIds: number[],
  localGeoJSONFeatures: LocalGeoJSONFeature[],
  iqrResults: IQROrderedResultItem[] | null = null,
  randomKey=''
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...(iqrResults ? buildIQRImageSources(iqrResults) : {}),
    ...buildImageSourceFilter(timestamp, enabledSiteImages, settings),
    ...buildRdwatchtilesSources(timestamp, modelRunIds, regionIds, randomKey),
    ...openmaptilesSources(filters),
    ...localGeoJSONSources(localGeoJSONFeatures),
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
    ...(iqrResults ? buildIQRImageLayers(iqrResults, settings) : []),
    ...buildImageLayerFilter(timestamp, enabledSiteImages, settings),
    ...rdwatchtilesLayers(timestamp, filters, modelRunIds, regionIds),
    ...localGeoJSONLayers(localGeoJSONFeatures),
  ],
});
