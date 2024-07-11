<script setup lang="ts">
import { onMounted } from "vue";
import { ApiService } from "../client";
import SAMEditor from "../components/imageViewer/SAMEditor.vue";
import { ref } from 'vue';
import { updateRegionList, updateRegionMap } from "../store";


const props = defineProps(
    {
        id: {
            type: String,
            required: true,
        }
    }
);

const imageURL = ref('');
const embeddingURL = ref('');

onMounted(async () => {
  await updateRegionList();
  await updateRegionMap();
  const image = await ApiService.getSiteImage(parseInt(props.id, 10));
  imageURL.value = image.image;
  if (image.image_embedding) {
    embeddingURL.value = image.image_embedding;
  }
  // Now we need to set the numpy value image value for the image display
});


</script>

<template>
  <v-main
    v-if="imageURL && embeddingURL"
    style="z-index:1"
  >
    <SAMEditor
      :image-url="imageURL"
      :embedding-u-r-l="embeddingURL"
    />
  </v-main>
</template>
