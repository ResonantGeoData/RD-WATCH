<script setup lang="ts">
import { PropType, Ref, onMounted, watch } from "vue";
import { ApiService } from "../../client";
import SAMEditor from "./SAMEditor.vue";
import { ref } from "vue";
import { state } from "../../store";
import { EvaluationImage } from "../../types";
import { denormalizePolygon } from "./imageUtils";

const props = defineProps({
  siteEvalId: {
    type: String,
    required: true,
  },
  id: {
    type: String,
    required: true,
  },
  image: {
    type: Object as PropType<EvaluationImage>,
    required: true,
  },
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits<{
  (e: "polygonUpdate", data: GeoJSON.Polygon): void;
  (e: "clear"): void;
  (e: "cancel"): void;
}>();

const imageURL = ref("");
const embeddingURL = ref("");
const SAMEditorRef: Ref<HTMLDivElement | null> = ref(null);
const divSize = ref([0, 0]);
const loaded = ref(false);

const loadImageData = async () => {
  loaded.value = false;
  const image = await ApiService.getSiteImage(parseInt(props.id, 10));
  imageURL.value = image.image;
  if (image.image_embedding) {
    embeddingURL.value = image.image_embedding;
  }
  // Now we need to set the numpy value image value for the image display
  if (image.image_dimensions) {
    let ratio = image.image_dimensions[1] / image.image_dimensions[0];
    let heightAdjustment = 0.45;
    let widthAdjustment = -550;
    const maxHeight = document.documentElement.clientHeight * heightAdjustment;
    const maxWidth = document.documentElement.clientWidth - widthAdjustment;
    let width = maxWidth;
    let height = width * ratio;
    if (height > maxHeight) {
      height = maxHeight;
      width = height / ratio;
    }
    divSize.value = [width, height];
  }
  loaded.value = true;
};

onMounted(async () => {
  loadImageData();
});

const updatePolygon = (polygon: GeoJSON.Polygon) => {
  // We need to set it to edit mode if it isn't in edit mode already.
  state.filters.editingPolygonSiteId = props.siteEvalId;
  if (state.editPolygon && polygon) {
    const [imageWidth, imageHeight] = divSize.value;
    const geoPoly = denormalizePolygon(
      props.image.bbox,
      imageWidth,
      imageHeight,
      polygon
    );
    if (geoPoly) {
      state.editPolygon.setPolygonEdit(geoPoly);
    }
  }
};

const cancel = () => {
  state.editPolygon?.cancelPolygonEdit();
  state.filters.editingPolygonSiteId = null;
  emit("cancel");
};

watch([() => props.id, () => props.image, () => props.siteEvalId], () => {
  loadImageData();
});
</script>

<template>
  <v-container v-if="loaded">
    <SAMEditor
      ref="SAMEditorRef"
      :image-url="imageURL"
      :embedding-u-r-l="embeddingURL"
      :width="divSize[0]"
      :height="divSize[1]"
      @update-polygon="updatePolygon"
      @cancel="cancel"
    />
  </v-container>
</template>
