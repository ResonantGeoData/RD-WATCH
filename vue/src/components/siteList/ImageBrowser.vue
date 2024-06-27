<script setup lang="ts">
import { computed } from "vue";
import { state } from "../../store";
import { SiteOverview } from "../../store";
import { imageFilter } from "../../mapstyle/images";
const props = defineProps<{
  siteOverview: SiteOverview;
}>();

const imagesActive = computed(() => state.enabledSiteImages.findIndex((item) => item.id === props.siteOverview.id) !== -1);



const currentClosestTimestamp = computed(() => {
  const observation = state.enabledSiteImages.find((item) => item.id === props.siteOverview.id);
  if (observation) {
    const images = observation.images.filter((item) => imageFilter(item, state.siteOverviewSatSettings));
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
    const observation = state.enabledSiteImages.find((item) => item.id === props.siteOverview.id);
    if (observation) {
      const images = observation.images.filter((item) => imageFilter(item, state.siteOverviewSatSettings));
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



</script>

<template>
  <div @click.stop>
    <v-row
      dense
      justify="center"
      align="center"
      class="details"
    >
      <v-col
        v-if="currentClosestTimestamp"
      >
        {{ currentClosestTimestamp.filteredTotal }} of {{ currentClosestTimestamp.total }}
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
        size="25"
        :disabled="!currentClosestTimestamp.prev"
        :color="currentClosestTimestamp.prev ? 'primary' : 'gray'"
        @click.stop="goToTimestamp(-1)"
      >
        mdi-chevron-left
      </v-icon>
      <v-spacer />
      <span
        v-if="currentClosestTimestamp"
        class="timedisplay"
      >
        {{ currentClosestTimestamp.time }} - {{ currentClosestTimestamp.type }}{{ currentClosestTimestamp.siteobs !== null ? '*': '' }}
      </span>
      <v-spacer />
      <v-icon
        size="25"
        :disabled="!currentClosestTimestamp.next"
        :color="currentClosestTimestamp.next ? 'primary' : 'gray'"
        @click.stop="goToTimestamp(1)"
      >
        mdi-chevron-right
      </v-icon>
      <v-spacer />
    </v-row>
  </div>
</template>

<style scoped>
.timedisplay {
  font-size: 1em;
  text-align: center;
  margin: auto;
}

.details {
  font-size: 0.70em;
}
</style>
