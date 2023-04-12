<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { state } from '../../store'
import SiteObservationDisplay from "./SiteObservationDisplay.vue";
import type { Ref } from "vue";
import { hoveredInfo } from "../../interactions/popup";


</script>

<template>
  <div
    v-if="state.selectedObservations.length"
    class="fixed h-screen w-200 pt-2 pb-2 pr-2 absolute inset-y-0 right-0"
  >
    <div
      class="flex h-full flex-col overflow-hidden rounded-xl bg-white drop-shadow-2xl"
    >
      <h2>List of selected site observations</h2>
      <site-observation-display
        v-for="item in state.selectedObservations"
        :key="`siteObs_${item.id}`"
        :site-observation="item"
        class="siteObs"
        :class="{ outlined: hoveredInfo.siteId.includes(item.id) }"
      />
    </div>
  </div>
</template>

<style scoped>
.sample {
  z-index: 999;
}
.siteObs {
  margin: 10px;
}
.outlined {
  background-color: orange;
  border: 2px solid orange;
}

</style>
