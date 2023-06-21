<script setup lang="ts">
import TimeSlider from "./TimeSlider.vue";
import { ApiService, ModelRun } from "../client";
import { state } from "../store";
import { ref } from "vue";

const props = defineProps<{
  modelRun: ModelRun;
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "toggle"): void;
}>();

async function handleClick() {
  emit("toggle");
}

const useScoring = ref(false);

async function getScoringColoring() {
  if (!useScoring.value) { // inverted value because of the delay
    const results = await ApiService.getScoreColoring(props.modelRun.id, props.modelRun.region?.id || 0)
    let tempResults = state.filters.scoringColoring;
    if (!tempResults) {
      tempResults = {};
    }
    if (tempResults !== undefined && tempResults !== null)  {
      tempResults[`${props.modelRun.id}_${props.modelRun.region?.id || 0}`] = results;
    }
    state.filters = { ...state.filters, scoringColoring: tempResults };
  } else {
    let tempResults = state.filters.scoringColoring;
    if (tempResults) {
      if (Object.keys(tempResults).includes(`${props.modelRun.id}_${props.modelRun.region?.id || 0}`)) {
        delete tempResults[`${props.modelRun.id}_${props.modelRun.region?.id || 0}`];
      }
      if (Object.values(tempResults).length === 0) {
        tempResults = null;
      }
    }
    state.filters = { ...state.filters, scoringColoring: tempResults };
  }
}
</script>

<template>
  <v-card
    outlined
    class="my-3 modelRunCard"
    :class="{selectedCard: props.open}"
  >
    <v-card-text
      @click.prevent="handleClick"
    >
      <v-row dense>
        <div class="model-title">
          {{ modelRun.title }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          region:
        </div>
        <div>
          {{ modelRun.region?.name || "(none)" }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          last updated:
        </div>
        <div>
          {{
            modelRun.timestamp === null
              ? "--"
              : new Date(modelRun.timestamp * 1000).toLocaleString()
          }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          number of sites:
        </div>
        <div>
          {{ modelRun.numsites }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          average score:
        </div>
        <div>
          {{ modelRun.score === null ? "--" : modelRun.score.toFixed(2) }}
        </div>
      </v-row>
      <v-row dense>
        <div>
          date coverage:
        </div>
        <div>
          {{
            modelRun.timerange === null
              ? "--"
              : `${new Date(modelRun.timerange.min * 1000).toLocaleString(
                "en",
                {
                  dateStyle: "short",
                }
              )} - ${new Date(modelRun.timerange.max * 1000).toLocaleString(
                "en",
                {
                  dateStyle: "short",
                }
              )}`
          }}
        </div>
      </v-row>
      <v-row dense>
        <v-icon
          v-if="modelRun.performer.short_code === 'TE' && modelRun.score == 1"
          color="rgb(37, 99, 235)"
        >
          mdi-check-decagram
        </v-icon>
        <div
          class="float-right "
        >
          {{ modelRun.performer.short_code }}
        </div>
      </v-row>
      <v-row
        v-if="modelRun.hasScores && props.open"
        dense
      >
        <input
          v-model="useScoring"
          type="checkbox"
          @click.stop="getScoringColoring()"
        >
        <span class="ml-2"> Scoring Coloring</span>
      </v-row>
    </v-card-text>
    <v-card-actions v-if="open">
      <TimeSlider
        :min="modelRun.timerange?.min || 0"
        :max="modelRun.timerange?.max || 0"
      />
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.modelRunCard{
  border: 3px solid transparent;
}
.modelRunCard:hover {
  cursor: pointer;
  border: 3px solid blue;
}
.selectedCard{
  background-color: lightblue;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
