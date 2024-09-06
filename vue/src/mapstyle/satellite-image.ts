import type { LayerSpecification, SourceSpecification } from "maplibre-gl";
import type { MapFilters, SatelliteData, SatelliteTimeStamp } from "../store";

const urlRoot = `${location.protocol}//${location.host}`;
const satelliteImages = "satelliteTiles";
export const buildSourceFilter = (
    timestamp: number,
    satellite: SatelliteData
) => {
    if (!satellite.satelliteImagesOn || satellite.satelliteSources.length === 0) {
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
    const tileSource = satellite.satelliteTimeSource;
    let sourceEndpoint = 'tile';
    if (tileSource === 'WorldView') {
      sourceEndpoint = 'visual-tile';
    }
    if (timeStamp !== '') {
        let tiles = `${urlRoot}/api/satellite-image/${sourceEndpoint}/{z}/{x}/{y}.webp?timestamp=${timeStamp}`;
        if ( tileSource === 'S2') {
          tiles = `${tiles}&constellation=${constellation}&spectrum=${spectrum}&level=2A`
        }
        const source: SourceSpecification = {
            type: "raster",
            tiles: [tiles],
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
    if (!satellite.satelliteImagesOn || satellite.satelliteSources.length === 0) {
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

export const setSatelliteTimeStamp = (state: { filters: MapFilters, satellite: SatelliteData, timestamp: number}, filteredTimeList: SatelliteTimeStamp[]) => {
  if (state.filters && filteredTimeList && filteredTimeList.length > 0) {
    const list = filteredTimeList.map((item) => new Date(`${item.timestamp}Z`));
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
    // Try each date in the list until one works.
    for (const date of baseList) {
      const timeStamp = date.toISOString().substring(0, 19);
      const currentIndex = state.satellite.satelliteTimeList.findIndex((item) => item.timestamp.substring(0, 19) === timeStamp);
      if (currentIndex === -1) {
        continue;
      }
      state.satellite.satelliteTimeSource = state.satellite.satelliteTimeList[currentIndex].source;
      state.satellite.satelliteTimeStamp = timeStamp;
      break;
    }
  }
}
