<script setup lang="ts">
import { map } from "./map";
import { LngLatBounds } from "maplibre-gl";

setTimeout(() => {
  map.fitBounds(LngLatBounds.convert([80, 32, 90, 55]), {
    animate: true,
    essential: true,
  });
}, 2000);

setTimeout(() => {
  map.fitBounds(LngLatBounds.convert([80, -55, 90, -32]), {
    animate: true,
    essential: true,
  });
}, 5000);
</script>

<template>
  <div class="fixed h-screen w-80 pl-2 pt-2 pb-2">
    <div class="h-full w-full rounded-xl bg-white drop-shadow-2xl"></div>
  </div>
</template>
