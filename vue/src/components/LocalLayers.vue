<script setup lang="ts">
import { computed, ref } from 'vue';
import { addLocalMapLayer, focusLayer, removeLocalMapLayer, setLayerName, setLayerVisibility } from '../actions/localMapLayers';
import { state } from '../store';

const isLoading = ref(false);

async function loadFiles(files: File[]) {
  const promise = Promise.all(files.map(async (file) => {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function() {
        resolve(reader.result as string);
      };
      reader.onerror = reject;
      reader.readAsText(file, 'utf-8');
    });
  }));

  isLoading.value = true;
  promise.finally(() => {
    isLoading.value = false;
  });

  const geoJsons = await promise;

  geoJsons.forEach((data) => {
    addLocalMapLayer(JSON.parse(data));
  });
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

const localLayers = computed(() => {
  return state.localMapFeatureIds.map(
    (id) => state.localMapFeatureById[id],
  );
})

</script>

<template>
  <div class="h-100 overflow-y-auto d-flex flex-column">
    <div class="text-center py-2">
      <v-btn
        variant="flat"
        color="secondary"
        :disabled="isLoading"
        :loading="isLoading"
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
    <v-list class="overflow-y-auto">
      <v-list-item
        v-for="layer in localLayers"
        :key="layer.id"
      >
        <v-text-field
          variant="underlined"
          :placeholder="`Layer ${layer.id}`"
          :model-value="layer.name"
          @model-value:update="setLayerName(layer.id, $event)"
        />
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
            @click="setLayerVisibility(layer.id, !layer.visible)"
          >
            <v-icon>{{ layer.visible ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon>
            <v-tooltip
              activator="parent"
              location="bottom"
            >
              Toggle Visibility
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
