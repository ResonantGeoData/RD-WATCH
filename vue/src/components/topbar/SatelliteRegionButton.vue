<script setup lang="ts">
import { Ref, computed, ref, watch } from 'vue';
import { ApiService, ModelRunList, Region } from '../../client';
import { filteredSatelliteTimeList, state } from '../../store';
const selectedRegion: Ref<Region | undefined> = ref(undefined);

const currentModelRunList: Ref<ModelRunList | null> = ref(state.modelRunList || null);
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
  console.log(currentModelRunList.value);
  if (currentModelRunList.value) {
    getSatelliteTimestamps(currentModelRunList.value);
  }
}
watch(() => state.modelRunList, () => {
    if (state.modelRunList) {
        currentModelRunList.value = state.modelRunList;
    }
});
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

const imagesOn = computed({
  get() {
    return state.satellite.satelliteImagesOn || false;
  },
  set(val: boolean) {
    state.satellite = { ...state.satellite, satelliteImagesOn: val };
  },
});

const imageOpacity = computed({
  get() {
    return state.satellite.imageOpacity || 0;
  },
  set(val: number) {
    state.satellite = { ...state.satellite, imageOpacity: val };
  },
});

const cloudCover = computed({
  get() {
    return state.satellite.cloudCover || 1000;
  },
  set(val: number) {
    state.satellite = { ...state.satellite, cloudCover: val };
  },
});


const S2Imagery = computed({
  get() {
    return state.satellite.satelliteSources.includes('S2');
  },
  set(val: boolean) {
    if (!state.satellite.satelliteSources.includes('S2') && val) {
      state.satellite.satelliteSources.push('S2')
    } else if (state.satellite.satelliteSources.includes('S2')) {
      const index = state.satellite.satelliteSources.indexOf('S2');
      state.satellite.satelliteSources.splice(index, 1);
    }
  },
});



const worldViewImagery = computed({
  get() {
    return state.satellite.satelliteSources.includes('WorldView');
  },
  set(val: boolean) {
    if (!state.satellite.satelliteSources.includes('WorldView') && val) {
      state.satellite.satelliteSources.push('WorldView')
    } else if (state.satellite.satelliteSources.includes('WorldView')) {
      const index = state.satellite.satelliteSources.indexOf('WorldView');
      state.satellite.satelliteSources.splice(index, 1);
    }
  },
});

const satelliteImageState = computed(() => (selectedRegion.value !== null && !(filteredSatelliteTimeList.value.length === 0 && state.satellite.satelliteSources.length !== 0)))

</script>



<template>
  <v-menu
    v-if="satelliteImageState"
    open-on-hover
    width="400"
  >
    <template #activator="{ props }">
      <v-btn
        v-bind="props"
        class="px-2 mx-2"
        :class="{
          'animate-flicker': state.satellite.loadingSatelliteImages,
        }"
        :color="imagesOn ? 'primary' : ''"
        :disabled="selectedRegion === null || (filteredSatelliteTimeList.length === 0 && state.satellite.satelliteSources.length !== 0)"
        @click="imagesOn = selectedRegion !== null && (filteredSatelliteTimeList.length !== 0 || state.satellite.satelliteSources.length === 0) ? !imagesOn : imagesOn"
      >
        <v-icon
          color="imagesOn ? 'white' : 'black'"
          size="x-large"
        >
          mdi-image
        </v-icon>
        <v-icon
          :color="imagesOn ? 'white' : 'black'"
          size="large"
        >
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card outlined>
      <v-card-title>Satellite Imagery</v-card-title>
      <v-card-text>
        <v-row dense>
          <v-checkbox label="Show Satellite image timestamps" />
        </v-row>
        <v-row dense>
          <v-divider />
        </v-row>
        <v-row dense>
          <h3>Source</h3>
        </v-row>
        <v-row dense>
          <v-radio v-model="S2Imagery">
            <template #label>
              <span>S2 Imagery</span> <span
                style="color:gray"
                class="pl-2"
              > (default)</span>
            </template>
          </v-radio>
        </v-row>
        <v-row dense>
          <span style="color:gray">Sentinel-2 Imagery from Element 84</span>
        </v-row>
        <v-row dense>
          <v-radio
            v-model="worldViewImagery"
            label="World View Imagery"
          />
        </v-row>
        <v-row dense>
          <span style="color:gray">WorldView Imagery from SMART STAC Server</span>
        </v-row>
        <v-row>
          <v-divider />
        </v-row>
        <v-row
          dense
          align="center"
          justify="center"
        >
          <v-col cols="4">
            <span>Image Opacity:</span>
          </v-col>
          <v-col cols="6">
            <v-slider
              v-model.number="imageOpacity"
              min="0"
              max="1"
              step="0.1"
              color="primary"
              density="compact"
              class="mt-5"
            />
          </v-col>
          <v-col cols="2">
            <span class="">{{ (imageOpacity * 100).toFixed(0) }}%</span>
          </v-col>
        </v-row>
        <v-row
          dense
          align="center"
          justify="center"
        >
          <v-col>
            <span class="label">Cloud Cover:</span>
          </v-col>
          <v-col cols="6">
            <v-slider
              v-model.number="cloudCover"
              :disabled="state.satellite.loadingSatelliteImages"
              min="0"
              max="100"
              step="20"
              color="primary"
              density="compact"
              class="mt-5"
            />
          </v-col>
          <v-col cols="2">
            <span class="label">&lt;{{ cloudCover }}%</span>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-menu>
  <v-tooltip
    v-else
    location="bottom"
  >
    <template #activator="{ props: props }">
      <v-btn
        class="px-2 mx-2"
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