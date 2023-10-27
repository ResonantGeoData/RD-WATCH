<script setup lang="ts">
import { ref } from "vue";
import { ObsDetails } from "../../store";
import ImageViewer from './ImageViewer.vue';

defineProps<{
  siteEvalId: string;
  siteEvaluationName?: string;
  dateRange?: number[] | null
  obsDetails?: ObsDetails;
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
        :site-evaluation-name="siteEvaluationName"
        :obs-details="obsDetails"
        :date-range="dateRange"
        dialog
        @close="displayImage = false"
      />
    </v-dialog>
  </div>
</template>
