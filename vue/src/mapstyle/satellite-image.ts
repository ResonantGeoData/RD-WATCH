import type { LayerSpecification, SourceSpecification } from "maplibre-gl";
import type { MapFilters } from "../store";

const urlRoot = `${location.protocol}//${location.host}`;
const satelliteImages = "satelliteTiles";
export const buildSourceFilter = (
    timestamp: number,
    filters: MapFilters
) => {
    if (!filters.satelliteImagesOn) {
         return undefined;
    }
    let timeStamp = '0';
    if (filters && filters.satelliteTimeList && filters.satelliteTimeList.length > 0) {
        const list = filters.satelliteTimeList.map((item) => new Date(item));
        const base = new Date(timestamp * 1000)
        list.sort((a,b) => {
            const distanceA = Math.abs(base.valueOf() - a.valueOf());
            const distanceB = Math.abs(base.valueOf() - b.valueOf());
            return distanceA - distanceB;
        })
        timeStamp = list[0].toISOString().substring(0,19);
        console.log(timeStamp);
    }
    const constellation = "S2";
    const spectrum="visual";
    const source: SourceSpecification = {
        type: "raster",
        tiles: [`${urlRoot}/api/satellite-image/tile/{z}/{x}/{y}.webp?constellation=${constellation}&timestamp=${timeStamp}&spectrum=${spectrum}&level=2A`],
        minzoom: 0,
        maxzoom: 14,
      };
    return {satelliteTiles : source}
}
  
export const layers = (
    timestamp: number,
    filters: MapFilters
  ): LayerSpecification[] => {
    if (!filters.satelliteImagesOn) {
         return [];
    }
    const layers: LayerSpecification[] = [
    {
        id: "satelliteimages",
        type: "raster",
        source: satelliteImages,
        paint: {
            "raster-opacity":filters.imageOpacity,
          },
      
    },
];
return layers;
  }