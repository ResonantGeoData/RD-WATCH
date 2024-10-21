<script setup lang="ts">
import LayerToggles from './topbar/LayerToggles.vue';
import RegionButton from './topbar/RegionButton.vue';
import SatelliteRegionButton from './topbar/SatelliteRegionButton.vue';
import BaseMapButton from './topbar/BaseMapButton.vue';
import TextButton from './topbar/TextButton.vue';
import PatternsButton from './topbar/PatternsButton.vue';
</script>

<template>
  <v-row
    dense
  >
    <v-row
      class="toolbar-background"
      dense
    >
      <layer-toggles />
      <region-button />
      <base-map-button />
      <satellite-region-button />
      <text-button />
      <patterns-button />
      <v-spacer />
    </v-row>
    <v-spacer />
  </v-row>
</template>

<style scoped>
.toolbar-background {
    border-radius: 6px;
    background-color: #FFFFFFBB;
    padding-top: 10px;
    padding-bottom: 3px;
}
</style>
