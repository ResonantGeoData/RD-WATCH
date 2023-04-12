<script setup lang="ts">
import { ApiService } from "../../client";
import { SiteObservation } from "../../store";

const props = defineProps<{
  siteObservation: SiteObservation;
}>();

const getImages = (id:number)  => {
    ApiService.getObservationImages(id.toString());
}

</script>

<template>
  <details
    class="group relative rounded-lg border-2 border-gray-50 open:border-blue-600 hover:border-gray-200 open:hover:border-blue-600"
  >
    <summary
      class="cursor-pointer select-none list-none bg-gray-50 p-2 group-open:bg-blue-600 group-hover:bg-gray-200 group-open:group-hover:bg-blue-600"
    >
      <div class="grid grid-cols-8">
        <div class="col-span-8 group-open:text-white">
          <div class="model-title">
            SiteId: {{ siteObservation.id }}
          </div>
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          images:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          <div>L8:{{ siteObservation.imageCounts.L8 }}</div>
          <div>S2:{{ siteObservation.imageCounts.S2 }}</div>
          <div>WV:{{ siteObservation.imageCounts.WV }}</div>
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          score:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{ siteObservation.score.min.toFixed(2) }} to {{ siteObservation.score.max.toFixed(2) }} 
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          average score:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{ siteObservation.score.average.toFixed(2) }}
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          date coverage:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{
            siteObservation.timerange === null
              ? "--"
              : `${new Date(siteObservation.timerange.min * 1000).toLocaleString(
                "en",
                {
                  dateStyle: "short",
                }
              )} - ${new Date(siteObservation.timerange.max * 1000).toLocaleString(
                "en",
                {
                  dateStyle: "short",
                }
              )}`
          }}
        </div>
        <div class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100">
          <button
            class="btn-accent btn-sm"
            @click="getImages(siteObservation.id)"
          >
            Get Images
          </button>
        </div>
      </div>
    </summary>
  </details>
</template>

<style scoped>
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
