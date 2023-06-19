<script setup lang="ts">
import SideBar from "./components/SideBar.vue";
import MapLibre from "./components/MapLibre.vue";
import EvaluationsSideBar from "./components/siteObservations/EvaluationsSideBar.vue";
import Legend from "./components/Legend.vue"
import { state } from './store';
</script>

<template>
  <v-app id="RGD">
    <v-navigation-drawer
      location="left"
      width="400"
      sticky
      style="max-height:100vh;"
      permanent
    >
      <SideBar />
    </v-navigation-drawer>
    <v-main style="z-index:1">
      <MapLibre />
      <v-row v-if="state.mapLegend">
        <v-card>
          <v-card-title>Legend</v-card-title>
          <v-card-text>
            <Legend />
          </v-card-text>
        </v-card>
      </v-row>
    </v-main>
    <v-navigation-drawer
      location="right"
      width="400"
      sticky
      permanent
    >
      <EvaluationsSideBar />
    </v-navigation-drawer>
  </v-app>
</template>

<style scoped>
</style>
