<script setup lang="ts">
import { computed, onMounted } from "vue";
import { ApiService } from "../client";
import { state } from "../store";
import { useRoute } from 'vue-router';



const scoringApp = computed(()=> ApiService.getApiPrefix().includes('scoring'));
const route = useRoute();
const proposals = computed(() => route.path.includes('proposals'));


const toggleGroundTruth = (id: string) => {
  if (state.filters.drawObservations?.includes('groundtruth') || state.filters.drawSiteOutline?.includes('groundtruth')) {
        if (state.openedModelRuns) {
          state.openedModelRuns.add(id);
        }
        const configuration_id = Array.from(state.openedModelRuns);
        state.filters = { ...state.filters, configuration_id};
      }
      else if (!state.filters.drawObservations?.includes('groundtruth') && !state.filters.drawSiteOutline?.includes('groundtruth')) {
        if (state.openedModelRuns) {
          if (state.openedModelRuns.has(id)) {
            state.openedModelRuns.delete(id);
          }
        }
        const configuration_id = Array.from(state.openedModelRuns);
        state.filters = { ...state.filters, configuration_id};
      }

}

onMounted(() => {
  // For proposal view we default to sites
  if (proposals.value) {
    const drawObservations = undefined;
    const drawSiteOutline = ['model'];
    state.filters = { ...state.filters, drawSiteOutline, drawObservations, scoringColoring: undefined, siteTimeLimits: undefined };

  }
})

const checkGroundTruth = async () => {
  if (scoringApp.value) {
    return;
  } else if (proposals.value) {
    // We need to get the groundTruth value and toggle that instead.
    if (state.proposals.ground_truths) {
      const id = state.proposals.ground_truths;
      toggleGroundTruth(id);
    }
  } else {
    // We need to find the ground-truth model and add it to the visible items
    const performer = state.filters.performer_ids?.map((item) => state.performerMapping[item].short_code)
    const request = await ApiService.getModelRuns({
      limit: 10,
      performer,
      region: state.filters.regions? state.filters.regions[0] : '',
      groundtruth: true
    });
    if (request.items.length) {
      const id = request.items[0].id;
      toggleGroundTruth(id)
    }
  }
}

const toggleObs = (type?: undefined | 'model' | 'groundtruth') => {
  let val;
  let copy = state.filters.drawObservations;
  if (type === undefined) {
    val = !state.filters.drawObservations ? ['model', 'groundtruth'] : undefined;
  } else {
    if (copy) {
        const index = copy.indexOf(type);
        if (index !== -1 ) {
            copy.splice(index, 1);
        } else {
            copy.push(type);
        }
    } else {
        copy = [type];
    }
    val = copy;
    if (val?.length === 0) {
        val = undefined;
    }
  }
  state.filters = { ...state.filters, drawObservations: val, scoringColoring: undefined };
  checkGroundTruth();
}

const toggleSite = (type?: undefined | 'model' | 'groundtruth') => {
    let val;
  let copy = state.filters.drawSiteOutline;
  if (type === undefined) {
    val = !state.filters.drawSiteOutline ? ['model', 'groundtruth'] : undefined;

  } else {
    if (copy) {
        const index = copy.indexOf(type);
        if (index !== -1 ) {
            copy.splice(index, 1);
        } else {
            copy.push(type);
        }
    } else {
        copy = [type];
    }
    val = copy;
    if (val?.length === 0) {
        val = undefined;
    }
  }
  state.filters = { ...state.filters, drawSiteOutline: val, scoringColoring: undefined, siteTimeLimits: undefined };
  checkGroundTruth();
}

const toggleSiteTimeLimits = () => {
    state.filters = { ...state.filters, siteTimeLimits: !state.filters.siteTimeLimits, scoringColoring: undefined };

}

const toggleRegion = () => {
  const val = !state.filters.drawRegionPoly;
  state.filters = { ...state.filters, drawRegionPoly: val };
}

const toggleScoring = (data? : undefined | 'simple' | 'detailed') => {
  let val = state.filters.scoringColoring ? undefined : 'simple';
  if (data) {
    val = data;
  }
  if (val !== undefined) {
    // We turn off other state;
    state.filters = { ...state.filters, drawObservations: undefined, drawSiteOutline: undefined}

  }
  state.filters = { ...state.filters, scoringColoring: val as 'simple' | 'detailed' | undefined };
}

</script>

<template>
  <v-row
    dense
    class="base"
  >
    <v-menu
      open-on-hover
    >
      <template #activator="{ props }">
        <v-btn
          class="px-2 mx-2"
          v-bind="props"
          size="large"
          :color="state.filters.drawObservations ? 'rgb(37, 99, 235)' : ''"
          style="min-width: 200px"
          @click="toggleObs()"
        >
          <span>
            Observations
          </span>
          <v-icon
            v-if="state.filters.drawObservations?.includes('model')"
          >
            mdi-alpha-m-box
          </v-icon>
          <v-icon
            v-if="state.filters.drawObservations?.includes('groundtruth')"
          >
            mdi-alpha-t-box
          </v-icon>
        </v-btn>
      </template>
      <v-card outlined>
        <v-list>
          <v-list-item
            value="Model"
            @click="toggleObs('model')"
          >
            Model
            <v-icon>
              mdi-alpha-m-box
            </v-icon>
          </v-list-item>
          <v-list-item
            value="GroundTruth"
            @click="toggleObs('groundtruth')"
          >
            GroundTruth
            <v-icon>
              mdi-alpha-t-box
            </v-icon>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>
    <v-menu
      open-on-hover
    >
      <template #activator="{ props }">
        <v-btn
          class="px-2 mx-2"
          v-bind="props"
          size="large"
          :color="state.filters.drawSiteOutline ? 'rgb(37, 99, 235)' : ''"
          style="min-width:150px"
          @click="toggleSite()"
        >
          <span>
            Sites
          </span>
          <v-icon
            v-if="state.filters.drawSiteOutline?.includes('model')"
          >
            mdi-alpha-m-box
          </v-icon>
          <v-icon
            v-if="state.filters.drawSiteOutline?.includes('groundtruth')"
          >
            mdi-alpha-t-box
          </v-icon>
          <v-icon
            v-if="state.filters.siteTimeLimits"
          >
            mdi-clock
          </v-icon>
        </v-btn>
      </template>
      <v-card outlined>
        <v-list>
          <v-list-item
            value="Model"
            @click="toggleSite('model')"
          >
            Model
            <v-icon>
              mdi-alpha-m-box
            </v-icon>
          </v-list-item>
          <v-list-item
            value="GroundTruth"
            @click="toggleSite('groundtruth')"
          >
            GroundTruth
            <v-icon>
              mdi-alpha-t-box
            </v-icon>
          </v-list-item>
          <v-list-item
            value="GroundTruth"
            @click="toggleSiteTimeLimits()"
          >
            Time Limits
            <v-icon>
              mdi-clock
            </v-icon>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>
    <v-btn
      class="px-2 mx-2"
      size="large"
      :color="state.filters.drawRegionPoly ? 'rgb(37, 99, 235)' : ''"
      @click="toggleRegion()"
    >
      Region
    </v-btn>
    <v-menu
      open-on-hover
    >
      <template #activator="{ props }">
        <v-btn
          v-if="scoringApp"
          class="px-2 mx-2"
          v-bind="props"
          size="large"
          :color="state.filters.scoringColoring ? 'rgb(37, 99, 235)' : ''"
          style="min-width:125px"
          @click="toggleScoring()"
        >
          <span>
            Scoring
          </span>
          <v-icon
            v-if="state.filters.scoringColoring == 'simple'"
          >
            mdi-alpha-s-box
          </v-icon>
          <v-icon
            v-if="state.filters.scoringColoring == 'detailed'"
          >
            mdi-alpha-d-box
          </v-icon>
        </v-btn>
      </template>
      <v-card outlined>
        <v-list>
          <v-list-item
            value="Simple"
            @click="toggleScoring('simple')"
          >
            Simple
            <v-icon>
              mdi-alpha-s-box
            </v-icon>
          </v-list-item>
          <v-list-item
            value="Detailed"
            @click="toggleScoring('detailed')"
          >
            Detailed
            <v-icon>
              mdi-alpha-d-box
            </v-icon>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>
  </v-row>
</template>

<style scoped>
.base {
    position: absolute;
    left: 400px;
    margin-left: 10px;
}
.button-label {
    font-size: 8px;
}
</style>
