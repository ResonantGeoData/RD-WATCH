<script setup lang="ts">
import {
  SiteModelStatus,
} from "../../client/services/ApiService";
import { state } from "../../store";
import { clickedInfo, hoveredInfo } from "../../interactions/mouseEvents";
import { timeRangeFormat } from "../../utils";

export interface SiteDisplay {
  number: number;
  id: string;
  uuid?: string;
  name: string;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  startDate: number;
  endDate: number;
  selected: boolean;
  filename?: string | null;
  images: number;
  S2: number;
  WV: number;
  L8: number;
  PL: number;
  status?: SiteModelStatus;
  timestamp: number;
  downloading: boolean;
  proposal?: boolean;
  details?: {
    performer: string;
    version: string;
    region: string;
    title: string;
  };
}

const props = defineProps<{
    site: SiteDisplay;
    selectedEval: string | null;
}>();
const emit = defineEmits<{
  (e: "selected", val: SiteDisplay | null): void;
  (e: "clicked", { uuid } : { uuid: string }): void;
  (e: "image-download", val: SiteDisplay): void;
}>();

const statusMap: Record<SiteModelStatus, { name: string; color: string, icon: string }> = {
  PROPOSAL: { name: "Proposed", color: "orange", icon: "mdi-dots-horizontal-circle" },
  REJECTED: { name: "Rejected", color: "error", icon: "mdi-alert-circle" },
  APPROVED: { name: "Approved", color: "success", icon: "mdi-check-circle" },
};


const download = (id: string) => {
  const url = `/api/evaluations/${id}/download`;
  window.location.assign(url);
};

const setImageDownloadDialog = () => {
    emit('image-download', props.site)
};

</script>

<template>
      <v-card
      variant="flat"
        :id="`site-id-${site.id}`"
        :key="`${site.name}_${site.id}_${site.selected}`"
        class="siteCard"
        :class="{
          selectedCard: site.id === selectedEval,
          hoveredCard: hoveredInfo.siteId.includes(site.id),
        }"
        @mouseenter="state.filters.hoverSiteId = site.id"
        @mouseleave="state.filters.hoverSiteId = undefined"
        @click="emit('selected', site)"
      >
        <v-card-title class="title">
            <v-row dense>
                <v-col><span> {{  site.name }}</span></v-col>
                <v-spacer />
                <v-col v-if="site.status" cols="1" class="mr-4" >
                  <v-tooltip
              open-delay="0"
              bottom
            >
              <template #activator="{ props }">

                    <v-icon 
                        size="20"
                        class="pa-0 ma-0 site-icon"
                        :color="statusMap[site.status].color"
                        v-bind="props"
                        >
                        {{  statusMap[site.status].icon }}
                    </v-icon>
                  </template>
                  <span> {{ statusMap[site.status].name }} </span>
                </v-tooltip>

                </v-col>
            </v-row>
        </v-card-title>
        <v-card-text>
          <v-row v-if="!site.proposal && site.details" dense>
            <span class="site-model-info"> {{ site.details.performer }} {{ site.details.title}}: {{site.details.version}} </span>
          </v-row>
          <v-row v-if="!site.proposal" dense>
            <span>Date range:</span><span class=" ml-1 site-model-dates"> {{ timeRangeFormat({min: site.startDate, max: site.endDate })}} </span>
          </v-row>

          <v-row
          v-if="site.images"
            dense
          >
            <v-col>
                <span class="image-label">WV:</span>
                <span class="image-value">{{ site.WV }}</span>
                <span class="image-line" />
            </v-col>
            <v-col>
                <span class="image-label">S2:</span>
                <span class="image-value">{{ site.S2 }}</span>
                <span class="image-line" />
            </v-col>
            <v-col>
                <span class="image-label">L8:</span>
                <span class="image-value">{{ site.L8 }}</span>
                <span class="image-line" />
            </v-col>
            <v-col>
                <span class="image-label">PL:</span>
                <span class="image-value">{{ site.PL || 0 }}</span>
              
            </v-col>
          </v-row>
          <v-row v-else align="center">
            <span class="no-images">No Images Downloaded</span>
          </v-row>
          <v-row dense class=pt-2>
            <v-tooltip
              v-if="site.filename"
              open-delay="0"
              bottom
            >
              <template #activator="{ props }">
                <v-icon
                  size="small"
                  class="pa-0 ma-1 site-icon"
                  v-bind="props"
                >
                  mdi-file-question-outline
                </v-icon>
              </template>
              <span>
                {{ site.filename }}
              </span>
            </v-tooltip>
            <v-spacer />
            <v-tooltip open-delay="300">
              <template #activator="{ props }">
                <v-btn
                  variant="tonal"
                  density="compact"
                  class="pa-0 ma-1 site-icon"
                  size="small"
                  color="primary"
                  v-bind="props"
                  @click.stop="download(site.id)"
                >
                  <v-icon size="small">
                    mdi-export
                  </v-icon>
                </v-btn>
              </template>
              <span>Download JSON</span>
            </v-tooltip>
            <v-tooltip open-delay="300">
              <template #activator="{ props }">
                <v-btn
                  v-if="!site.downloading"
                  variant="tonal"
                  density="compact"
                  class="pa-0 ma-1 site-icon"
                  size="small"
                  color=primary
                  v-bind="props"
                  @click.stop="setImageDownloadDialog()"
                >
                  <v-icon>mdi-image</v-icon>
                </v-btn>
                <v-btn
                  v-else-if="site.downloading"
                  variant="tonal"
                  density="compact"
                  class="pa-0 ma-1 site-icon"
                  size="xmall"
                  v-bind="props"
                >
                  <v-icon>mdi-spin mdi-sync</v-icon>
                </v-btn>
              </template>
              <span> {{ site.downloading ? 'Downloading Images' : 'Download Satellite Images' }} </span>
            </v-tooltip>
          </v-row>
        </v-card-text>
      </v-card>
</template>

<style scoped>
.siteCard {
  border: 3px solid transparent;
  border-bottom: 1px solid gray;
}
.siteCard:hover {
  cursor: pointer;
  border: 3px solid #188DC8;
}

.title {
  font-size: 12px;
}

.errorCard {
  background-color: lightcoral;
}

.hoveredCard {
  background-color: orange;
  border: 3px solid orange;
}

.selectedCard {
  background-color: #e8f1f8;
}

.image-label {
  font-size: 11px;
  color: gray;
}
.image-value {
  font-size: 11px;
  color: black;
  font-weight: bolder;
}
.image-line {
  margin-left: 5px;
  border-right: 1px solid gray;
}
.site-icon {
  min-width: 25px;
  min-height: 25px;;
}
.no-images {
  font-size:14px;
  color: red;
}
.site-model-info {
  font-size: 12px;
}
.site-dates-label {
  color: gray
}
.site-model-dates {
  font-size: 10px;
}
</style>
