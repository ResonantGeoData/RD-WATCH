<script setup lang="ts">
import { state } from "../../store";

</script>

<template>
  <v-tooltip
    location="bottom"
  >
    <template #activator="{ props: props }">
      <v-btn
        v-bind="props"
        class="px-2 mx-2"
        :variant="state.mapLegend ? undefined : 'text'"
        :color="state.mapLegend ? 'primary' : ''"
        @click="state.mapLegend = !state.mapLegend"
      >
        <v-icon
          :color="state.mapLegend ? 'white': ''"
          size="x-large"
        >
          mdi-map-legend
        </v-icon>
      </v-btn>
    </template>
    <span>Toggle On/Off Legend</span>
  </v-tooltip>
</template>
