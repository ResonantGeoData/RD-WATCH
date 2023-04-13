<script setup lang="ts">
import { ApiService } from "../../client";
import { ImageBBox, state } from "../../store";
import { SiteObservation } from "../../store";

const props = defineProps<{
  siteObservation: SiteObservation;
}>();

const getImages = (id:number)  => {
    ApiService.getObservationImages(id.toString());
}

const turnImagesOn = (siteObs: SiteObservation) => {
    const found = state.enabledSiteObservations.find((item) => item.id === siteObs.id);
    if (found === undefined) {
        const baseBBox = siteObs.bbox;
        const bbox = [
            [baseBBox.xmin, baseBBox.ymax],
            [baseBBox.xmax, baseBBox.ymax],
            [baseBBox.xmax, baseBBox.ymin],
            [baseBBox.xmin, baseBBox.ymin],
        ] as ImageBBox;
        if (siteObs.imageCounts.WV.images) {
            const tempArr = [...state.enabledSiteObservations];
            tempArr.push({
                id: siteObs.id,
                timestamp: siteObs.timerange.min,
                images: siteObs.imageCounts.WV.images,
                bbox,
            });
            state.enabledSiteObservations = tempArr;
            console.log(`Adding site: ${siteObs.id}`)
        }
    } else {
        const tempArr = [...state.enabledSiteObservations];
        const index = tempArr.findIndex((item) => item.id === siteObs.id);
        if (index !== -1) {
            tempArr.splice(index, 1);
            state.enabledSiteObservations = tempArr;
        }
    }
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
          <div>L8: <b>{{ siteObservation.imageCounts.L8.loaded }}</b> of {{ siteObservation.imageCounts.L8.total }}</div>
          <div>S2: <b>{{ siteObservation.imageCounts.S2.loaded }}</b> of {{ siteObservation.imageCounts.S2.total }}</div>
          <div>WV: <b>{{ siteObservation.imageCounts.WV.loaded }}</b> of {{ siteObservation.imageCounts.WV.total }}</div>
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
          <div class="form-control ml-10">
            <label class="label cursor-pointer">
              <span class="label-text">Images:</span>
              <input
                :value="siteObservation.imagesActive"
                :disabled="siteObservation.imageCounts.WV.loaded === 0"
                type="checkbox"
                class="checkbox-primary checkbox"
                @click="turnImagesOn(siteObservation)"
              >
            </label>
          </div>
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
