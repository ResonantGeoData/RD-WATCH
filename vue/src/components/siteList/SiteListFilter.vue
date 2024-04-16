<script setup lang="ts">

import { Ref, computed, ref, } from "vue";
import { EnabledSiteObservations, SiteObservationImage, state } from '../../store'

export interface SiteFilterType {
    modelRun: string[];
    imagesDownloaded?: boolean;
}


defineProps<{
    modelValue: SiteFilterType,
}>();

const emit = defineEmits<{
  (e: "update:modelValue", filter: string): void;
}>();


const cloudFilter = computed({
    get() {
      return state.siteObsSatSettings.cloudCoverFilter;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, cloudCoverFilter: val };
    },
  });
  
  const percentBlackFilter = computed({
    get() {
      return state.siteObsSatSettings.percentBlackFilter;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, percentBlackFilter: val };
    },
  });
  
  const imageOpacity = computed({
    get() {
      return state.siteObsSatSettings.imageOpacity;
    },
    set(val: number) {
      state.siteObsSatSettings = { ...state.siteObsSatSettings, imageOpacity: val };
    },
  });
  
  const updateSources = () => {
  const newObservations: EnabledSiteObservations[] = [];
  state.enabledSiteObservations.filter((item) => {
    const tempImages: SiteObservationImage[] = [];
    item.images.forEach((image) => {
      if (!state.siteObsSatSettings.observationSources.includes(image.source)) {
        image.disabled = true;
      } else if (image.disabled) {
        delete image.disabled;
      }
      tempImages.push(image);
    });
    if (tempImages.length) {
      item.images = tempImages;
    }
    newObservations.push(item);
  });
  state.enabledSiteObservations = newObservations;
}

const baseSources: Ref<(SatelliteTypes)[]> = ref(['S2', 'WV', 'L8', 'PL'])

const sources: Ref<(SatelliteTypes)[]> = ref(['S2', 'WV', 'L8', 'PL']);
const updateSatSources = () => {
  state.siteObsSatSettings = {...state.siteObsSatSettings, observationSources: sources.value };
  updateSources();
};
const filterDialog = ref(false);


</script>

<template>
  <v-tooltip>
    <template #activator="{ props }">
      <v-icon
        v-bind="props"
        size="small"
        @click="filterDialog = true"
      >
        mdi-filter
      </v-icon>
    </template>
    <v-container>
      <h3>Filter Settings</h3>
      <v-row
        align="center"
        class="mt-3"
        dense
      >
        <v-col>Sources:</v-col>
        <v-col>
          <v-row align="center">
            <span
              v-for="item in sources"
              :key="item"
              class="mx-1"
            >{{ item }}</span>
          </v-row>
        </v-col>
      </v-row>
      <v-row>
        <v-col>Cloud Cover:</v-col>
        <v-col>{{ cloudFilter }}%</v-col>
      </v-row>
      <v-row>
        <v-col>NoData:</v-col>
        <v-col>{{ percentBlackFilter }}%</v-col>
      </v-row>
      <v-row>
        <v-col>Image Opacity:</v-col>
        <v-col>{{ imageOpacity }}%</v-col>
      </v-row>
    </v-container>
  </v-tooltip>
  <v-dialog
    v-model="filterDialog"
    width="600"
  >
    <v-card>
      <v-row
        dense
        class="pt-2"
      >
        <v-select
          v-model="sources"
          :items="baseSources"
          label="Sources"
          multiple
          density="compact"
          closable-chips
          chips
          class="mx-2"
          width="150"
          @update:model-value="updateSatSources()"
        />
      </v-row>

      <div style="border: 1px solid black; padding:5px">
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-col cols="3">
            <span class="setting-label">Cloud Cover:</span>
          </v-col>
          <v-col cols="7">
            <v-slider
              v-model.number="cloudFilter"
              min="0"
              max="100"
              step="1"
              color="primary"
              density="compact"
              class="mt-5"
            />
          </v-col>
          <v-col>
            <span class="pl-2 setting-label">
              {{ cloudFilter }}%
            </span>
          </v-col>
        </v-row>
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-col cols="3">
            <span class="setting-label">NoData:</span>
          </v-col>
          <v-col cols="7">
            <v-slider
              v-model.number="percentBlackFilter"
              min="0"
              max="100"
              step="1"
              color="primary"
              density="compact"
              class="mt-5"
            />
          </v-col>
          <v-col>
            <span class="pl-2 setting-label">
              {{ percentBlackFilter }}%
            </span>
          </v-col>
        </v-row>
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-col cols="3">
            <span class="setting-label">Image Opacity:</span>
          </v-col>
          <v-col cols="7">
            <v-slider
              v-model.number="imageOpacity"
              min="0"
              max="100"
              step="1"
              color="primary"
              density="compact"
              class="mt-5"
            />
          </v-col>
          <v-col>
            <span class="pl-2 setting-label">
              {{ imageOpacity }}%
            </span>
          </v-col>
        </v-row>
      </div>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.setting-label {
  font-size: 0.85em;
}
</style>