import {  Map, MapDataEvent } from "maplibre-gl";
import { ShallowRef, watch } from "vue";
import { state } from "../store";


const satelliteTilesUIDs: Record<string, string> = {};
type MapDataLoad = MapDataEvent & { sourceId?: string, tile? : { uid?: number}}

const satelliteLoading = (map: ShallowRef<null | Map>) => {
    watch([() => state.satellite.satelliteTimeStamp, () => state.satellite.satelliteImagesOn], () => {
        state.satellite.loadingSatelliteImages = false;
        Object.keys(satelliteTilesUIDs).forEach((key) => delete satelliteTilesUIDs[key]);
    });
    if (map.value) {
        map.value.on("data", function (e: MapDataLoad) {
            if (e.sourceId === 'satelliteTiles') {
                if (e?.tile?.uid) {
                if (satelliteTilesUIDs[e.tile.uid])
                delete satelliteTilesUIDs[e.tile.uid];
                }
                if (Object.values(satelliteTilesUIDs).length === 0) {
                state.satellite.loadingSatelliteImages = false;
                } else {
                    state.satellite.loadingSatelliteImages = true;
                }
            }
        });
        map.value.on("dataloading", function (e: MapDataLoad) {
            if (e.sourceId === 'satelliteTiles') {
                if (e?.tile?.uid) {
                satelliteTilesUIDs[e.tile.uid] = 'loading';
                state.satellite.loadingSatelliteImages = true;
                }
            }
        });
    }
};

export { satelliteLoading };
