<script setup lang="ts">
import { Ref, computed, ref, watch } from 'vue';
import { ApiService, ModelRunList, Region } from '../../client';
import { filteredSatelliteTimeList, state } from '../../store';
const selectedRegion: Ref<Region | undefined> = ref(undefined);

const currentModelRunList: Ref<ModelRunList | null> = ref(null);
const satelliteRegionTooLarge = ref(false);
const loadingSatelliteTimestamps = ref(false);
const askDownloadSatelliteTimestamps = ref(false);
async function getSatelliteTimestamps(modelRun: ModelRunList, force=false) {
  satelliteRegionTooLarge.value = false;
  loadingSatelliteTimestamps.value = true;
  state.satellite.satelliteTimeList = [];
  const bbox = modelRun.bbox?.coordinates[0];
  if (bbox && !force) {
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    (bbox as []).forEach((item: [number, number]) => {
      minX = Math.min(minX, item[1]);
      minY = Math.min(minY, item[0]);
      maxX = Math.max(maxX, item[1]);
      maxY = Math.max(maxY, item[0]);
    })
    const xSize = maxX - minX;
    const ySize = maxY - minY;
    if (xSize > 1 || ySize > 1) {
      loadingSatelliteTimestamps.value = false;
      satelliteRegionTooLarge.value = true;
      return;
    }
  }
  const results = await ApiService.getAllSatelliteTimestamps(
      'S2', 'visual','2A', modelRun.timerange?.min, modelRun.timerange?.max, modelRun.bbox?.coordinates[0] as []);

  loadingSatelliteTimestamps.value = false;
  state.satellite.satelliteTimeList = results;
  state.satellite.satelliteBounds = modelRun.bbox?.coordinates[0] as [];
}

const startLoadingSatelliteTimeStamps = async () => {
  askDownloadSatelliteTimestamps.value = false;
  if (currentModelRunList.value) {
    getSatelliteTimestamps(currentModelRunList.value);
  }
}

const satelliteLoadingColor = computed(() => {
  if (satelliteRegionTooLarge.value) {
    return 'warning'
  }
  if (loadingSatelliteTimestamps.value) {
    return 'primary';
  }
  return ''
})

watch (() => state.filters.regions, () => {
  if (state.filters.regions?.length) {
    selectedRegion.value = state.filters.regions[0];
  }
});

watch(selectedRegion, () => {
  // Reset satellite time list when on other regions
  satelliteRegionTooLarge.value = false;
  state.satellite = { ...state.satellite, satelliteImagesOn: false, satelliteTimeList: []};
  state.filters = { ...state.filters, regions: selectedRegion.value ? [selectedRegion.value] : undefined };
});

const expandSettings = ref(false);

const imagesOn = computed({
  get() {
    return state.satellite.satelliteImagesOn || false;
  },
  set(val: boolean) {
    state.satellite = { ...state.satellite, satelliteImagesOn: val };
  },
});

</script>



<template>
  <v-btn
    v-if="selectedRegion !== null && !(filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
    class="px-2 mx-2"
    size="large"
    :class="{
      'animate-flicker': state.satellite.loadingSatelliteImages,
    }"
    :color="imagesOn ? 'primary' : ''"
    :disabled="selectedRegion === null || (filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
    @click="imagesOn = selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0) ? !imagesOn : imagesOn"
  >
    <v-icon>mdi-image</v-icon>
  </v-btn>
  <v-tooltip v-else>
    <template #activator="{ props: props }">
      <v-btn
        class="px-2 mx-2"
        size="large"
        v-bind="props"
        :disabled="!selectedRegion"
        :class="{
          'animate-flicker': loadingSatelliteTimestamps,
        }"
        :color="satelliteLoadingColor"
        @click="askDownloadSatelliteTimestamps = true"
      >
        <v-icon>mdi-satellite-variant</v-icon>
      </v-btn>
    </template>
    <v-alert
      v-if="!satelliteRegionTooLarge"
      type="warning"
      title="Download Region Satellite Timestamps"
      text="This is a long running process that could cause instability on the server.  Please only run this if you are sure you need to use the region satellite feature."
    />
    <v-alert
      v-else
      type="warning"
      title="Region Too Large to Download Timestamps"
      text="The Region is too large to download timestamps for."
    />
  </v-tooltip>
  <v-dialog
    v-model="askDownloadSatelliteTimestamps"
    width="600"
  >
    <v-card>
      <v-card-title>Download Satellite Timestamps</v-card-title>
      <v-card-text>
        <v-alert type="warning">
          Downloading satellite timestamps can cause the server to become unstable.  Only use this feature if you need to view full region satellite images and realize that usage will impact other users on the server.
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-row>
          <v-spacer />
          <v-btn
            color="error"
            class="mx-2"
            variant="tonal"
            @click="askDownloadSatelliteTimestamps = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="warning"
            class="mx-2"
            variant="tonal"
            @click="startLoadingSatelliteTimeStamps()"
          >
            Download
          </v-btn>
        </v-row>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>