<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import type { Ref } from "vue";
import { state } from "../store";
import { addPattern } from "../interactions/fillPatterns";
import { InformationCircleIcon } from "@heroicons/vue/24/solid";


const autoZoom = computed({
  get() {
    return state.settings.autoZoom || false;
  },
  set(val: boolean) {
    state.settings = { ...state.settings, autoZoom: val };
  },
});
const imagesOn = computed({
  get() {
    return state.satellite.satelliteImagesOn || false;
  },
  set(val: boolean) {
    state.satellite = { ...state.satellite, satelliteImagesOn: val };
  },
});

const imageOpacity = computed({
  get() {
    return state.satellite.imageOpacity || 0;
  },
  set(val: number) {
    state.satellite = { ...state.satellite, imageOpacity: val };
  },
});

const cloudCover = computed({
  get() {
    return state.satellite.cloudCover || 1000;
  },
  set(val: number) {
    state.satellite = { ...state.satellite, cloudCover: val };
  },
});

const showSiteOutline = computed({
  get() {
    return state.filters.showSiteOutline || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, showSiteOutline: val };
  },
});

const showRegionPolygon = computed({
  get() {
    return state.filters.showRegionPolygon || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, showRegionPolygon: val };
  },
});

const groundTruthPattern = computed({
  get() {
    return state.filters.groundTruthPattern || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, groundTruthPattern: val };
  },
});
const otherPattern = computed({
  get() {
    return state.filters.otherPattern || false;
  },
  set(val: boolean) {
    state.filters = { ...state.filters, otherPattern: val };
  },
});
const patternThickness = computed({
  get() {
    return state.patterns?.patternThickness;
  },
  set(val: number) {
    state.patterns = { ...state.patterns, patternThickness: val };
  },
});

const patternOpacity = computed({
  get() {
    return state.patterns?.patternOpacity;
  },
  set(val: number) {
    state.patterns = { ...state.patterns, patternOpacity: val };
  },
});

const S2Imagery = computed({
  get() {
    return state.satellite.satelliteSources.includes('S2');
  },
  set(val: boolean) {
    if (!state.satellite.satelliteSources.includes('S2') && val) {
      state.satellite.satelliteSources.push('S2')
    } else if (state.satellite.satelliteSources.includes('S2')) {
      const index = state.satellite.satelliteSources.indexOf('S2');
      state.satellite.satelliteSources.splice(index, 1);
    }
  },
});

const worldViewImagery = computed({
  get() {
    return state.satellite.satelliteSources.includes('WorldView');
  },
  set(val: boolean) {
    if (!state.satellite.satelliteSources.includes('WorldView') && val) {
      state.satellite.satelliteSources.push('WorldView')
    } else if (state.satellite.satelliteSources.includes('WorldView')) {
      const index = state.satellite.satelliteSources.indexOf('WorldView');
      state.satellite.satelliteSources.splice(index, 1);
    }
  },
});


const patternDensity: Ref<number> = ref(1);
const patternDensityIndex = ref([64, 128, 256, 512, 1024])


const drawCanvasPattern = () => {
  if (hiddenCanvas.value) {
    var ctx = hiddenCanvas.value.getContext("2d");
    if (ctx) {
      ctx.strokeStyle = "rgba(255,0,0,1)";
      ctx.lineWidth = 4;
      const thickness = patternThickness.value;
      const width = patternDensityIndex.value[patternDensity.value];
      const height = patternDensityIndex.value[patternDensity.value];

      ctx.clearRect(0, 0, width, height);
      ctx.rect(0, 0, width, height);
      ctx.stroke();
      const outlineURL = hiddenCanvas.value.toDataURL();
      if (siteOutlineImg.value) {
        siteOutlineImg.value.src = outlineURL;
      }

      ctx.lineWidth = thickness;
      ctx.strokeStyle = `rgba(0,0,0,${patternOpacity.value}`;
      ctx.clearRect(0, 0, width, height);
      const size = 8;
      for (let i = 0; i <= width; i += size) {
        ctx.beginPath();
        ctx.lineCap = 'round'
        ctx.moveTo(0, width - i * size);
        ctx.lineCap = 'round'
        ctx.lineTo(width - i * size, 0);
        ctx.stroke();
        ctx.beginPath();
        ctx.lineCap = 'round'
        ctx.moveTo(0, width + i * size );
        ctx.lineCap = 'round'
        ctx.lineTo(width + i * size, 0);
        ctx.stroke();
      }

      const dataURL = hiddenCanvas.value.toDataURL();
      if (groundImg.value) {
        groundImg.value.src = dataURL;
      }
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i <= width; i += size) {
        ctx.beginPath();
        ctx.moveTo(i * size, 0);
        ctx.lineTo(width, width - i * size);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i * size);
        ctx.lineTo(width, width + i * size);
        ctx.stroke();
      }
      const performerURL = hiddenCanvas.value.toDataURL();
      if (performerImg.value) {
        performerImg.value.src = performerURL;
      }
    }
  }
};
onMounted(() => {
drawCanvasPattern();
nextTick(() => {
      if (performerImg.value !== null && groundImg.value !== null) {
        addPattern(performerImg.value, groundImg.value);
      }
  });
});


watch([patternThickness, patternOpacity, patternDensity], () => {
    nextTick(() => {
      drawCanvasPattern();
      nextTick(() => {
        if (performerImg.value !== null && groundImg.value !== null) {
          addPattern(performerImg.value, groundImg.value);
        }
      });
    });
});

const groundImg: Ref<null | HTMLImageElement> = ref(null);
const performerImg: Ref<null | HTMLImageElement> = ref(null);
const siteOutlineImg: Ref<null | HTMLImageElement> = ref(null);
const hiddenCanvas: Ref<null | HTMLCanvasElement> = ref(null);
const info = computed(() => {
  const date = import.meta.env.VITE_GIT_COMMIT_DATE;
  const hash = import.meta.env.VITE_GIT_COMMIT_HASH;
  return { date, hash };
});

const expandInfo = ref(false);

watch(hiddenCanvas, () => {
  drawCanvasPattern();
});
</script>

<template>
  <v-card
    variant="outlined"
    class="mb-5"
    width="375"
  >
    <v-container dense>
      <canvas
        ref="hiddenCanvas"
        style="display: none"
        :width="patternDensityIndex[patternDensity]"
        :height="patternDensityIndex[patternDensity]"
      />
      <v-row
        dense
      >
        <h4>
          Settings
        </h4>
        <InformationCircleIcon
          class="hover h-5 text-blue-600"
          @click="expandInfo = !expandInfo"
        />
      </v-row>
      <v-row
        v-if="expandInfo"
        dense
        style="font-size: 0.75em"
      >
        <v-col>
          <div style="font-weight: bold">
            Date:
          </div>
          <span> {{ info.date }}</span>
        </v-col>
        <v-col>
          <div style="font-weight: bold">
            Hash:
          </div>
          <span> {{ info.hash }}</span>
        </v-col>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">Auto Zoom:</span>
          <input
            v-model="autoZoom"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">Images:</span>
          <input
            v-model="imagesOn"
            :disabled="state.satellite.satelliteTimeList.length === 0"

            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row
        v-if="imagesOn"
        dense
        class="form-control"
      >
        <label class="label cursor-pointer">
          <span class="label-text">Image Opacity:</span>
          <input
            v-model.number="imageOpacity"
            min="0"
            max="1"
            step="0.1"
            class="chrome-range w-full"
            type="range"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">S2 Imagery:</span>
          <input
            v-model="S2Imagery"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">WorldView Imagery:</span>
          <input
            v-model="worldViewImagery"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row
        v-if="imagesOn"
        dense
        class="form-control"
      >
        <label class="label cursor-pointer">
          <span class="label-text">Cloud Cover:</span>
          <input
            v-model.number="cloudCover"
            :disabled="state.satellite.loadingSatelliteImages"
            min="0"
            max="100"
            step="20"
            class="chrome-range w-full"
            type="range"
          >
          <span class="label-text pl-2">&lt;{{ cloudCover }}%</span>
        </label>
      </v-row>



      <v-row dense>
        <label class="label cursor-pointer">
          <img
            ref="siteOutlineImg"
            height="32"
            width="32"
          >
          <span class="label-text">Site Outline:</span>
          <input
            v-model="showSiteOutline"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <div
            :style="{
              border: '1px solid grey',
              height: '32px',
              width: '32px'
            }"
          />
          <span class="label-text">Region Polygon:</span>
          <input
            v-model="showRegionPolygon"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <img
            ref="groundImg"
            class="img-pixelated"
            height="32"
            width="32"
          >
          <span class="label-text">Ground Truth Pattern:</span>
          <input
            v-model="groundTruthPattern"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <img
            ref="performerImg"
            height="32"
            width="32"
          >
          <span class="label-text">Performer Pattern:</span>
          <input
            v-model="otherPattern"
            type="checkbox"
            class="checkbox-primary checkbox"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">Pattern Thickness:</span>
          <input
            v-model="patternThickness"
            type="range"
            min="1"
            max="16"
            step="1"
            class="range range-primary"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">Pattern Opacity:</span>
          <input
            v-model="patternOpacity"
            type="range"
            min="0"
            max="1"
            step="0.1"
            class="range range-primary"
          >
        </label>
      </v-row>
      <v-row dense>
        <label class="label cursor-pointer">
          <span class="label-text">Pattern Density:</span>
          <input
            v-model="patternDensity"
            type="range"
            min="0"
            max="4"
            step="1"
            class="range range-primary"
          >
        </label>
      </v-row>
    </v-container>
  </v-card>
</template>

<style scoped>
.hover:hover {
  cursor: pointer;
}

.img-pixelated {
  image-rendering: crisp-edges;
}
</style>
