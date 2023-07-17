<script setup lang="ts">
import SideBar from "./components/SideBar.vue";
import MapLibre from "./components/MapLibre.vue";
import RightBar from "./components/RightBar.vue"
</script>

<template>
  <v-app
    id="RGD"
  >
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
    </v-main>
    <RightBar />
  </v-app>
</template>
