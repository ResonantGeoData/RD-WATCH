<script setup lang="ts">
import SideBar from "./components/SideBar.vue";
import MapLibre from "./components/MapLibre.vue";
import ObservationSideBar from "./components/siteObservations/ObservationSideBar.vue";
</script>

<template>
  <SideBar />
  <observation-side-bar />
  <MapLibre />
</template>
