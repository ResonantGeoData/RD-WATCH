<script setup lang="ts">
import { computed,} from "vue";
import { state } from "../../store";



const drawMap = computed({
  get() {
    return state.filters.drawMap || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, drawMap: val };
  },
});

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
