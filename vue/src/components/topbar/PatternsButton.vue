<script setup lang="ts">
import { Ref, computed, nextTick, onMounted, ref, watch } from "vue";
import { state } from "../../store";
import { addPattern } from "../../interactions/fillPatterns";

const groundImg: Ref<null | HTMLImageElement> = ref(null);
const menuImg: Ref<null | HTMLImageElement> = ref(null);
const performerImg: Ref<null | HTMLImageElement> = ref(null);
const siteOutlineImg: Ref<null | HTMLImageElement> = ref(null);
const hiddenCanvas: Ref<null | HTMLCanvasElement> = ref(null);
const patternDensity: Ref<number> = ref(1);
const patternDensityIndex = ref([64, 128, 256, 512, 1024]);

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

watch(hiddenCanvas, () => {
  drawCanvasPattern();
});

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
        ctx.lineCap = "round";
        ctx.moveTo(0, width - i * size);
        ctx.lineCap = "round";
        ctx.lineTo(width - i * size, 0);
        ctx.stroke();
        ctx.beginPath();
        ctx.lineCap = "round";
        ctx.moveTo(0, width + i * size);
        ctx.lineCap = "round";
        ctx.lineTo(width + i * size, 0);
        ctx.stroke();
      }

      const dataURL = hiddenCanvas.value.toDataURL();
      if (groundImg.value) {
        groundImg.value.src = dataURL;
      }
      if (menuImg.value) {
        menuImg.value.src = dataURL;
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

const menuOpened = () => {
  nextTick(() => {
    drawCanvasPattern();
    if (performerImg.value !== null && groundImg.value !== null) {
      addPattern(performerImg.value, groundImg.value);
    }
  });
};

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
</script>

<template>
  <canvas
    ref="hiddenCanvas"
    style="display: none"
    :width="patternDensityIndex[patternDensity]"
    :height="patternDensityIndex[patternDensity]"
  />
  <v-menu
    open-on-click
    :close-on-content-click="false"
    width="400"
    @update:model-value="menuOpened"
  >
    <template #activator="{ props }">
      <v-btn
        v-bind="props"
        class="px-2 mx-2"
        :variant="groundTruthPattern || otherPattern ? undefined : 'text'"
        :color="groundTruthPattern || otherPattern ? 'primary' : ''"
      >
        <img
          ref="menuImg"
          class="img-pixelated"
          height="24"
          width="24"
        >
        <v-icon :color="groundTruthPattern || otherPattern ? 'white' : ''">
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card class="pa-4 pattern-card">
      <v-card-title class="card-title mb-2">
        Fill Pattern
      </v-card-title>
      <v-row
        class="px-3"
        align="center"
        justify="center"
      >
        <v-col cols="2">
          <img
            ref="groundImg"
            class="img-pixelated"
            height="32"
            width="32"
          >
        </v-col>
        <v-col>
          Ground Truth Pattern
        </v-col>
        <v-col cols="2">
          <v-checkbox
            v-model="groundTruthPattern"
            density="compact"
            hide-details
          />
        </v-col>
      </v-row>
      <v-row
        class="px-3"
        justify="center"
        align="center"
      >
        <v-col cols="2">
          <img
            ref="performerImg"
            height="32"
            width="32"
          >
        </v-col>
        <v-col>
          Performer Pattern
        </v-col>
        <v-col cols="2">
          <v-checkbox
            v-model="otherPattern"
            density="compact"
            hide-details
          />
        </v-col>
      </v-row>
      <v-row
        dense
        class="px-3"
        align="center"
        justify="center"
      >
        <v-col cols="4">
          <span>Thickness:</span>
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
      <v-row
        dense
        class="px-3"
        align="center"
        justify="center"
      >
        <v-col cols="4">
          <span>Opacity:</span>
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
      <v-row
        dense
        class="px-3"
        align="center"
        justify="center"
      >
        <v-col cols="4">
          <span>Density:</span>
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
    </v-card>
  </v-menu>
</template>

<style scoped>
.hover:hover {
  cursor: pointer;
}
.img-pixelated {
  image-rendering: crisp-edges;
}
.card-title {
  background-color: #F3F3F3;
}
</style>
