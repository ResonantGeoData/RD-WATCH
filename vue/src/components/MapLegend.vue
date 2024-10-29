<script setup lang="ts">

import { annotationLegend } from '../mapstyle/annotationStyles';
import { state } from '../store';

</script>

<template>
  <div
    v-if="state.mapLegend && (state.filters.drawObservations || state.filters.drawSiteOutline || state.filters.scoringColoring)"
    class="legend"
  >
    <v-card
      density="compact"
      class="legend-base"
    >
      <v-card-title>
        <v-row
          align="center"
          class="px-4"
        >
          <span
            :class="{'legend-title-single': !state.filters.scoringColoring, 'legend-title': state.filters.scoringColoring}"
          >Legend</span>
          <v-spacer />
          <v-col cols="1">
            <v-icon
              size="small"
              @click="state.mapLegend = false"
            >
              mdi-close-circle
            </v-icon>
          </v-col>
        </v-row>
      </v-card-title>
      <v-card-text class="legend-card-text">
        <v-row dense>
          <v-card
            v-if="state.filters.drawSiteOutline && !state.filters.scoringColoring"
            density="compact"
            class="white"
          >
            <v-card-title
              class="legend-title"
            >
              Site Models
            </v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col>
                  <v-row
                    v-for="item in annotationLegend.siteLegend"
                    :key="item.name"
                    align="center"
                    class="px-5"
                  >
                    <span
                      :style="`background-color: ${item.color}`"
                      class="color-icon pr-1"
                    />
                    <span
                      class="pl-1 legend-label"
                    >
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card
            v-if="state.filters.drawObservations"
            density="compact"
          >
            <v-card-title
              class="legend-title"
            >
              Site Observations
            </v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col>
                  <v-row
                    v-for="item in annotationLegend.observationLegend"
                    :key="item.name"
                    align="center"
                    class="px-5"
                  >
                    <span
                      :style="`background-color: ${item.color}`"
                      class="color-icon pr-1"
                    />
                    <span
                      class="pl-1 legend-label"
                    >
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
          <v-card
            v-if="state.filters.scoringColoring"
            density="compact"
          >
            <v-card-title class="legend-title">
              Scoring
            </v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col>
                  <v-row
                    v-for="item in annotationLegend.scoringLegend"
                    :key="item.name"
                    align="center"
                    class="px-5"
                  >
                    <span
                      :style="`background-color: ${item.color}`"
                      class="color-icon pr-1"
                    />
                    <span class="pl-1 legend-label">
                      :{{ item.name }}
                    </span>
                  </v-row>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<style>
.legend {
  max-width: 400px;
}
.legend-title {
  font-size:1.0em !important;
}
.legend-label {
  font-size: 0.75em;
}
.color-icon {
  min-width: 15px;
  max-width: 15px;
  min-height: 15px;
  max-height: 15px;;
}
.legend-card-text {
  background-color: white;
  opacity: 1.0 !important;
}
.legend-base {
  opacity: 0.75;
  background-color: #FFFFFFBB
}
</style>
