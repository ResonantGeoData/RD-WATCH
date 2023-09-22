<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import type { Ref } from "vue";
import { state } from "../store";
import { addPattern } from "../interactions/fillPatterns";

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
    state.filters = { ...state.filters, showSiteOutline: val,  };
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
const showText = computed({
    get() {
      return state.filters.showText || false;
    },
    set(val: boolean) {
      state.filters = { ...state.filters, showText: val };
    },

  })

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
    class="mb-2 settings-card"
    width="350"
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
        <v-spacer />
        <v-icon
          size="small"
          :color="expandInfo ? 'rgb(37, 99, 235)' : 'black'"
          @click="expandInfo = !expandInfo"
        >
          mdi-information
        </v-icon>
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
        <v-col cols="8">
          <v-checkbox
            v-model="autoZoom"
            label="Auto Zoom"
            density="compact"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="imagesOn"
            label="Images"
            density="compact"
            :disabled="state.satellite.satelliteTimeList.length === 0"
          />
        </v-col>
      </v-row>
      <v-row
        v-if="imagesOn"
        dense
      >
        <v-col cols="8">
          <v-checkbox
            v-model="S2Imagery"
            label="S2 Imagery"
            density="compact"
          />
        </v-col>
      </v-row>
      <v-row 
        v-if="imagesOn"
        dense
      >
        <v-col cols="8">
          <v-checkbox
            v-model="worldViewImagery"
            label="WorldView Imagery"
            density="compact"
          />
        </v-col>
      </v-row>

      <v-row
        v-if="imagesOn"
        dense
        align="center"
        justify="center"
      >
        <v-col cols="4">
          <span>Image Opacity:</span>
        </v-col>
        <v-col cols="6">
          <v-slider
            v-model.number="imageOpacity"
            min="0"
            max="1"
            step="0.1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col cols="2">
          <span class="">{{ (imageOpacity * 100).toFixed(0) }}%</span>
        </v-col>
      </v-row>
      <v-row
        v-if="imagesOn"
        dense
        align="center"
        justify="center"
      >
        <v-col>
          <span class="label">Cloud Cover:</span>
        </v-col>
        <v-col cols="6">
          <v-slider
            v-model.number="cloudCover"
            :disabled="state.satellite.loadingSatelliteImages"
            min="0"
            max="100"
            step="20"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
        <v-col cols="2">
          <span class="label">&lt;{{ cloudCover }}%</span>
        </v-col>
      </v-row>


      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="showText"
            label="Site Label On"
            density="compact"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="showSiteOutline"
            label="Site Outline:"
            density="compact"
          />
        </v-col>
        <v-col>
          <img
            ref="siteOutlineImg"
            height="32"
            width="32"
          >
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="showRegionPolygon"
            label="Region Polygon:"
            density="compact"
          />
        </v-col>
        <v-col>
          <div
            :style="{
              border: '1px solid grey',
              height: '32px',
              width: '32px'
            }"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="groundTruthPattern"
            label="Ground Truth Pattern:"
            density="compact"
          />
        </v-col>
        <v-col>
          <img
            ref="groundImg"
            class="img-pixelated"
            height="32"
            width="32"
          >
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="8">
          <v-checkbox
            v-model="otherPattern"
            label="PerformerPattern:"
            density="compact"
          />
        </v-col>
        <v-col>
          <img
            ref="performerImg"
            height="32"
            width="32"
          >
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="4">
          <span>Pattern Thickness:</span>
        </v-col>
        <v-col>
          <v-slider
            v-model.number="patternThickness"
            min="1"
            max="16"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="4">
          <span>Pattern Opacity:</span>
        </v-col>
        <v-col>
          <v-slider
            v-model.number="patternOpacity"
            min="0"
            max="1"
            step="0.1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="4">
          <span>Pattern Density:</span>
        </v-col>
        <v-col>
          <v-slider
            v-model.number="patternDensity"
            min="0"
            max="4"
            step="1"
            color="primary"
            density="compact"
            class="mt-5"
          />
        </v-col>
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
.settings-card {
  overflow-y: auto;
  max-height: calc(100vh - 250px);
}
</style>
