<script setup lang="ts">
import { computed, onBeforeMount, onBeforeUnmount } from "vue";
import { ApiService } from "../../client";
import { ImageBBox, SiteObservationImage, getSiteObservationDetails, state } from "../../store";
import { SiteObservation } from "../../store";
import { imageFilter } from "../../mapstyle/images";
import EvaluationImages from "./EvaluationImages.vue";
import EvaluationScoring from "./EvaluationScoring.vue";

const props = defineProps<{
  siteObservation: SiteObservation;
}>();


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
            if (siteObs.imageCounts.WV.images && state.siteObsSatSettings.observationSources.includes('WV')) {
              imageList = [...siteObs.imageCounts.WV.images]
            }
            if (siteObs.imageCounts.S2.images && state.siteObsSatSettings.observationSources.includes('S2')) {
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
  await getSiteObservationDetails(props.siteObservation.id.toString(), props.siteObservation.scoringBase);
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

const currentClosestTimestamp = computed(() => {
  const observation = state.enabledSiteObservations.find((item) => item.id === props.siteObservation.id);
  if (observation) {
    const images = observation.images.filter((item) => imageFilter(item, state.siteObsSatSettings));
    if (images.length) {
      const closest = images.map((item) => item.timestamp).reduce((prev, curr) => {
                  return Math.abs(curr - state.timestamp) < Math.abs(prev - state.timestamp) ? curr : prev
              });
      const rootIndex = observation.images.findIndex((item) => item.timestamp === closest);
      const index = images.findIndex((item) => item.timestamp === closest);
      let prev = true;
      let next = true;
      if (index === 0) {
        prev = false;
      }
      if (index + 1 >= images.length) {
        next = false;
      }
      return {
        time: `${new Date(closest * 1000).toLocaleDateString()} ${new Date(closest * 1000).toLocaleTimeString()}`, 
        type: observation.images[rootIndex].source,
        prev,
        next,
        siteobs: observation.images[rootIndex].siteobs_id,
        total: observation.images.filter((item) => item.source !== 'L8').length,
        filteredTotal: images.length,
        index,
        cloudCover: observation.images[rootIndex].cloudcover,
        percentBlack: observation.images[rootIndex].percent_black,
       };
    }
  }
  return null;
})
const goToTimestamp = (dir: number, loop = false) => {
  if (currentClosestTimestamp.value && currentClosestTimestamp.value.time) {
    const observation = state.enabledSiteObservations.find((item) => item.id === props.siteObservation.id);
    if (observation) {
      const images = observation.images.filter((item) => imageFilter(item, state.siteObsSatSettings));
      const closest = images.filter((item) => !item.disabled).map((item) => item.timestamp).reduce((prev, curr) => {
                return Math.abs(curr - state.timestamp) < Math.abs(prev - state.timestamp) ? curr : prev
            });
      const index = images.findIndex((item) => item.timestamp === closest);
      if (dir === 1 && index + 1< images.length) {
        state.timestamp = images[index + 1].timestamp;
      } else if (dir === 1 && loop && images.length) {
        state.timestamp = images[0].timestamp;
      }
      if (dir === -1 && index > 0) {
        state.timestamp = images[index - 1].timestamp;
      }
    }
  }
}

const changeTimstamp = ({dir, loop}: {dir: number, loop: boolean}) => {
  goToTimestamp(dir, loop);
}

</script>

<template>
  <v-card class="siteevaldisplay">
    <v-card-text>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col>
          <span class="model-title">
            {{ `${state.regionMap[siteObservation.scoringBase.regionId]}_${siteObservation.scoringBase.siteNumber.toString().padStart(4, '0')}` }}
          </span>
        </v-col>
        <v-col>
          <span>
            <v-btn
              variant="text"
              density="compact"
              :color="imagesActive ? 'rgb(37, 99, 235)': 'black'"
              :disabled="!hasImages"
              icon="mdi-image"
              @click="hasImages && toggleImages(siteObservation)"
            />
          </span>
        </v-col>
        <v-spacer />
        <v-col class="pl-10">
          <v-icon 
            size="large"
            color="rgb(37, 99, 235)"
            class="mr-2"
            @click="refresh()"
          >
            mdi-sync
          </v-icon>

          <v-icon
            size="large"
            color="red"
            @click="close()"
          >
            mdi-close
          </v-icon>
        </v-col>
      </v-row>
      <v-expansion-panels
        variant="accordion"
        class="pa-0 ma-0 mb-2"
      >
        <v-expansion-panel key="Images">
          <v-expansion-panel-title>Images</v-expansion-panel-title>
          <v-expansion-panel-text>
            <evaluation-images
              :site-observation="siteObservation"
              :images-active="imagesActive"
              @change-timestamp="changeTimstamp($event)"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel v-if="siteObservation.scoringBase.version" key="Scoring">
          <v-expansion-panel-title>Scoring</v-expansion-panel-title>
          <v-expansion-panel-text>
            <evaluation-scoring
              :site-observation="siteObservation"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      
      <v-row
        dense
        justify="center"
        align="center"
      >
        <div>
          score:
        </div>
        <div>
          {{ siteObservation.score.min.toFixed(2) }} to {{ siteObservation.score.max.toFixed(2) }} 
        </div>
        <v-spacer />
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <div>
          average:
        </div>
        <div c>
          {{ siteObservation.score.average.toFixed(2) }}
        </div>
        <v-spacer />
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <div>
          dates:
        </div>
        <div>
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
        <v-spacer />
      </v-row>

      <v-row
        dense
        justify="center"
        align="center"
        class="details"
      >
        <v-col
          v-if="currentClosestTimestamp"
        >
          <b>Filter:</b> {{ currentClosestTimestamp.filteredTotal }} of {{ currentClosestTimestamp.total }}
        </v-col>
        <v-col
          v-if="currentClosestTimestamp"
        >
          <b>Cloud:</b> {{ currentClosestTimestamp.cloudCover }}%
        </v-col>
        <v-col
          v-if="currentClosestTimestamp && currentClosestTimestamp.percentBlack !== undefined && currentClosestTimestamp.percentBlack !== null"
        >
          <b>>NoData:</b> {{ currentClosestTimestamp.percentBlack.toFixed(0) }}%
        </v-col>
      </v-row>

      <v-row
        v-if="imagesActive && currentClosestTimestamp"
        dense
        justify="center"
        align="center"
      >
        <v-icon
          size="40"
          :disabled="!currentClosestTimestamp.prev"
          :color="currentClosestTimestamp.prev ? 'rgb(37, 99, 235)' : 'gray'"
          @click="goToTimestamp(-1)"
        >
          mdi-chevron-left
        </v-icon>

        <span
          v-if="currentClosestTimestamp"
          class="timedisplay"
        >
          {{ currentClosestTimestamp.time }} - {{ currentClosestTimestamp.type }}{{ currentClosestTimestamp.siteobs !== null ? '*': '' }}
        </span>
        <v-icon
          size="40"
          :disabled="!currentClosestTimestamp.next"
          :color="currentClosestTimestamp.next ? 'rgb(37, 99, 235)' : 'gray'"
          @click="goToTimestamp(1)"
        >
          mdi-chevron-right
        </v-icon>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.siteevaldisplay {
  -webkit-user-select: none; /* Safari */
  -ms-user-select: none; /* IE 10 and IE 11 */
  user-select: none; /* Standard syntax */
}
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

.timedisplay {
  font-size: 1em;
  min-width:220px;
  max-width:220px;
  text-align: center;
}
.hover:hover {
  cursor: pointer;
}
.details {
  font-size: 0.75em;
}

</style>
