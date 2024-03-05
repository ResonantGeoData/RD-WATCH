<script setup lang="ts">
import { computed, ref, watch, withDefaults } from "vue";
import { EvaluationImage } from "../../types";
import { PixelPoly } from "./imageUtils";
import { state } from '../../store';

interface Props {
    combinedImages: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[];
}
const props = withDefaults(defineProps<Props>(), {
});

const emit = defineEmits<{
    (e: "imageFilter", data: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[]): void;
}>();

const baseImageSources = ref(['S2', 'WV', 'L8', 'PL'])
const baseObs = ref(['observations', 'non-observations'])
const filterSettings = ref(false);


const filteredImages = computed(() => {
  return props.combinedImages.filter((item) => {
    let add = true;
    if (!state.imageFilter.sources.includes(item.image.source)) {
      add = false;
    }
    if (state.imageFilter.obsFilter.includes('observations') && state.imageFilter.obsFilter.length ===1 && item.image.observation_id === null) {
      add = false;
    }
    if (state.imageFilter.obsFilter.includes('non-observations') && state.imageFilter.obsFilter.length ===1 && item.image.observation_id !== null) {
      add = false;
    }
    if (item.image.percent_black > state.imageFilter.noData) {
      add = false;
    }
    if (item.image.cloudcover > state.imageFilter.cloudCover
) {
      add = false;
    }
    return add;
  });
})
watch(filteredImages, () => {
  emit('imageFilter', filteredImages.value);
})
</script>

<template>
  <div>
    <v-icon
      :color="filterSettings ? 'blue' : ''"
      @click="filterSettings = !filterSettings"
    >
      mdi-filter
    </v-icon>
    <span>
      {{ filteredImages.length }}/{{ combinedImages.length }}
    </span>
    <span v-if="state.imageFilter.sources.length !== 4">
      <v-chip
        v-for="item in state.imageFilter.sources"
        :key="`filterChip_${item}`"
        size="small"
      >
        {{ item }}
      </v-chip>
    </span>
    <div v-if="filterSettings">
      <v-row dense>
        <v-select
          v-model="state.imageFilter.obsFilter"
          label="Site Observations"
          :items="baseObs"
          multiple
          closable-chips
          chips
          class="mx-2"
        />
        <v-select
          v-model="state.imageFilter.sources"
          label="Sources"
          :items="baseImageSources"
          multiple
          closable-chips
          chips
          class="mx-2"
        />
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col cols="3">
          <span>Cloud Cover:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="state.imageFilter.cloudCover"
            min="0"
            max="100"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ state.imageFilter.cloudCover }}%
          </span>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col cols="3">
          <span>NoData:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="state.imageFilter.noData"
            min="0"
            max="100"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ state.imageFilter.noData }}%
          </span>
        </v-col>
      </v-row>
    </div>
  </div>
</template>
