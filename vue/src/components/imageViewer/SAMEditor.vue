<script lang="ts">
import { computed, defineComponent, onMounted } from "vue";

import useSAM from "../../use/useSAM";

const MODEL_DIR = "/sam_onnx_quantized_example.onnx";

export default defineComponent({
  name: "SAMImage",
  props: {
    imageUrl: {
      type: String,
      required: true
    },
    embeddingURL: {
      type: String,
      required: true,
    },
    width: {
      type: Number,
      default: -1,
    },
    height: {
      type: Number,
      default: -1,
    }
  },
  emits: ['updatePolygon', 'clear', 'cancel'],
  setup(props, { emit }) {
    const { state, initModel, loadImage, mouseOut, handleMouse, undo, convertMasksToPoly, clearMasks, updateSmoothing } = useSAM();
    const { image, polygons, maskImg, smoothing, selectedMasks } = state;
    onMounted(async () => {
      await initModel(MODEL_DIR);
      const url = (props.imageUrl);
      await loadImage(url, props.embeddingURL);
    });
    const adjustSmoothing = async (e: number) => {
      smoothing.value = e;
      const polygon = await updateSmoothing(smoothing.value);
      if (polygon) {
        emit('updatePolygon',  polygon);
      }

    };

    const widthGreater = computed(() => {
      if (image.value?.src) {
        return (image.value.width > image.value.height);
      }
      return false;
    })

    const generatePolys = async () => {
      const polygon = await convertMasksToPoly();
      if (polygons) {
        emit('updatePolygon',  polygon);
      }
    }

    const clearPoly = () => {
      clearMasks();
      emit('clear');
    }

    const cancel = () => {
      clearMasks();
      emit('cancel');
    }

    return {
      image,
      polygons,
      maskImg,
      smoothing,
      selectedMasks,
      widthGreater,
      mouseOut,
      handleMouse,
      adjustSmoothing,
      generatePolys,
      cancel,
      undo,
      clearPoly

    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-btn
        size="small"
        color="error"
        class="mx-2"
        @click="cancel()"
      >
        Cancel
      </v-btn>
      <v-btn
        v-if="selectedMasks.length"
        size="small"
        class="mx-2"
        @click="undo()"
      >
        Undo
      </v-btn>
      <v-btn
        v-if="selectedMasks.length"
        size="small"
        class="mx-2"
        @click="clearPoly()"
      >
        Clear
      </v-btn>
      <v-btn
        v-if="selectedMasks.length"
        size="small"
        class="mx-2"
        :disabled="!selectedMasks.length"
        @click="generatePolys()"
      >
        generate
      </v-btn>
      <v-slider
        v-if="polygons.length"
        :model-value="smoothing"
        min="0"
        max="30"
        step="1"
        :label="`Smoothness: ${smoothing}`"
        color="primary"
        thumb-label
        density="compact"
        @end="adjustSmoothing($event)"
      />
    </v-row>
    <v-row>
      <v-spacer />
      <div style="position: relative;">
        <img
          v-if="image"
          id="baseSAMImage"
          :src="image.src"
          :style="`width: ${width}px; height: ${height}px`"
          @mousemove="handleMouse($event, 'hover')"
          @mouseout="mouseOut"
          @click="handleMouse($event, 'click')"
        >
        <img
          v-if="maskImg"
          :src="maskImg.src"
          class="mask custom-styles"
          :style="`width: ${width}px; height: ${height}px`"
        >
        <img
          v-for="(maskImage, index) in selectedMasks"
          :key="`image_${index}`"
          :src="maskImage.src"
          class="selected-mask"
          :style="`width: ${width}px; height: ${height}px`"
        >
        <canvas
          id="geoJSONCanvas"
          class="selected-mask"
          :style="`width: ${width}px; height: ${height}px`"
          style="position: absolute; top: 0; left: 0;"
        />
      </div>
      <v-spacer />
    </v-row>
  </div>
</template>

<style lang="scss" scoped>
.custom-flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.full-size {
  width: 100%;
  height: 100%;
}
.custom-size {
  position: relative;
  width: 90%;
  height: 90%;
}
.full-width {
  width: 90vw;
}
.full-height {
  height: 80vh;
}

.full-height {
  height: 100%;
}
.mask {
  z-index: 1000;
  // border: 1px solid red;
}

.selected-mask {
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0.6;
  pointer-events: none;
}
.custom-styles {
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0.4;
  pointer-events: none;
}
</style>
