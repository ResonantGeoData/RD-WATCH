<script setup lang="ts">

import { state } from '../../store'
import { computed } from "vue";

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

  const singleSelect = computed({
    get() {
      return state.selectionSettings.singleSelect;
    },
    set(val: boolean) {
      let openDetailVal = val && state.selectionSettings.openDetails;
      if (!val) {
        openDetailVal = false;
      }
      state.selectionSettings = { ...state.selectionSettings, singleSelect: val, openDetails: openDetailVal };
    },
  });

  const openDetails = computed({
    get() {
      return state.selectionSettings.openDetails;
    },
    set(val: boolean) {
      state.selectionSettings = { ...state.selectionSettings, openDetails: val };
    },
  });

</script>

<template>
  <v-expansion-panels
    variant="accordion"
    class="pa-0 ma-0 mb-2"
  >
    <v-expansion-panel key="Selection">
      <v-expansion-panel-title>Selection Settings</v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-checkbox
            v-model="singleSelect"
            density="compact"
            label="Single Selection"
            class="pa-0 ma-0"
          />
        </v-row>
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-checkbox
            v-model="openDetails"
            :disabled="!singleSelect"
            density="compact"
            label="Open Details on Select"
          />
        </v-row>
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel key="Images">
      <v-expansion-panel-title>Image Settings</v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-row
          dense
          justify="center"
          align="center"
        >
          <v-col cols="3">
            <span class="setting-label">Cloud Cover:</span>
          </v-col>
          <v-col cols="6">
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
          <v-col cols="6">
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
          <v-col cols="6">
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
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<style scoped>
.setting-label {
  font-size: 0.85em;
}
</style>