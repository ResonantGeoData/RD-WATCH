<script setup lang="ts">
import { ref } from "vue";
import { ApiService } from "../../client";
import { ObsDetails } from "../../store";
import ImageViewer from './ImageViewer.vue';

defineProps<{
  siteEvalId: string;
  siteEvaluationName?: string;
  dateRange?: number[] | null
  obsDetails?: ObsDetails;
}>();

const displayImage = ref(false);

const openNewTab = (id: string) => {
  const name = `#${ApiService.getApiPrefix().replace('api/','').replace('/api','')}/imageViewer/${id}`
  window.open(name, '_blank');
};

</script>

<template>
  <div>
    <v-btn
      @click="displayImage = true"
    >
      Image Viewer
    </v-btn>
    <v-tooltip
      text="Open Image Viewer in a new tab"
      location="bottom"
    >
      <template #activator="{ props }">
        <v-btn
          v-bind="props"
          class="ml-2"
          @click="openNewTab(siteEvalId)"
        >
          <v-icon v-bind="props">
            mdi-tab-plus
          </v-icon>
        </v-btn>
      </template>
    </v-tooltip>

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
