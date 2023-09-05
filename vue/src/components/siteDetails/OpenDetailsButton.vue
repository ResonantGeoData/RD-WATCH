<script setup lang="ts">
import { ref } from "vue";
import SiteDetails from './SiteDetails.vue';
import { state } from '../../store'
const props = defineProps<{
  siteEvalId: number;
  name: string;
  dateRange: number[] | null;
}>();

const displayImage = ref(false);


const openDetailViewer = () => {
  state.selectedSiteDetails = {
    id: props.siteEvalId,
    name: props.name,
    dateRange: props.dateRange,
  }
  state.openSiteDetails = true;
}

</script>

<template>
  <div>
    <v-btn
      size="small"
      @click="openDetailViewer()"
    >
      Show Details
    </v-btn>
    <v-dialog
      v-model="displayImage"
      width="800"
    >
      <SiteDetails
        :site-eval-id="siteEvalId"
        dialog
        @close="displayImage = false"
      />
    </v-dialog>
  </div>
</template>
