<script setup lang="ts">
import { computed } from "vue";
import { ApiService } from "../../client";
import { ImageBBox, SiteObservationImage, state } from "../../store";
import { SiteObservation } from "../../store";
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
  const data = await ApiService.getSiteObservations(props.siteObservation.id.toString());
          const { results, images } = data;
          const worldViewList = images.results.filter((item) => item.source === 'WV')
            .sort((a, b) => (a.timestamp - b.timestamp));
          const S2List = images.results.filter((item) => item.source === 'S2');
          const L8 = { 
            total: results.filter((item) => item.constellation === 'L8').length,
            loaded:0,
          };
          const S2 = {
            total: results.filter((item) => item.constellation === 'S2').length,
            loaded:S2List.length,
            images: S2List,
          };
          const WV = { 
            total: results.filter((item) => item.constellation === 'WV').length,
            loaded:worldViewList.length,
            images: worldViewList,
          };
          let minScore = Infinity;
          let maxScore = -Infinity;
          let avgScore = 0;
          results.forEach((item) => {
            minScore = Math.min(minScore, item.score);
            maxScore = Math.max(maxScore, item.score);
            avgScore += item.score
          })
          avgScore = avgScore / results.length;
          const foundIndex = state.selectedObservations.findIndex((item) => item.id === props.siteObservation.id);
          
          state.selectedObservations.splice(foundIndex,1,
          {
            id: props.siteObservation.id,
            timerange: data.timerange,
            imagesLoaded: false,
            imagesActive: false,
            imageCounts: {
              L8,
              S2,
              WV,
            },
            score: {
              min: minScore,
              max: maxScore,
              average: avgScore,
            },
            bbox: data.bbox,
          } )
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
    class="relative rounded-lg border-2 border-gray-50 open:border-blue-600 hover:border-gray-200 open:hover:border-blue-600"
  >
    <summary
      class="select-none list-none bg-gray-50 p-2 group-hover:bg-gray-200"
    >
      <div class="grid grid-cols-4">
        <div class="col-span-4">
          <div class="grid grid-cols-2">
            <span class="model-title">
              SiteId: {{ siteObservation.id }}
            </span>
            <span class="grid grid-cols-2 justify-self-end">
              <ArrowPathIcon
                class="hover h-5 text-blue-600"
                data-tip="Refresh"
                @click="refresh()"
              />

              <XMarkIcon
                class="hover h-5 text-red-600 "
                data-tip="Close"
                @click="close()"
              />
            </span>
          </div>
        </div>
        <div
          class="col-span-1 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          images:
        </div>
        <div class="col-span-3 text-xs font-light group-open:text-white">
          <div>L8: <b>{{ siteObservation.imageCounts.L8.loaded }}</b> of {{ siteObservation.imageCounts.L8.total }}</div>
          <div>S2: <b>{{ siteObservation.imageCounts.S2.loaded }}</b> of {{ siteObservation.imageCounts.S2.total }}</div>
          <div>WV: <b>{{ siteObservation.imageCounts.WV.loaded }}</b> of {{ siteObservation.imageCounts.WV.total }}</div>
        </div>
        <div
          class="col-span-1 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          score:
        </div>
        <div class="col-span-3 text-xs font-light group-open:text-white">
          {{ siteObservation.score.min.toFixed(2) }} to {{ siteObservation.score.max.toFixed(2) }} 
        </div>
        <div
          class="col-span-1 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          average score:
        </div>
        <div class="col-span-3 text-xs font-light group-open:text-white">
          {{ siteObservation.score.average.toFixed(2) }}
        </div>
        <div
          class="col-span-1 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          date coverage:
        </div>
        <div class="col-span-3 text-xs font-light group-open:text-white">
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
        <div class="col-span-4 text-xs font-light text-gray-600 group-open:text-gray-100">
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
          class="col-span-4 font-light text-gray-600 group-open:text-gray-100"
        >
          <button
            class="btn-primary btn-xs m-1"
            :class="{'btn-disabled': !currentClosestTimestamp.prev}"
            @click="goToTimestamp(-1)"
          >
            Prev
          </button>

          <span
            v-if="currentClosestTimestamp"
            style="font-size: 0.75em; min-width:175px"
            class="badge-secondary badge ml-1"
          >{{ currentClosestTimestamp.time }} - {{ currentClosestTimestamp.type }} id:{{  currentClosestTimestamp.siteobs ? currentClosestTimestamp.siteobs : 'null'}}</span>
          <button
            class="btn-primary btn-xs m-1"
            :class="{'btn-disabled': !currentClosestTimestamp.next}"
            @click="goToTimestamp(1)"
          >
            Next
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
.checkboxlabel {
  display: inline;
}
</style>
