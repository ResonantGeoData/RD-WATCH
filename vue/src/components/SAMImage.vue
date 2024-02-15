<script lang="ts">
import { defineComponent, onMounted } from "vue";

import useSAM from "../use/useSAM";

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
    }
  },
  setup(props) {
    const { state, initModel, loadImage, mouseOut, handleMouse } = useSAM();
    const { image, polygons, maskImg, smoothing, selectedMasks } = state;
    onMounted(async () => {
      await initModel(MODEL_DIR);
      const url = (props.imageUrl);
      await loadImage(url, props.embeddingURL);
    });
    const updateSmoothing = (e: Event) => {
      smoothing.value = parseInt((e.target as HTMLInputElement).value);
    };

    return {
      image,
      polygons,
      maskImg,
      smoothing,
      selectedMasks,
      mouseOut,
      handleMouse,
      updateSmoothing,
    };
  },
});
</script>

<template>
  <div>
    <div>
      <input
        id="smoothness"
        type="range"
        name="smoothness"
        min="0"
        max="30"
        :value="smoothing"
        @change="updateSmoothing($event)"
      >
      <label for="smoothness">Smoothness ({{ smoothing }})</label>
    </div>
    <div class="custom-flex-center full-size">
      <div class="custom-flex-center custom-size">
        <img
          v-if="image"
          :src="image.src"
          class="full-width"
          @mousemove="handleMouse($event, 'hover')"
          @mouseout="mouseOut"
          @click="handleMouse($event, 'click')"
        >
        <img
          v-if="maskImg"
          :src="maskImg.src"
          class="full-width mask custom-styles"
        >
        <img
          v-for="(maskImage, index) in selectedMasks"
          :key="`image_${index}`"
          :src="maskImage.src"
          class="full-width selected-mask"
        >
        <canvas
          id="geoJSONCanvas"
          class="selected-mask"
        />
      </div>
    </div>
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
  width: 100%;
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
