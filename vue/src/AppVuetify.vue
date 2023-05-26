<script setup lang="ts">
import SideBar from "./componentsVuetify/SideBar.vue";
import MapLibre from "./componentsVuetify/MapLibre.vue";
import EvaluationsSideBar from "./componentsVuetify/siteObservations/EvaluationsSideBar.vue";

</script>

<template>
  <v-app id="RGD">
    <v-navigation-drawer
      location="left"
      width="400"
      sticky
      style="max-height:100vh;"
    >
      <SideBar />
    </v-navigation-drawer>
    <v-main style="z-index:1">
      <MapLibre />
    </v-main>
    <v-navigation-drawer
      location="right"
      width="400"
      sticky
    >
      <EvaluationsSideBar />
    </v-navigation-drawer>
  </v-app>
</template>
