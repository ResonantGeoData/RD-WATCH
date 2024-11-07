<script setup lang="ts">
import { computed, ref, watch, withDefaults } from "vue";
import { EvaluationImage } from "../../types";
import { PixelPoly } from "./imageUtils";
import { state } from '../../store';
import { DefaultAnimationSettings } from "../../client/services/ApiService";

interface Props {
    combinedImages: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[];
    rescaleImage: boolean;
}
const props = withDefaults(defineProps<Props>(), {
});

const emit = defineEmits<{
    (e: "imageFilter", data: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[]): void,
    (e: "animationDefaults", data: DefaultAnimationSettings): void;
    (e: "rescaleBBox", data: number): void;
}>();

const baseImageSources = ref(['S2', 'WV', 'L8', 'PL'])
const baseObs = ref(['observations', 'non-observations'])
const filterSettings = ref(true);
const rescaleBorder = ref(1)

const downloadingGifPointSize = computed({
  get() {
    return state.gifSettings.pointSize || 1;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, pointSize: val };
  },
});

const lineThicknessFactor = computed({
  get() {
    return state.gifSettings.lineThicknessFactor;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, lineThicknessFactor: val };
  },
});

const playbackFps = computed({
  get() {
    return state.gifSettings.fps || 1;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, fps: val };
  },
});


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

watch([
  () => state.imageFilter.sources,
  () => state.imageFilter.obsFilter,
  () => state.imageFilter.cloudCover,
  () => state.imageFilter.noData,
  () => props.rescaleImage,
  rescaleBorder,
  playbackFps,
  downloadingGifPointSize,
  lineThicknessFactor,
], (newData, [,,,,,oldRescaleBorder]) => {
  const defaultAnimationSettings: DefaultAnimationSettings = {
    cloudCover: state.imageFilter.cloudCover,
    noData: state.imageFilter.noData,
    sources: state.imageFilter.sources,
    include: state.imageFilter.obsFilter.map((item) => item === 'non-observations' ? 'nonobs' : 'obs'),
    rescale: props.rescaleImage,
    rescale_border: rescaleBorder.value,
    fps: playbackFps.value,
    point_radius: downloadingGifPointSize.value,
    line_thickness_factor: lineThicknessFactor.value,
  }
  emit('animationDefaults', defaultAnimationSettings);

  if (rescaleBorder.value !== oldRescaleBorder) {
    emit('rescaleBBox', rescaleBorder.value);
  }
})
</script>

<template>
  <div class="pt-2">
    <v-icon
      color="blue"
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
    <div
      v-if="filterSettings"
      class="pt-2"
    >
      <v-row dense>
        <v-select
          v-model="state.imageFilter.obsFilter"
          label="Site Observations"
          :items="baseObs"
          multiple
          closable-chips
          chips
          density="compact"
          class="mx-2"
        />
        <v-select
          v-model="state.imageFilter.sources"
          label="Sources"
          :items="baseImageSources"
          multiple
          closable-chips
          density="compact"
          chips
          class="mx-2"
        />
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col
          cols="2"
          class="slider-label"
        >
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
            hide-details
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
        <v-col
          cols="2"
          class="slider-label"
        >
          <span>NoData:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="state.imageFilter.noData"
            min="0"
            max="100"
            step="1"
            color="primary"
            hide-details
            density="compact"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ state.imageFilter.noData }}%
          </span>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col
          cols="2"
          class="slider-label"
        >
          <span>FPS:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="playbackFps"
            min="0.1"
            max="30"
            step="0.1"
            color="primary"
            hide-details
            density="compact"
          />
        </v-col>
        <v-col>
          <span>
            {{ playbackFps.toFixed(2) }}fps
          </span>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col
          cols="2"
          class="slider-label"
        >
          <span>Rescale Border:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="rescaleBorder"
            min="1"
            max="5"
            step="1"
            color="primary"
            hide-details
            density="compact"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ rescaleBorder }}X
          </span>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col
          cols="2"
          class="slider-label"
        >
          <span>Point Radius:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="downloadingGifPointSize"
            min="1"
            max="20"
            step="1"
            color="primary"
            hide-details
            density="compact"
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ downloadingGifPointSize }}px
          </span>
        </v-col>
        <v-col
          cols="2"
          class="slider-label"
        >
          <span>Line Width Factor:</span>
        </v-col>
        <v-col cols="7">
          <v-slider
            v-model.number="lineThicknessFactor"
            :min="0.1"
            :max="2"
            :step="0.1"
            density="compact"
            color="primary"
            hide-details
          />
        </v-col>
        <v-col>
          <span class="pl-2">
            {{ lineThicknessFactor }}
          </span>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<style scoped>
.slider-label {
  font-size: 0.75em;
}
</style>
