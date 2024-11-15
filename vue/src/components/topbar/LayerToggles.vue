
<script setup lang="ts">
import { computed, defineProps, onMounted, watch, withDefaults } from "vue";
import { ApiService } from "../../client";
import { state } from "../../store";
import { useRoute } from 'vue-router';



withDefaults(defineProps<{
  annotation: boolean;
}>(), {
  annotation: false,
});


const scoringApp = computed(()=> ApiService.getApiPrefix().includes('scoring'));
const route = useRoute();
const proposals = computed(() => route.path.includes('proposals'));


const modelRunEnabled = computed(() => state.openedModelRuns.size > 0);

enum GroundTruthState {
  NoGroundTruth = 0,
  HasGroundTruth = 1,
  AllGroundTruth = 2,
}

// Either has ground truth, is ground truth, or no ground truth
const groundTruthState = computed<GroundTruthState>(() => {
  let result: GroundTruthState  = GroundTruthState.NoGroundTruth;
  if (scoringApp.value) {
    return GroundTruthState.HasGroundTruth;
  }
  if (proposals.value) {
    if (state.proposals.ground_truths) {
      return GroundTruthState.HasGroundTruth;
    } else {
      return GroundTruthState.NoGroundTruth;
    }
  }
  let hasGroundTruth = false;
  state.openedModelRuns.forEach((item) => {
    if (state.groundTruthLinks[item]) {
      hasGroundTruth = true;
    }
  });
  if (hasGroundTruth) {
    result = GroundTruthState.HasGroundTruth;
  }
  // Check to see if it is ground Truth
  if (result === GroundTruthState.HasGroundTruth) {
    const keys = Object.keys(state.groundTruthLinks);
    const keysLength = keys.length;
    let selfReferencedKeys = 0;
    keys.forEach((key) => {
      if (state.groundTruthLinks[key] === key) {
        selfReferencedKeys += 1;
      }
    });
    if (selfReferencedKeys === keysLength) { // All groundTruth
      result = GroundTruthState.AllGroundTruth;
    }
  }
  return result;
});

watch(groundTruthState, () => {
  if (groundTruthState.value === GroundTruthState.AllGroundTruth && state.filters.drawSiteOutline?.includes('model')) {
    state.filters.drawSiteOutline = ['groundtruth'];
  }
  if (groundTruthState.value === GroundTruthState.AllGroundTruth && state.filters.drawObservations?.includes('model')) {
    state.filters.drawObservations = ['groundtruth'];
  }
});

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
          state.openedModelRuns.delete(id);
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
  if (scoringApp.value || groundTruthState.value === GroundTruthState.AllGroundTruth) {
    return;
  } else if (proposals.value) {
    // We need to get the groundTruth value and toggle that instead.
    if (state.proposals.ground_truths) {
      const id = state.proposals.ground_truths;
      toggleGroundTruth(id);
    }
  } else {
    // We need to find the ground-truth model and add it to the visible items
    Object.values(state.groundTruthLinks).forEach((uid) => {
      toggleGroundTruth(uid);
    });
  }
}

const toggleObs = (type?: undefined | 'model' | 'groundtruth') => {
  let val;
  let copy = state.filters.drawObservations;
  if (type === undefined) {
    const onVal:string[] = [];
    if (groundTruthState.value !== GroundTruthState.AllGroundTruth) {
      onVal.push('model');
    }
    if (groundTruthState.value === GroundTruthState.HasGroundTruth || groundTruthState.value === GroundTruthState.AllGroundTruth) {
      onVal.push('groundtruth');
    }
    val = !state.filters.drawObservations ? onVal : undefined;
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
    const onVal:string[] = [];
    if (groundTruthState.value !== GroundTruthState.AllGroundTruth) {
      onVal.push('model');
    }
    if (groundTruthState.value === GroundTruthState.HasGroundTruth || groundTruthState.value === GroundTruthState.AllGroundTruth) {
      onVal.push('groundtruth');
    }
    val = !state.filters.drawSiteOutline ? onVal : undefined;

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

const addProposal = () => {
  state.filters.addingSitePolygon = true;
}


</script>


<template>
  <v-menu
    v-if="scoringApp"
    open-on-hover
  >
    <template #activator="{ props }">
      <v-btn
        class="px-2 mx-2"
        v-bind="props"
        size="large"
        :disabled="!modelRunEnabled"
        :variant="state.filters.scoringColoring ? undefined : 'text'"
        :color="state.filters.scoringColoring ? 'primary' : ''"
        style="min-width:125px"
        @click="toggleScoring()"
      >
        <span>
          Scoring
        </span>
        <div
          v-if="state.filters.scoringColoring == 'simple'"
          class="layer-icon mx-1"
        >
          S
        </div>
        <div
          v-if="state.filters.scoringColoring == 'detailed'"
          class="layer-icon mx-1"
        >
          D
        </div>
        <v-icon :color="state.filters.scoringColoring ? 'white' : 'black'">
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card outlined>
      <v-list>
        <v-list-item
          value="Simple"
          @click="toggleScoring('simple')"
        >
          <div
            class="layer-icon pl-1"
          >
            S
          </div>

          <div
            class="layer-text"
          >
            Simple
          </div>
          <v-radio
            :model-value="state.filters.scoringColoring == 'simple'"
            density="compact"
            hide-details
            readonly
            class="item-checkbox"
          />
        </v-list-item>
        <v-list-item
          value="Detailed"
          @click="toggleScoring('detailed')"
        >
          <div
            class="layer-icon pl-1"
          >
            D
          </div>
          <div
            class="layer-text"
          >
            Detailed
          </div>
          <v-radio
            :model-value="state.filters.scoringColoring == 'detailed'"
            density="compact"
            hide-details
            readonly
            class="item-checkbox"
          />
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
  <v-divider
    v-if="scoringApp"
    vertical
  />
  <v-menu
    open-on-hover
  >
    <template #activator="{ props }">
      <v-btn
        class="px-2 mx-2"
        v-bind="props"
        :disabled="!modelRunEnabled"
        :variant="state.filters.drawObservations ? undefined : 'text'"
        :color="state.filters.drawObservations ? 'primary' : ''"
        style="min-width: 200px"
        @click="toggleObs()"
      >
        <span>
          Observations
        </span>
        <div
          v-if="state.filters.drawObservations?.includes('model')"
          class="layer-icon mx-1"
        >
          M
        </div>
        <div
          v-if="state.filters.drawObservations?.includes('groundtruth')"
          class="layer-icon mx-1"
        >
          G
        </div>
        <v-icon :color="state.filters.drawObservations ? 'white' : 'black'">
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card outlined>
      <v-list>
        <v-list-item
          value="All"
          class="rootItem"
          @click="toggleObs()"
        >
          <v-row
            dense
            align="center"
            class="pa-0 ma-0"
          >
            <v-spacer />
            <v-checkbox
              :model-value="state.filters.drawObservations?.includes('model') && state.filters.drawObservations?.includes('groundtruth')"
              density="compact"
              hide-details
              class="item-checkbox"
            />
          </v-row>
        </v-list-item>
        <v-list-item
          value="Model"
          :class="{'disabled-item': groundTruthState === GroundTruthState.AllGroundTruth}"
          :disabled="groundTruthState === GroundTruthState.AllGroundTruth"
          @click="groundTruthState !== GroundTruthState.AllGroundTruth && toggleObs('model')"
        >
          <div
            class="layer-icon pl-1"
          >
            M
          </div>
          <div
            class="layer-text"
          >
            Model
          </div>
          <v-checkbox-btn
            :model-value="state.filters.drawObservations?.includes('model')"

            density="compact"
            :disabled="groundTruthState === GroundTruthState.AllGroundTruth"
            hide-details
            readonly
            class="item-checkbox"
          />
        </v-list-item>
        <v-list-item
          value="GroundTruth"
          :class="{'disabled-item': groundTruthState === GroundTruthState.NoGroundTruth}"
          :disabled="groundTruthState === GroundTruthState.NoGroundTruth"
          @click="toggleObs('groundtruth')"
        >
          <div
            class="layer-icon pl-1"
          >
            G
          </div>
          <div
            class="layer-text"
          >
            GroundTruth
          </div>
          <v-checkbox-btn
            :model-value="state.filters.drawObservations?.includes('groundtruth')"
            density="compact"
            :disabled="groundTruthState === GroundTruthState.NoGroundTruth"
            hide-details
            readonly
            class="item-checkbox"
          />
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
        :disabled="!modelRunEnabled"
        :variant="state.filters.drawSiteOutline ? undefined : 'text'"
        :color="state.filters.drawSiteOutline ? 'primary' : ''"
        style="min-width:150px"
        @click="toggleSite()"
      >
        <span>
          Sites
        </span>
        <div
          v-if="state.filters.drawSiteOutline?.includes('model')"
          class="layer-icon mx-1"
        >
          M
        </div>
        <div
          v-if="state.filters.drawSiteOutline?.includes('groundtruth')"
          class="layer-icon mx-1"
        >
          G
        </div>
        <div
          v-if="state.filters.siteTimeLimits"
          class="layer-icon mx-1"
        >
          T
        </div>
        <v-icon :color="state.filters.drawSiteOutline ? 'white' : 'black'">
          mdi-menu-down
        </v-icon>
      </v-btn>
    </template>
    <v-card outlined>
      <v-list>
        <v-list-item
          value="All"
          class="rootItem"
          @click="toggleSite()"
        >
          <v-row
            dense
            align="center"
            class="pa-0 ma-0"
          >
            <v-spacer />
            <v-checkbox
              :model-value="state.filters.drawSiteOutline?.includes('model') && state.filters.drawSiteOutline?.includes('groundtruth')"
              density="compact"
              hide-details
              class="item-checkbox"
            />
          </v-row>
        </v-list-item>
        <v-list-item
          value="Model"
          :class="{'disabled-item': groundTruthState === GroundTruthState.AllGroundTruth}"
          :disabled="groundTruthState === GroundTruthState.AllGroundTruth"
          @click="toggleSite('model')"
        >
          <div
            class="layer-icon pl-1"
          >
            M
          </div>
          <div
            class="layer-text"
          >
            Model
          </div>
          <v-checkbox-btn
            :model-value="state.filters.drawSiteOutline?.includes('model')"
            density="compact"
            hide-details
            :disabled="groundTruthState === GroundTruthState.AllGroundTruth"
            readonly
            class="item-checkbox"
          />
        </v-list-item>
        <v-list-item
          value="GroundTruth"
          :class="{'disabled-item': groundTruthState === GroundTruthState.NoGroundTruth}"
          :disabled="groundTruthState === GroundTruthState.NoGroundTruth"
          @click="toggleSite('groundtruth')"
        >
          <div
            class="layer-icon pl-1"
          >
            G
          </div>
          <div
            class="layer-text"
          >
            GroundTruth
          </div>
          <v-checkbox-btn
            :model-value="state.filters.drawSiteOutline?.includes('groundtruth')"
            density="compact"
            hide-details
            :disabled="groundTruthState === GroundTruthState.NoGroundTruth"
            readonly
            class="item-checkbox"
          />
        </v-list-item>
        <v-list-item
          value="GroundTruth"
          @click="toggleSiteTimeLimits()"
        >
          <div
            class="layer-icon pl-1"
          >
            T
          </div>

          <div
            class="layer-text"
          >
            Time Limits
          </div>
          <v-checkbox-btn
            :model-value="state.filters.siteTimeLimits"
            density="compact"
            hide-details
            readonly
            class="item-checkbox"
          />
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
  <v-tooltip
    text="Add Proposal"
    location="bottom"
  >
    <template #activator="{ props }">
      <v-btn
        v-if="proposals && annotation && !scoringApp"
        class="px-2 mx-2"
        v-bind="props"
        :variant="state.filters.addingSitePolygon && modelRunEnabled ? undefined : 'text'"
        :disabled="state.filters.addingSitePolygon || !modelRunEnabled"
        :color="state.filters.addingSitePolygon ? 'primary' : ''"
        @click="addProposal()"
      >
        <v-icon
          size="x-large"
          :color="state.filters.addingSitePolygon ? 'white' : ''"
        >
          mdi-vector-polygon
        </v-icon><v-icon>mdi-plus</v-icon>
      </v-btn>
    </template>
  </v-tooltip>
</template>

<style scoped>
.divider {
  width: 1px;              /* Divider thickness */
  height: 50px;            /* Full height of the parent */
  background-color: #000000;  /* Divider color */
  margin: 0 10px;          /* Optional spacing around the divider */

}
.button-label {
    font-size: 8px;
}

.layer-text {
  text-transform: uppercase;
  font-size: 16px;
  display: inline;
  margin-left: 5px;
}

.layer-icon {
  color: #FFFFFF !important;
  background-color: #37474F;
  min-width: 30px !important;
  width:30px !important;
  height: 30px !important;
  min-height: 30px !important;
  max-width: 30px !important;
  max-height: 30px !important;
  border-radius: 5px !important;
  font-size: 20px !important;
  text-align: center !important;
  font-weight: 800 !important;
  line-height: 30px !important;
  display: inline;
}

.rootItem {
  border-bottom: 1px solid gray;
  height: 35px;
}

.item-checkbox {
  display:inline;
  float:right;
}

.disabled-item {
  background-color: gray;
  color: lightgray;
  cursor:not-allowed;
}
</style>