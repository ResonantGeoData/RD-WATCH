import type { LayerSpecification, SourceSpecification } from "maplibre-gl";
import type { MapFilters, SatelliteData } from "../store";

const urlRoot = `${location.protocol}//${location.host}`;
const satelliteImages = "satelliteTiles";
export const buildSourceFilter = (
    timestamp: number,
    satellite: SatelliteData
) => {
    if (!satellite.satelliteImagesOn) {
         return undefined;
    }
    const constellation = "S2";
    const spectrum="visual";
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    satellite.satelliteBounds.forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })

    const bbox : [number, number, number, number]= [minY, minX, maxY, maxX];
    if (bbox.filter((item) => item === Infinity || item === -Infinity).length) {
      console.error(`Filter for current has infinite bounding box`);
    } else {
    const timeStamp = satellite.satelliteTimeStamp;
      if (timeStamp !== '') {
        const source: SourceSpecification = {
            type: "raster",
            tiles: [`${urlRoot}/api/satellite-image/tile/{z}/{x}/{y}.webp?constellation=${constellation}&timestamp=${timeStamp}&spectrum=${spectrum}&level=2A`],
            minzoom: 0,
            maxzoom: 14,
            bounds: bbox,

          };
        return {satelliteTiles : source}
      }
    }
    return undefined;
}
  
export const layers = (
    timestamp: number,
    satellite: SatelliteData
  ): LayerSpecification[] => {
    if (!satellite.satelliteImagesOn) {
         return [];
    }
    const layers: LayerSpecification[] = [
      {
          id: "satelliteimages",
          type: "raster",
          source: satelliteImages,
          paint: {
              "raster-opacity":satellite.imageOpacity,
              "raster-fade-duration": 0,
            },      
      },  
    ];
    return layers;
  }

export const setSatelliteTimeStamp = (state: { filters: MapFilters, satellite: SatelliteData, timestamp: number}) => {
  if (state.filters && state.satellite.satelliteTimeList && state.satellite.satelliteTimeList.length > 0) {
    const list = state.satellite.satelliteTimeList.map((item) => new Date(`${item}Z`));
    const base = new Date(state.timestamp * 1000);
    const filtered = list.filter((item) => item.valueOf() <= base.valueOf());
    let baseList = filtered;
    if (filtered.length === 0) {
      baseList = list;
    }
    baseList.sort((a,b) => {
        const distanceA = Math.abs(base.valueOf() - a.valueOf());
        const distanceB = Math.abs(base.valueOf() - b.valueOf());
        return distanceA - distanceB;
    })
    // Lets try to get the closes timestamp that is less than the current time.
    const date = baseList[0];
    const timeStamp = date.toISOString().substring(0,19);
    state.satellite.satelliteTimeStamp = timeStamp;
}
}