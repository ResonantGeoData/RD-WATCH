import { state } from "../store";
import { getGeoJSONBounds } from "../utils";
import { FitBoundsEvent } from "./map";

let id = 1;

function nextId() {
  return id++;
}

export function addLocalMapLayer(feature: GeoJSON.GeoJSON): number {
  const id = nextId();
  state.localMapFeatureById[id] = {
    id,
    geojson: feature,
  };
  state.localMapFeatureIds.push(id);

  FitBoundsEvent.trigger(getGeoJSONBounds(feature));

  return id;
}

export function removeLocalMapLayer(id: number) {
  const idx = state.localMapFeatureIds.indexOf(id);
  if (idx === -1) return;

  state.localMapFeatureIds.splice(idx, 1);
  delete state.localMapFeatureById[id];
}

