<script setup lang="ts">
import { computed } from 'vue';
import { addLocalMapLayer, removeLocalMapLayer } from '../actions/localMapLayers';
import { state } from '../store';
import { getGeoJSONBounds } from '../utils';
import { FitBoundsEvent } from '../actions/map';

async function loadFiles(files: File[]) {
  await Promise.all(files.map(async (file) => {
    const data = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function() {
        resolve(reader.result as string);
      };
      reader.onerror = reject;
      reader.readAsText(file, 'utf-8');
    });
    addLocalMapLayer(JSON.parse(data));
  }));
}

async function promptForGeoJSONs() {
  const files = await new Promise<File[]>((resolve) => {
    const fileEl = document.createElement('input');
    fileEl.setAttribute('type', 'file');
    fileEl.setAttribute('multiple', 'multiple');
    fileEl.setAttribute('accept', '.geojson');
    fileEl.addEventListener('change', () => {
      const files = Array.from(fileEl.files ?? []);
      resolve(files);
    });
    fileEl.click();
  });

  await loadFiles(files);
}

function deleteLayer(layerId: number) {
  removeLocalMapLayer(layerId);
}

function focusLayer(layerId: number) {
  const layer = state.localMapFeatureById[layerId];
  if (!layer) return;

  const bounds = getGeoJSONBounds(layer.geojson);
  FitBoundsEvent.trigger(bounds);
}

const localLayers = computed(() => {
  return state.localMapFeatureIds.map(
    (id) => state.localMapFeatureById[id],
  );
})

</script>

<template>
  <div>
    <div class="text-center">
      <v-btn
        variant="flat"
        color="secondary"
        @click="promptForGeoJSONs"
      >
        <template #prepend>
          <v-icon>mdi-plus</v-icon>
        </template>
        Add local .geojson file
      </v-btn>
      <div
        v-if="!localLayers.length"
        class="mt-8 text-grey-darken-2"
      >
        No local layers
      </div>
    </div>
    <v-list>
      <v-list-item
        v-for="layer in localLayers"
        :key="layer.id"
        :title="`Layer ${layer.id}`"
      >
        <template #append>
          <v-btn
            color="grey-darken-1"
            icon
            variant="text"
            @click="focusLayer(layer.id)"
          >
            <v-icon>mdi-target</v-icon>
            <v-tooltip
              activator="parent"
              location="bottom"
            >
              Focus
            </v-tooltip>
          </v-btn>
          <v-btn
            color="grey-darken-1"
            icon
            variant="text"
            @click="deleteLayer(layer.id)"
          >
            <v-icon>mdi-delete</v-icon>
            <v-tooltip
              activator="parent"
              location="bottom"
            >
              Delete
            </v-tooltip>
          </v-btn>
        </template>
      </v-list-item>
    </v-list>
  </div>
</template>
