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
          },
      
    },
];
return layers;
  }