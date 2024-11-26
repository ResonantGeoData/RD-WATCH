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
import { buildIQRClusterLayers, buildIQRImageLayers, buildIQRImageSources, buildIQRSiteVectorLayers, buildIQRSiteVectorSources } from "./iqr";

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
  iqrSessionId: string | null = null,
  randomKey=''
): StyleSpecification => ({
  version: 8,
  sources: {
    ...naturalearthSources,
    ...buildSatelliteSourceFilter(timestamp, satellite),
    ...(iqrResults?.length ? buildIQRImageSources(iqrResults) : {}),
    ...(iqrResults?.length && iqrSessionId ? buildIQRSiteVectorSources(timestamp, iqrSessionId, randomKey) : {}),
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
    ...(iqrResults?.length ? buildIQRImageLayers(iqrResults, settings) : []),
    ...(iqrResults?.length && iqrSessionId ? buildIQRSiteVectorLayers(timestamp, filters, iqrSessionId) : []),
    ...buildImageLayerFilter(timestamp, enabledSiteImages, settings),
    ...rdwatchtilesLayers(timestamp, filters, modelRunIds, regionIds),
    ...localGeoJSONLayers(localGeoJSONFeatures),
    ...(iqrResults?.length ? buildIQRClusterLayers() : []),
  ],
});
