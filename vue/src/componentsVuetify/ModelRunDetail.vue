<script setup lang="ts">
import TimeSlider from "./TimeSlider.vue";
import type { ModelRun } from "../client";
import { CheckBadgeIcon } from "@heroicons/vue/24/solid";

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
</script>

<template>
  <v-card
    outlined
    :open="props.open"
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
        <CheckBadgeIcon
          v-if="modelRun.performer.short_code === 'TE' && modelRun.score == 1"
          class="hover h-5 text-blue-600 mt-0.5"
        />
        <div
          class="float-right mt-1 rounded bg-gray-400 pl-1 pr-1 group-open:bg-gray-100"
        >
          {{ modelRun.performer.short_code }}
        </div>
      </v-row>
    </v-card-text>
    <v-card-actions>
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
