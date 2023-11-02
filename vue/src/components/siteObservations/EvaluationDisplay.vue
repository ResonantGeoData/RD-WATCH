<script setup lang="ts">
import { computed, ref } from "vue";
import { getSiteObservationDetails, state, toggleSatelliteImages } from "../../store";
import { SiteObservation } from "../../store";
import { imageFilter } from "../../mapstyle/images";
import EvaluationImages from "./EvaluationImages.vue";
import EvaluationScoring from "./EvaluationScoring.vue";
import ImageViewerButton from "../imageViewer/ImageViewerButton.vue";
import { timeRangeFormat } from "../../utils";
const props = defineProps<{
  siteObservation: SiteObservation;
}>();



const refresh = async () => {
  await getSiteObservationDetails(props.siteObservation.id.toString(), props.siteObservation.obsDetails);
}
const close = () => {
  const foundIndex = state.selectedObservations.findIndex((item) => item.id === props.siteObservation.id);
  if (foundIndex !== -1) {
    toggleSatelliteImages(props.siteObservation, true);
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
        time: `${new Date(closest * 1000).toLocaleDateString()}`,
        type: observation.images[rootIndex].source,
        prev,
        next,
        siteobs: observation.images[rootIndex].observation_id,
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
const noScore = ref(false);

const changeTimstamp = ({dir, loop}: {dir: number, loop: boolean}) => {
  goToTimestamp(dir, loop);
}


const hasLoadedImages = computed(() => (Object.entries(props.siteObservation.imageCounts).findIndex(([,data]) => data.loaded > 0) !== -1));

</script>

<template>
  <v-card class="siteevaldisplay">
    <v-card-text>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col v-if="siteObservation.obsDetails">
          <span class="model-title">
            {{ `${siteObservation.obsDetails.region}_${siteObservation.obsDetails.siteNumber.toString().padStart(4, '0')}` }}
          </span>
        </v-col>
        <v-col cols="1">
          <span>
            <v-btn
              variant="text"
              density="compact"
              :color="imagesActive ? 'rgb(37, 99, 235)': 'black'"
              :disabled="!hasImages"
              icon="mdi-image"
              @click="hasImages && toggleSatelliteImages(siteObservation)"
            />
          </span>
        </v-col>
        <v-spacer />
        <v-col class="">
          <v-row dense>
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
          </v-row>
        </v-col>
      </v-row>
      <v-row
        dense
        justify="center"
        align="center"
      >
        <v-col v-if="siteObservation.obsDetails">
          <span>{{ `${siteObservation.obsDetails.performer} ${siteObservation.obsDetails.title}: V${siteObservation.obsDetails.version}` }}</span>
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
        <v-expansion-panel
          v-if="siteObservation.obsDetails && siteObservation.obsDetails.version && !noScore"
          key="Scoring"
        >
          <v-expansion-panel-title>Scoring</v-expansion-panel-title>
          <v-expansion-panel-text>
            <evaluation-scoring
              :site-observation="siteObservation"
              @no-score="noScore=true"
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
          {{ timeRangeFormat(siteObservation.timerange) }}
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
          size="35"
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
          size="35"
          :disabled="!currentClosestTimestamp.next"
          :color="currentClosestTimestamp.next ? 'rgb(37, 99, 235)' : 'gray'"
          @click="goToTimestamp(1)"
        >
          mdi-chevron-right
        </v-icon>
      </v-row>
      <v-row>
        <image-viewer-button
          v-if="hasLoadedImages && siteObservation.obsDetails"
          :site-eval-id="siteObservation.id"
          :obs-details="siteObservation.obsDetails"
          :date-range="siteObservation.timerange ? [siteObservation.timerange?.min, siteObservation.timerange.max]: undefined"
          :site-evaluation-name="`${siteObservation.obsDetails.region}_${siteObservation.obsDetails.siteNumber.toString().padStart(4, '0')}`"
        />
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
  font-size: 0.70em;
}

</style>
