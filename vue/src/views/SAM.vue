<script setup lang="ts">
import { onMounted } from "vue";
import { ApiService } from "../client";
import SAMImage from "../components/SAMImage.vue";
import { ref } from 'vue';


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
    <SAMImage
      :image-url="imageURL"
      :embedding-u-r-l="embeddingURL"
    />
  </v-main>
</template>
