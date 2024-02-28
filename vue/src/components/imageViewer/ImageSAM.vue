<script setup lang="ts">
import { PropType, onMounted } from "vue";
import { ApiService } from "../../client";
import SAMEditor from "./SAMEditor.vue";
import { ref } from 'vue';
import { state } from "../../store";
import { EvaluationImage } from "../../types";
import { denormalizePolygon } from "./imageUtils";


const props = defineProps(
    {
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
        }
    }
);

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits<{
    (e: "polygonUpdate", data: GeoJSON.Polygon): void;
    (e: "clear"): void;
    (e: "cancel"): void;
}>();

const imageURL = ref('');
const embeddingURL = ref('');

onMounted(async () => {
  const image = await ApiService.getSiteImage(parseInt(props.id, 10));
  imageURL.value = image.image;
  if (image.image_embedding) {
    embeddingURL.value = image.image_embedding;
  }
  // Now we need to set the numpy value image value for the image display
});

const updatePolygon = (polygon: GeoJSON.Polygon) => {
    console.log('updatePolygon');
    console.log(polygon);
    // We need to set it to edit mode if it isn't in edit mode already.
    state.filters.editingPolygonSiteId = props.siteEvalId;
  if (state.editPolygon && polygon) {
    const [imageWidth, imageHeight] =  props.image.image_dimensions;
    const geoPoly = denormalizePolygon(props.image.bbox, imageWidth, imageHeight, polygon);
    if (geoPoly) {
        state.editPolygon.setPolygonEdit(geoPoly);
    }
  }

}

</script>

<template>
  <v-container>
    <SAMEditor
      :image-url="imageURL"
      :embedding-u-r-l="embeddingURL"
      @update-polygon="updatePolygon"
    />
  </v-container>
</template>
