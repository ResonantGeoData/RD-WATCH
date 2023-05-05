<script setup lang="ts">
import { computed } from "vue";
import { ApiService } from "../../client";
import { ImageBBox, SiteObservationImage, getSiteObservationDetails, state } from "../../store";
import { SiteObservation } from "../../store";
import { ArrowPathIcon, ChevronLeftIcon, ChevronRightIcon, XMarkIcon } from "@heroicons/vue/24/solid";
const props = defineProps<{
  siteObservation: SiteObservation;
}>();
const getImages = (id:number, constellation: 'WV' | 'S2' | 'L8' = 'WV')  => {
    ApiService.getObservationImages(id.toString(), constellation);
}
const toggleImages = (siteObs: SiteObservation, off= false) => {
    const found = state.enabledSiteObservations.find((item) => item.id === siteObs.id);
    if (found === undefined && !off) {
        const baseBBox = siteObs.bbox;
        const bbox = [
            [baseBBox.xmin, baseBBox.ymax],
            [baseBBox.xmax, baseBBox.ymax],
            [baseBBox.xmax, baseBBox.ymin],
            [baseBBox.xmin, baseBBox.ymin],
        ] as ImageBBox;
        if (siteObs.imageCounts.WV.images || siteObs.imageCounts.S2.images) {
            const tempArr = [...state.enabledSiteObservations];
            let imageList: SiteObservationImage[] = [];
            if (siteObs.imageCounts.WV.images && state.observationSources.includes('WV')) {
              imageList = [...siteObs.imageCounts.WV.images]
            }
            if (siteObs.imageCounts.S2.images && state.observationSources.includes('S2')) {
              imageList = [...imageList, ...siteObs.imageCounts.S2.images]
            }
            tempArr.push({
                id: siteObs.id,
                timestamp: siteObs.timerange.min,
                images: imageList,
                bbox,
            });
            state.enabledSiteObservations = tempArr;
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
const refresh = async () => {
  await getSiteObservationDetails(props.siteObservation.id.toString());
}
const close = () => {
  const foundIndex = state.selectedObservations.findIndex((item) => item.id === props.siteObservation.id);
  if (foundIndex !== -1) {
    toggleImages(props.siteObservation, true);
    state.selectedObservations.splice(foundIndex, 1);
  }
}
const imagesActive = computed(() => state.enabledSiteObservations.findIndex((item) => item.id === props.siteObservation.id) !== -1);
const hasImages = computed(() => props.siteObservation.imageCounts.WV.loaded > 0 || props.siteObservation.imageCounts.S2.loaded > 0);
const canGetImages = computed(() => ({
  WV: props.siteObservation.imageCounts.WV.total,
  S2: props.siteObservation.imageCounts.S2.total,
}));
const currentClosestTimestamp = computed(() => {
  const observation = state.enabledSiteObservations.find((item) => item.id === props.siteObservation.id);
  if (observation) {
    const images = observation.images.filter((item) => !item.disabled)
    if (images.length) {
      const closest = images.map((item) => item.timestamp).reduce((prev, curr) => {
                  return Math.abs(curr - state.timestamp) < Math.abs(prev - state.timestamp) ? curr : prev
              });
      const index = observation.images.findIndex((item) => item.timestamp === closest);
      let prev = true;
      let next = true;
      if (index === 0) {
        prev = false;
      }
      if (index + 1 >= observation.images.length) {
        next = false;
      }
      return {time: new Date(closest * 1000).toLocaleDateString(), type: observation.images[index].source, prev, next, siteobs: observation.images[index].siteobs_id };
    }
  }
  return null;
})
const goToTimestamp = (dir: number, loop = false) => {
  if (currentClosestTimestamp.value && currentClosestTimestamp.value.time) {
    const observation = state.enabledSiteObservations.find((item) => item.id === props.siteObservation.id);
    if (observation) {
      const closest = observation.images.filter((item) => !item.disabled).map((item) => item.timestamp).reduce((prev, curr) => {
                return Math.abs(curr - state.timestamp) < Math.abs(prev - state.timestamp) ? curr : prev
            });
      const index = observation.images.findIndex((item) => item.timestamp === closest);
      if (dir === 1 && index + 1< observation.images.length) {
        state.timestamp = observation.images[index + 1].timestamp;
      } else if (dir === 1 && loop && observation.images.length) {
        state.timestamp = observation.images[0].timestamp;
      }
      if (dir === -1 && index > 0) {
        state.timestamp = observation.images[index - 1].timestamp;
      }
    }
  }
}
const startLooping = () => {
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
  }
  state.loopingInterval = setInterval(() => {
    goToTimestamp(1, true)
  }, 1000);
  state.loopingId = props.siteObservation.id;
}
const stopLooping = () => {
  if (state.loopingInterval !== null) {
    clearInterval(state.loopingInterval);
    state.loopingId = null;
  }
}
</script>

<template>
  <details
    class="relative rounded-lg border-2 border-gray-50 open:border-blue-600 hover:border-gray-200"
  >
    <summary
      class="list-none bg-gray-50 p-2 group-hover:bg-gray-200"
    >
      <div class="grid grid-cols-4">
        <div class="col-span-4">
          <div class="grid grid-cols-2">
            <span class="model-title">
              SiteId: {{ siteObservation.id }}
            </span>
            <span class="grid grid-cols-2 justify-self-end">
              <ArrowPathIcon
                class="icon h-5 text-blue-600"
                data-tip="Refresh"
                @click="refresh()"
              />

              <XMarkIcon
                class="icon h-5 text-red-600 "
                data-tip="Close"
                @click="close()"
              />
            </span>
          </div>
        </div>
        <div class="col-span-4 text-sm font-light group-open:text-white ">
          <div class="grid grid-cols-4 ">
            <div class="justify-self-center">
              Source
            </div>
            <div class="justify-self-center">
              Cached
            </div>
            <div class="justify-self-center">
              Obs
            </div>
            <div class="justify-self-center">
              Non-Obs
            </div>
          </div>
          <div class="grid grid-cols-4 ">
            <b class="justify-self-center">L8</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.L8.loaded }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.L8.total }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.L8.loaded !== 0 ?Math.max(siteObservation.imageCounts.L8.loaded - siteObservation.imageCounts.L8.total, 0) : '-' }}</b>
          </div>
          <div class="grid grid-cols-4 ">
            <b class="justify-self-center">S2</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.S2.loaded }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.S2.total }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.S2.loaded !== 0 ?Math.max(siteObservation.imageCounts.S2.loaded - siteObservation.imageCounts.S2.total, 0) : '-' }}</b>
          </div>
          <div class="grid grid-cols-4 ">
            <b class="justify-self-center">WV</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.WV.loaded }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.WV.total }}</b>
            <b class="justify-self-center">{{ siteObservation.imageCounts.WV.loaded !== 0 ?Math.max(siteObservation.imageCounts.WV.loaded - siteObservation.imageCounts.WV.total, 0) : '-' }}</b>
          </div>
        </div>
        <div
          class="col-span-1 text-sm font-light text-gray-600 group-open:text-gray-100"
        >
          score:
        </div>
        <div class="col-span-3 text-sm font-light group-open:text-white">
          {{ siteObservation.score.min.toFixed(2) }} to {{ siteObservation.score.max.toFixed(2) }} 
        </div>
        <div
          class="col-span-1 text-sm font-light text-gray-600 group-open:text-gray-100"
        >
          average:
        </div>
        <div class="col-span-3 text-sm font-light group-open:text-white">
          {{ siteObservation.score.average.toFixed(2) }}
        </div>
        <div
          class="col-span-1 text-sm font-light text-gray-600 group-open:text-gray-100"
        >
          dates:
        </div>
        <div class="col-span-3 text-sm font-light group-open:text-white">
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
        <div class="col-span-4 text-sm font-light text-gray-600 group-open:text-gray-100">
          <button
            class="btn-accent btn-xs m-1"
            :class="{'btn-disabled': canGetImages.WV === 0}"
            @click="getImages(siteObservation.id, 'WV')"
          >
            Get WV
          </button>
          <button
            class="btn-accent btn-xs m-1"
            :class="{'btn-disabled': canGetImages.S2 === 0}"
            @click="getImages(siteObservation.id, 'S2')"
          >
            Get S2
          </button>
          <button
            v-if="false"
            class="btn-accent btn-xs m-1"
            @click="getImages(siteObservation.id, 'L8')"
          >
            Get L8
          </button>

          <span class="label checkboxlabel">
            <span class="label-text">Images:</span>
            <input
              :value="siteObservation.imagesActive"
              :disabled="!hasImages"
              type="checkbox"
              class="checkbox-primary checkbox-xs ml-1"
              @click="toggleImages(siteObservation)"
            >
          </span>
          <span v-if="imagesActive">
            <button
              v-if="state.loopingId !== siteObservation.id"
              class="btn-success btn-xs m-1 ml-2"
              @click="startLooping()"
            >
              Play
            </button>
            <button
              v-else
              class="btn-error btn-xs m-1 ml-2"
              @click="stopLooping()"
            >
              Stop
            </button>
          </span>
        </div>
        <div 
          v-if="imagesActive && currentClosestTimestamp"
          class="col-span-4 grid grid-flow-col"
        >
          <ChevronLeftIcon
            class="h-10 text-blue-600"
            :class="{'icon': currentClosestTimestamp.prev, 'text-gray-600': !currentClosestTimestamp.prev}"
            @click="goToTimestamp(-1)"
          />
          <span
            v-if="currentClosestTimestamp"
            style="font-size: 1em; min-width:200px; text-align: center;"
            class="justify-self-center self-center"
          >{{ currentClosestTimestamp.time }} - {{ currentClosestTimestamp.type }}{{ currentClosestTimestamp.siteobs !== null ? '*': '' }}</span>
          <ChevronRightIcon
            class="h-10 text-blue-600 "
            :class="{'icon': currentClosestTimestamp.next, 'text-gray-600': !currentClosestTimestamp.next}"
            @click="goToTimestamp(1)"
          />
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
.checkboxlabel {
  display: inline;
}
.icon:hover {
  cursor: pointer;
  font-weight: bolder;
}
</style>
