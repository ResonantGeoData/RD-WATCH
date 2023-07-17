<script setup lang="ts">
import { ref } from "vue";
import ImageViewer from './ImageViewer.vue';
const props = defineProps<{
  siteEvalId: number;
}>();

const displayImage = ref(false);


</script>

<template>
  <div>
    <v-btn @click="displayImage = true">
      Show Image Viewer
    </v-btn>
    <v-dialog
      v-model="displayImage"
      width="800"
    >
      <ImageViewer
        :site-eval-id="siteEvalId"
        dialog
        @close="displayImage = false"
      />
    </v-dialog>
  </div>
</template>
