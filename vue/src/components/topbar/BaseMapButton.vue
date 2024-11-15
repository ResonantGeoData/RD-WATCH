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
        :variant="drawMap ? undefined : 'text'"
        :color="drawMap ? 'primary' : ''"
        @click="drawMap = !drawMap"
      >
        <v-icon
          :color="drawMap ? 'white': ''"
          size="x-large"
        >
          mdi-road
        </v-icon>
      </v-btn>
    </template>
    <span>Toggle On/Off BaseMap</span>
  </v-tooltip>
</template>
