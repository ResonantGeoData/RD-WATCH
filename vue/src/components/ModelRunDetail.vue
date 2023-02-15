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
  <details
    class="group relative rounded-lg border-2 border-gray-50 open:border-blue-600 hover:border-gray-200 open:hover:border-blue-600"
    :open="props.open"
  >
    <summary
      class="cursor-pointer select-none list-none bg-gray-50 p-2 group-open:bg-blue-600 group-hover:bg-gray-200 group-open:group-hover:bg-blue-600"
      @click.prevent="handleClick"
    >
      <div class="grid grid-cols-8">
        <div class="col-span-8 group-open:text-white">
          <div class="modelTitle">
            {{ modelRun.title }}
          </div>
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          region:
        </div>
        <div
          class="col-span-5 font-mono text-xs font-light group-open:text-white"
        >
          {{ modelRun.region?.name || "(none)" }}
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          last updated:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{
            modelRun.timestamp === null
              ? "--"
              : new Date(modelRun.timestamp * 1000).toLocaleString()
          }}
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          number of sites:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{ modelRun.numsites }}
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          average score:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
          {{ modelRun.score === null ? "--" : modelRun.score.toFixed(2) }}
        </div>
        <div
          class="col-span-3 text-xs font-light text-gray-600 group-open:text-gray-100"
        >
          date coverage:
        </div>
        <div class="col-span-5 text-xs font-light group-open:text-white">
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
        <div class="col-span-8 pt-2"></div>
        <div
          class="tooltip tooltip-right col-span-1 h-5 w-5 text-xs text-lime-600 group-open:text-white"
          data-tip="Ground Truth"
        >
          <CheckBadgeIcon
            v-if="modelRun.performer.short_code === 'TE' && modelRun.score == 1"
          />
        </div>
        <div
          class="col-span-7 rounded text-right text-xs text-gray-50 group-open:text-blue-600"
        >
          <div
            class="float-right mt-1 rounded bg-gray-400 pl-1 pr-1 group-open:bg-gray-100"
          >
            {{ modelRun.performer.short_code }}
          </div>
        </div>
      </div>
    </summary>
    <div class="grid grid-cols-4 p-2">
      <div class="col-span-4">
        <TimeSlider
          :min="modelRun.timerange?.min || 0"
          :max="modelRun.timerange?.max || 0"
        />
      </div>
    </div>
  </details>
</template>

<style scoped>
.modelTitle {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
