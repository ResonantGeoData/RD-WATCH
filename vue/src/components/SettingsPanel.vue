<script setup lang="ts">
import { ref, watch } from "vue";
import type { Performer, QueryArguments, Region } from "../client";
import type { Ref } from "vue";
import { state } from "../store";
import { updatePattern } from "../interactions/fillPatterns";

const showSiteOutline: Ref<boolean> = ref(false);
const groundTruthPattern: Ref<boolean> = ref(false);
const otherPattern: Ref<boolean> = ref(false);
const patternThickness = ref(1);
const patternOpacity = ref(255);
watch(showSiteOutline, (val) => {
  state.filters = { ...state.filters, showSiteOutline: val };
});

watch(groundTruthPattern, (val) => {
  state.filters = { ...state.filters, groundTruthPattern: val };
});

watch(otherPattern, (val) => {
  state.filters = { ...state.filters, otherPattern: val };
});

watch([patternThickness, patternOpacity], () => {
  updatePattern(patternThickness.value, patternOpacity.value);
});

</script>

<template>
  <div class="gap-2 border-t border-gray-300 bg-gray-100 p-2">
    <h4>Settings</h4>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Site Outline:</span> 
        <input v-model="showSiteOutline" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Ground Truth Pattern:</span> 
        <input v-model="groundTruthPattern" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Performer Pattern:</span> 
        <input v-model="otherPattern" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Pattern Thickness:</span> 
        <input v-model="patternThickness" type="range" min="0" max="10" step="0.25" class="range range-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Pattern Opacity:</span> 
        <input v-model="patternOpacity" type="range" min="0" max="255" class="range range-primary" />
      </label>
    </div>

  </div>
</template>
