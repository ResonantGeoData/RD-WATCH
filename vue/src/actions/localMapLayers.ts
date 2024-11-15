import { state } from "../store";
import { getGeoJSONBounds } from '../utils';
import { FitBoundsEvent } from '../actions/map';

let _id = 1;

function nextId() {
  return _id++;
}

function defaultLayerName(layerId: number) {
  return `Layer ${layerId}`;
}

export function addLocalMapLayer(feature: GeoJSON.GeoJSON): number {
  const id = nextId();
  state.localMapFeatureById[id] = {
    id,
    geojson: feature,
    visible: true,
    name: defaultLayerName(id),
  };
  state.localMapFeatureIds.push(id);

  return id;
}

export function removeLocalMapLayer(id: number) {
  const idx = state.localMapFeatureIds.indexOf(id);
  if (idx === -1) return;

  state.localMapFeatureIds.splice(idx, 1);
  delete state.localMapFeatureById[id];
}

export function focusLayer(layerId: number) {
  const layer = state.localMapFeatureById[layerId];
  if (!layer) return;

  const bounds = getGeoJSONBounds(layer.geojson);
  FitBoundsEvent.trigger(bounds);
}

export function setLayerVisibility(layerId: number, visible: boolean) {
  const layer = state.localMapFeatureById[layerId];
  if (!layer) return;

  state.localMapFeatureById[layerId] = {
    ...layer,
    visible,
  };
}

export function setLayerName(layerId: number, name: string) {
  const layer = state.localMapFeatureById[layerId];
  if (!layer) return;

  state.localMapFeatureById[layerId] = {
    ...layer,
    name: name.trim().length ? name : defaultLayerName(layerId),
  };
}
