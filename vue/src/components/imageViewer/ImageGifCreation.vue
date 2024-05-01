<script setup lang="ts">
import { Ref, computed, ref, watch, withDefaults } from "vue";
import { EvaluationImage } from "../../types";
import { PixelPoly } from "./imageUtils";
import { CanvasCapture } from 'canvas-capture';
import { createCanvas, drawData } from './imageUtils';
import { state } from '../../store'

interface Props {
  filteredImages: {image: EvaluationImage; poly: PixelPoly, groundTruthPoly?: PixelPoly}[];
  siteEvaluationName: string | null;
  drawGroundTruth: boolean;
  rescaleImage: boolean;
  fullscreen: boolean | undefined;
  rescalingBBox: number;
  disabled: boolean,
  background: HTMLCanvasElement & { ctx?: CanvasRenderingContext2D | null } | undefined;

}
const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits<{
    (e: "rescaleBBox", data: number): void;
}>();

const downloadingGifFPS = computed({
  get() {
    return state.gifSettings.fps;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, fps: val };
  },
});
const downloadingGifQuality = computed({
  get() {
    return state.gifSettings.quality || 0.01;
  },
  set(val: number) {
    state.gifSettings = { ...state.gifSettings, quality: val };
  },
});


const downloadingGif = ref(false);
const downloadingGifState: Ref<null | 'drawing' | 'generating'> = ref(null);
const downloadingGifProgress = ref(0);
const GifSettingsDialog = ref(false);
const exportProgress = (progress: number) => {
  downloadingGifProgress.value = progress * 100;
  if (progress === 1) {
    downloadingGif.value = false;
    downloadingGifState.value = null;
    downloadingGifProgress.value = 0;
  }
}
const rescaleBBoxLocal = ref(props.rescalingBBox);

watch(() => props.rescalingBBox, () => {
    rescaleBBoxLocal.value = props.rescalingBBox;
})

function drawForDownload() {
  downloadingGif.value = true;
  let width = -Infinity;
  let height = -Infinity;
  for (let i = 0; i< props.filteredImages.length; i += 1) {
    const [imgWidth, imgHeight ] =props.filteredImages[i].image.image_dimensions;
    width = Math.max(width, imgWidth);
    height = Math.max(height, imgHeight);
  }
  if (width < 500 || height < 500) {
    const ratio = width / height;
    if (width < 500) {
      width = 500;
      height = ratio / 500;
    }
    if (height < 500) {
      height = 500;
      width = ratio * 500;
    }
  }
  const offScreenCanvas = createCanvas(width * props.rescalingBBox, height * props.rescalingBBox);
  downloadingGifState.value = 'drawing';
  CanvasCapture.init(offScreenCanvas, { verbose: false});
  CanvasCapture.beginGIFRecord({
    name: props.siteEvaluationName || 'download',
    fps: downloadingGifFPS.value,
    quality: downloadingGifQuality.value,
    onExportProgress: exportProgress,
  });
  let index = 0;
  function drawImageForRecord(){
    requestAnimationFrame(drawImageForRecord);
    if (index < props.filteredImages.length ) {
      drawData(
        offScreenCanvas,
        props.filteredImages[index].image,
        props.filteredImages[index].poly,
        props.filteredImages[index].groundTruthPoly,
        width,
        height,
        props.background,
        props.drawGroundTruth,
        props.rescaleImage,
        props.fullscreen,
        props.rescalingBBox,
      );
      CanvasCapture.recordFrame();
      index += 1
      downloadingGifProgress.value = (index / props.filteredImages.length) * 100;
    } else {
      CanvasCapture.stopRecord();
      downloadingGifState.value = 'generating';
      downloadingGifProgress.value = 0;
    }
  }
  drawImageForRecord();
}

</script>

<template>
  <div>
    <div v-if="downloadingGif">
      <span> {{ downloadingGifState === 'drawing' ? 'Drawing' : 'GIF Creation' }}</span>
      <v-progress-linear
        v-model="downloadingGifProgress"
        width="50"
      />
    </div>
    <v-tooltip
      open-delay="50"
      bottom
    >
      <template #activator="{ props }">
        <v-btn
          v-if="!downloadingGif"
          v-bind="props"
          variant="tonal"
          density="compact"
          :disabled="disabled"
          class="pa-0 ma-1 sidebar-icon"
          @click="drawForDownload()"
        >
          <v-icon>
            mdi-download-box-outline
          </v-icon>
        </v-btn>
        <v-btn
          v-else
          v-bind="props"
          variant="tonal"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
        >
          <v-icon>
            mdi-spin mdi-sync
          </v-icon>
          <v-icon @click="GifSettingsDialog = true">
            mdi-cog
          </v-icon>
        </v-btn>
      </template>
      <span>
        Download Images to GIF.
      </span>
    </v-tooltip>
    <v-tooltip
      open-delay="50"
      bottom
    >
      <template #activator="{ props }">
        <v-btn
          v-bind="props"
          variant="tonal"
          :disabled="disabled"
          density="compact"
          class="pa-0 ma-1 sidebar-icon"
          @click="GifSettingsDialog = true"
        >
          <v-icon>
            mdi-cog
          </v-icon>
        </v-btn>
      </template>
      <span> GIF Download Settings</span>
    </v-tooltip>
    <v-dialog
      v-model="GifSettingsDialog"
      width="400"
    >
      <v-card>
        <v-card-title> GIF Downloading Settings</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-text-field
              v-model.number="downloadingGifFPS"
              type="number"
              label="FPS"
              step="0.1"
              :rules="[v => v > 0 || 'Value must be greater than 0']"
            />
          </v-row>
          <v-row dense>
            <v-slider
              v-model="rescaleBBoxLocal"
              min="1"
              max="5"
              step="0.1"
              :label="`Zoom out (${rescaleBBoxLocal.toFixed(2)})X`"
              @update:model-value="$emit('rescaleBBox', $event)"
            />
          </v-row>

          <v-row dense>
            <v-slider
              v-model="downloadingGifQuality"
              min="0"
              max="1"
              step="0.1"
              :label="`Quality (${downloadingGifQuality.toFixed(2)})`"
            />
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-row>
            <v-spacer />
            <v-btn
              color="success"
              @click="GifSettingsDialog = false"
            >
              OK
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.sidebar-icon {
  min-width: 20px;
  min-height: 20px;;
}
</style>