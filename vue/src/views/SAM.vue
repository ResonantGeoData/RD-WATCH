<script setup lang="ts">
import SideBar from "../components/SideBar.vue"
import MapLibre from "../components/MapLibre.vue";
import RightBar from "../components/RightBar.vue"
import LayerSelection from "../components/LayerSelection.vue";
import { onMounted } from "vue";
import { state } from "../store";
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
  embeddingURL.value = image.image_embedding;
  // Now we need to set the numpy value image value for the image display
});


</script>

<template>
  <v-main v-if="imageURL && embeddingURL" style="z-index:1">
    <SAMImage :imageUrl="imageURL" :embeddingURL="embeddingURL" />
    <h3>{{ imageURL }}</h3>
  </v-main>
</template>
