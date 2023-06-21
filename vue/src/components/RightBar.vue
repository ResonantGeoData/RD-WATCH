<script setup lang="ts">
import { state } from "../store";
import EvaluationsSideBar from "./siteObservations/EvaluationsSideBar.vue";
import MapLegend from "./MapLegend.vue"


</script>

<template>
  <span>
    <v-navigation-drawer
      v-if="state.selectedObservations.length "
      location="right"
      floating
      width="400"
      sticky
      permanent
      class="fill-height"
      style="overflow-y: hidden;"
    >
      <v-row dense>
        <v-col
          class="navcolumn"
        >
          <EvaluationsSideBar style="flex-grow: 1;" />
          <MapLegend class="mx-auto mt-5" />
        </v-col>
      </v-row>
    </v-navigation-drawer>
    <MapLegend
      v-else
      class="static-map-legend"
    />
  </span>
</template>

<style scoped>

.static-map-legend {
    position: absolute;
    bottom: 0px;
    right: 0px;
    z-index: 2;
}
.navcolumn {
    display: flex;
    flex-flow: column;
    height: 100vh;
}
</style>
