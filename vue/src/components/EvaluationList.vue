<script setup lang="ts">
import { ApiService, SiteObservation } from "../client";
import { map } from "../map";
import { LngLatBounds } from "maplibre-gl";
import { computed, ref, watch, watchEffect } from "vue";
import type { SiteEvaluation } from "../client";
import type { Ref } from "vue";

const evaluations: Ref<Array<SiteEvaluation>> = ref([]);
const observations: Ref<Array<SiteObservation>> = ref([]);

const mouseInPanel: Ref<boolean> = ref(false);
const mouseInFocus: Ref<boolean> = ref(false);

const hoveredEvaluationIdx: Ref<number | undefined> = ref(undefined);
const hoveredEvaluation = computed(() =>
  hoveredEvaluationIdx.value === undefined
    ? undefined
    : evaluations.value[hoveredEvaluationIdx.value]
);

const focusedEvaluationIdx: Ref<number | undefined> = ref(undefined);
const focusedEvaluation = computed(() =>
  focusedEvaluationIdx.value === undefined
    ? undefined
    : evaluations.value[focusedEvaluationIdx.value]
);

const selectedObservationIdx: Ref<number | undefined> = ref(undefined);
const selectedObservation = computed(() =>
  selectedObservationIdx.value === undefined
    ? undefined
    : observations.value[selectedObservationIdx.value]
);

const loadEvaluations = () => {
  ApiService.getSiteEvaluations().then((evl) => {
    evaluations.value = evl;
  });
};

const loadObservations = (evaluation: SiteEvaluation) => {
  ApiService.getSiteObservations(evaluation.id.toString()).then((obs) => {
    observations.value = obs;
    selectedObservationIdx.value = 0;
  });
};

const setSiteHighlight = (evaluation: SiteEvaluation, value: boolean) => {
  map.setFeatureState(
    {
      source: "all-sites",
      sourceLayer: "default",
      id: evaluation.id,
    },
    { hover: value }
  );
};

const setSiteFocus = (evaluation: SiteEvaluation, value: boolean) => {
  map.setFeatureState(
    {
      source: "all-sites",
      sourceLayer: "default",
      id: evaluation.id,
    },
    { focus: value }
  );
};

const setObservationSelected = (
  observation: SiteObservation,
  value: boolean
) => {
  map.setFeatureState(
    {
      source: "observations",
      sourceLayer: "default",
      id: observation.id,
    },
    { selected: value }
  );
};

const addObservationLayers = (evaluation: SiteEvaluation) => {
  map.addSource("observations", {
    type: "vector",
    tiles: [
      `${location.protocol}//${location.host}/api/site/${evaluation.id}/tile/{z}/{x}/{y}.pbf`,
    ],
    maxzoom: 14,
  });
  map.addLayer({
    id: "observations",
    type: "fill",
    source: "observations",
    "source-layer": "default",
    paint: {
      "fill-color": [
        "interpolate-lab",
        ["linear"],
        ["get", "score"],
        0,
        "#FF0000",
        1,
        "#00FF00",
      ],
      "fill-opacity": [
        "case",
        ["boolean", ["feature-state", "selected"], false],
        0.2,
        0,
      ],
    },
  });
};

const removeObservationLayers = () => {
  map.removeLayer("observations");
  map.removeSource("observations");
};

const flyTo = (evaluation: SiteEvaluation) => {
  map.fitBounds(
    LngLatBounds.convert(evaluation.bbox as [number, number, number, number]),
    {
      padding: 160,
      offset: [80, 0],
    }
  );
};

const setSiteOverviewVisiblity = (value: boolean) => {
  const visibility = value ? "visible" : "none";
  map.getLayer("site-background").visibility = visibility;
  map.getLayer("site-hover").visibility = visibility;
};

watch(mouseInPanel, (value) => {
  if (!value && focusedEvaluation.value !== undefined) {
    setSiteOverviewVisiblity(false);
  }
});

watch(mouseInFocus, () => setSiteOverviewVisiblity(false));

watch(hoveredEvaluation, (value, prior) => {
  if (prior !== undefined) {
    setSiteHighlight(prior, false);
  }
  if (value !== undefined) {
    setSiteHighlight(value, true);
    if (value.id !== focusedEvaluation.value?.id) {
      setSiteOverviewVisiblity(true);
    }
  } else if (
    focusedEvaluation.value !== undefined &&
    (mouseInFocus.value || !mouseInPanel.value)
  ) {
    setSiteOverviewVisiblity(false);
  }
});

watch(focusedEvaluation, (value, prior) => {
  if (prior !== undefined) {
    setSiteFocus(prior, false);
    removeObservationLayers();
  }
  if (value !== undefined) {
    loadObservations(value);
    addObservationLayers(value);
    setSiteFocus(value, true);
    flyTo(value);
    setSiteOverviewVisiblity(false);
  } else {
    setSiteOverviewVisiblity(true);
  }
});

watch(focusedEvaluationIdx, (value, prior) => {
  if (value === undefined) {
    selectedObservationIdx.value = undefined;
    observations.value = [];
    hoveredEvaluationIdx.value = prior;
  }
});

watch(selectedObservation, (value, prior) => {
  if (value !== undefined) {
    if (prior !== undefined) {
      setObservationSelected(prior, false);
    }
    setObservationSelected(value, true);
  }
});

watchEffect(() => {
  loadEvaluations();
});
</script>

<template>
  <div
    class="grid h-full justify-center justify-items-stretch overflow-y-scroll"
    @mouseover.stop="mouseInPanel = true"
    @mouseleave.stop="mouseInPanel = false"
  >
    <div
      v-for="(evaluation, idx) in evaluations"
      :key="evaluation.id"
      class="pt-4"
    >
      <div
        v-if="focusedEvaluationIdx === idx"
        class="rounded-lg border-2 border-solid border-blue-600"
        @mouseover.stop="mouseInFocus = true"
        @mouseleave.stop="mouseInFocus = false"
      >
        <button
          class="relative h-24 w-72 rounded-t-md bg-blue-600 p-2"
          @mouseover.stop="hoveredEvaluationIdx = idx"
          @mouseleave.stop="hoveredEvaluationIdx = undefined"
          @click="focusedEvaluationIdx = undefined"
        >
          <div class="grid grid-cols-2">
            <div
              class="col-span-1 text-left font-mono text-lg font-bold text-white"
            >
              {{ evaluation.site }}
            </div>
            <div class="col-span-1 text-right text-xs font-light text-gray-100">
              [site]
            </div>
            <div class="col-span-1 text-left text-sm font-light text-white">
              {{ evaluation.timestamp }}
            </div>
            <div class="col-span-1 text-right text-xs font-light text-gray-100">
              [completion]
            </div>
          </div>
          <div
            class="absolute bottom-1 right-2 rounded bg-gray-100 pl-1 pr-1 text-xs text-blue-600"
          >
            {{ evaluation.performer.short_code }}
          </div>
        </button>
        <div class="p-4 text-center">
          <input
            v-model="selectedObservationIdx"
            type="range"
            min="0"
            :disabled="observations.length < 2"
            :max="observations.length - 1"
          />
          <p class="text-center text-sm font-light">
            {{ selectedObservation?.timestamp }}
          </p>
          <div class="grid grid-cols-4">
            <div class="col-span-1 text-left text-sm font-light text-gray-600">
              score:
            </div>
            <div class="col-span-3 text-left font-mono text-sm">
              {{ selectedObservation?.score }}
            </div>
            <div class="col-span-1 text-left text-sm font-light text-gray-600">
              label:
            </div>
            <div class="col-span-3 text-left font-mono text-sm">
              {{ selectedObservation?.label }}
            </div>
            <div class="col-span-1 text-left text-sm font-light text-gray-600">
              source:
            </div>
            <div class="col-span-3 text-left font-mono text-sm">
              {{ selectedObservation?.constellation }}
            </div>
          </div>
        </div>
      </div>

      <button
        v-else
        class="relative h-24 w-72 rounded-md bg-gray-50 p-2 hover:bg-gray-200"
        @mouseover="hoveredEvaluationIdx = idx"
        @mouseleave="hoveredEvaluationIdx = undefined"
        @click="focusedEvaluationIdx = idx"
      >
        <div class="grid grid-cols-2">
          <div class="col-span-1 text-left font-mono text-lg font-bold">
            {{ evaluation.site }}
          </div>
          <div class="col-span-1 text-right text-xs font-light text-gray-400">
            [site]
          </div>
          <div class="col-span-1 text-left text-sm font-light">
            {{ evaluation.timestamp }}
          </div>
          <div class="col-span-1 text-right text-xs font-light text-gray-400">
            [completion]
          </div>
        </div>
        <div
          class="absolute bottom-1 right-2 rounded bg-gray-400 pl-1 pr-1 text-xs text-white"
        >
          {{ evaluation.performer.short_code }}
        </div>
      </button>
    </div>
  </div>
</template>
