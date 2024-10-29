<script setup lang="ts">
import LayerToggles from './topbar/LayerToggles.vue';
import RegionButton from './topbar/RegionButton.vue';
import SatelliteRegionButton from './topbar/SatelliteRegionButton.vue';
import BaseMapButton from './topbar/BaseMapButton.vue';
import TextButton from './topbar/TextButton.vue';
import PatternsButton from './topbar/PatternsButton.vue';
import LegendButton from './topbar/LegendButton.vue';
import MapLegend from './MapLegend.vue';
</script>

<template>
  <v-row
    dense
    class="flex-nowrap"
  >
    <v-spacer />
    <v-col cols="auto">
      <v-row
        class="toolbar-background d-flex"
        dense
      >
        <layer-toggles />
        <region-button />
        <base-map-button />
        <satellite-region-button />
        <text-button />
        <patterns-button />
        <legend-button />
        <v-spacer />
      </v-row>
    </v-col>
    <v-col cols="auto">
      <MapLegend class="static-map-legend" />
    </v-col>
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
