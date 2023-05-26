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
  
</script>

<template>
  <div style="border: 1px solid black; padding:5px">
    <v-row
      dense
      justify="center"
      align="center"
    >
      <v-col cols="3">
        <span>Cloud Cover:</span>
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
        <span class="pl-2">
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
        <span>NoData:</span>
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
        <span class="pl-2">
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
        <span>Image Opacity:</span>
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
        <span class="pl-2">
          {{ percentBlackFilter }}%
        </span>
      </v-col>
    </v-row>
  </div>
</template>