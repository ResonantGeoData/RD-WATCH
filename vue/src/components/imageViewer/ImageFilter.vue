<script setup lang="ts">
import { Ref, computed, onMounted, onUnmounted, ref, watch, withDefaults } from "vue";
import { EvaluationImage } from "../../types";
import { PixelPoly } from "./imageUtils";

interface Props {
    combinedImages: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[];
}
const props = withDefaults(defineProps<Props>(), {
});

const emit = defineEmits<{
    (e: "imageFilter", data: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[]): void;
}>();

const baseImageSources = ref(['S2', 'WV', 'L8'])
const baseObs = ref(['observations', 'non-observations'])
const filterSettings = ref(false);
const imageSourcesFilter: Ref<EvaluationImage['source'][]> = ref(['S2', 'WV', 'L8']);
const percentBlackFilter: Ref<number> = ref(100);
const cloudFilter: Ref<number> = ref(100);
const siteObsFilter: Ref<('observations' | 'non-observations')[]> = ref(['observations', 'non-observations'])

const filteredImages = computed(() => {
  return props.combinedImages.filter((item) => {
    let add = true;
    if (!imageSourcesFilter.value.includes(item.image.source)) {
      add = false;
    }
    if (siteObsFilter.value.includes('observations') && siteObsFilter.value.length ===1 && item.image.observation_id === null) {
      add = false;
    }
    if (siteObsFilter.value.includes('non-observations') && siteObsFilter.value.length ===1 && item.image.observation_id !== null) {
      add = false;
    }
    if (item.image.percent_black > percentBlackFilter.value) {
      add = false;
    }
    if (item.image.cloudcover > cloudFilter.value) {
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
    <v-icon @click="filterSettings = !filterSettings">
      mdi-filter
    </v-icon>
    <span>
      {{ filteredImages.length }} of {{ combinedImages.length }} images
    </span>
    <div v-if="filterSettings">
      <v-row dense>
        <v-select
          v-model="siteObsFilter"
          label="Site Observations"
          :items="baseObs"
          multiple
          closable-chips
          chips
          class="mx-2"
        />
        <v-select
          v-model="imageSourcesFilter"
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
            v-model.number="cloudFilter"
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
            {{ cloudFilter }}%
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
            v-model.number="percentBlackFilter"
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
            {{ percentBlackFilter }}%
          </span>
        </v-col>
      </v-row>
    </div>
  </div>
</template>
