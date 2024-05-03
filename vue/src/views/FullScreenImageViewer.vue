<script setup lang="ts">
import ImageViewer from "../components/imageViewer/ImageViewer.vue"
import { Ref, onMounted, ref } from "vue";
import { SiteDetails } from "../store";
import { ApiService } from "../client";

const props = defineProps(
    {
        siteEvalId: {
            type: String,
            required: true,
        }
    }
);

// Need to get details for the siteEvaluationId
const siteDetails: Ref<SiteDetails | null> = ref(null)
const dateRange: Ref<number[]> = ref([]);
const siteEvaluationName: Ref<string> = ref('')
const loadData = async () =>  {
    const details = await ApiService.getSiteDetails(props.siteEvalId)
    siteDetails.value = {
        region: details.regionName,
        configurationId: details.configurationId,
        siteNumber: parseInt(details.siteNumber),
        version: details.version,
        performer: details.version,
        title: details.title,
    }
    dateRange.value = [details.timemin, details.timemax];
    siteEvaluationName.value = `${details.regionName}_${details.siteNumber.toString()}`
}
onMounted(() => loadData());
</script>

<template>
  <div>
    <ImageViewer
      v-if="siteDetails"
      :site-eval-id="siteEvalId"
      :site-evaluation-name="siteEvaluationName"
      :site-details="siteDetails"
      :date-range="dateRange"

      fullscreen
    />
  </div>
</template>
