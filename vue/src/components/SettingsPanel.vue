<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Ref } from "vue";
import { state } from "../store";
import { updatePattern } from "../interactions/fillPatterns";

const showSiteOutline = computed({ 
  get() {  return state.filters.showSiteOutline || false },
  set(val: boolean) {state.filters = { ...state.filters, showSiteOutline: val} }
});

const groundTruthPattern = computed({ 
  get() {  return state.filters.groundTruthPattern || false },
  set(val: boolean) {state.filters = { ...state.filters, groundTruthPattern: val} }
});
const otherPattern = computed({ 
  get() {  return state.filters.otherPattern || false },
  set(val: boolean) {state.filters = { ...state.filters, otherPattern: val} }
});
const patternThickness = computed({ 
  get() {  return state.patterns?.patternThickness },
  set(val: number) {state.patterns = { ...state.patterns, patternThickness: val} }
});

const patternOpacity = computed({ 
  get() {  return state.patterns?.patternOpacity },
  set(val: number) {state.patterns = { ...state.patterns, patternOpacity: val} }
});

const drawCanvasPattern = () => {
  if (hiddenCanvas.value) {
    var ctx =hiddenCanvas.value.getContext("2d");
      if (ctx) {
      ctx.strokeStyle = 'rgba(255,0,0,1)'
      ctx.lineWidth = 20;
      const thickness = patternThickness.value
      const width = hiddenCanvas.value.width;
      const height = hiddenCanvas.value.height;

      ctx.clearRect(0, 0, width,height);
      ctx.rect(0,0,width,height)
      ctx.stroke()
      const outlineURL = hiddenCanvas.value.toDataURL();
      if (siteOutlineImg.value) {
        siteOutlineImg.value.src = outlineURL
      }

      ctx.lineWidth = thickness;
      ctx.strokeStyle = `rgba(0,0,0,${patternOpacity.value / 255}`;
      ctx.clearRect(0, 0, width,height);
      const size = 5;
      for (let i =0; i < width ; i += size ) {
        ctx.beginPath();
        ctx.moveTo(0, width - i*size);
        ctx.lineTo(width - (i * size), 0);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, width + i*size);
        ctx.lineTo(width + (i * size), 0);
        ctx.stroke();
      }
      const dataURL = hiddenCanvas.value.toDataURL();
      if (groundImg.value) {
        groundImg.value.src = dataURL
      }
      ctx.clearRect(0, 0, width,height);
      for (let i =0; i < width ; i += size ) {
        ctx.beginPath();
        ctx.moveTo(i*size, 0);
        ctx.lineTo(width, width - (i * size));
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i*size);
        ctx.lineTo(width, width + (i * size));
        ctx.stroke();
      }
      const performerURL = hiddenCanvas.value.toDataURL();
      if (performerImg.value) {
        performerImg.value.src = performerURL
      }
    }
  }
}

watch([patternThickness, patternOpacity], () => {
  const data = updatePattern(patternThickness.value, patternOpacity.value);
  if (groundImg.value && data) {
    var blob = new Blob( [data['diagonal-right']], { type: "image/png" } );
    var urlCreator = window.URL || window.webkitURL;
    var imageUrl = urlCreator.createObjectURL( blob );
    state.patterns = {
      patternThickness: patternThickness.value,
      patternOpacity: patternOpacity.value,
    };
    groundImg.value.src = imageUrl;
    drawCanvasPattern();
  }
});

const groundImg: Ref<null | HTMLImageElement> = ref(null)
const performerImg: Ref<null | HTMLImageElement> = ref(null)
const siteOutlineImg: Ref<null | HTMLImageElement> = ref(null)
const hiddenCanvas: Ref<null | HTMLCanvasElement> = ref(null)

watch(hiddenCanvas, () => {
  drawCanvasPattern();
});

</script>

<template>
  <div class="gap-2 border-t border-gray-300 bg-gray-100 p-2">
    <canvas ref="hiddenCanvas" style="display:none;"  width="75" height="75" />
    <h4>Settings</h4>
    <div class="form-control">
      <label class="label cursor-pointer">
        <img ref="siteOutlineImg" height="20" width="20" />
        <span class="label-text">Site Outline:</span> 
        <input v-model="showSiteOutline" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <img ref="groundImg" height="20" width="20" />
        <span class="label-text">Ground Truth Pattern:</span> 
        <input v-model="groundTruthPattern" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <img ref="performerImg" height="20" width="20" />
        <span class="label-text">Performer Pattern:</span> 
        <input v-model="otherPattern" type="checkbox" class="checkbox checkbox-primary" />
      </label>
    </div>
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Pattern Thickness:</span> 
        <input v-model="patternThickness" type="range" min="1" max="10" step="0.25" class="range range-primary" />
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
