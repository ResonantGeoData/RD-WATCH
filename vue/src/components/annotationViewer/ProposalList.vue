<script setup lang="ts">
import { Ref, ref, watch } from "vue";
import { ApiService } from "../../client";
import {
  DownloadSettings,
  Proposals,
  SiteModelStatus,
} from "../../client/services/ApiService";
import { state } from "../../store";
import { clickedInfo, hoveredInfo } from "../../interactions/mouseEvents";
import ImagesDownloadDialog from "../ImagesDownloadDialog.vue";

export interface ProposalDisplay {
  number: number;
  id: string;
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
  status: SiteModelStatus;
  timestamp: number;
  downloading: boolean;
}

const props = defineProps<{
  modelRun: string | null;
  selectedEval: string | null;
}>();
const emit = defineEmits<{
  (e: "selected", val: ProposalDisplay | null): void;
}>();

const proposalList: Ref<Proposals | null> = ref(null);
const modifiedList: Ref<ProposalDisplay[]> = ref([]);
const anyDownloading = ref(false);
const imageDownloadDialog = ref(false);
const imageTimeRange: Ref<{min: number, max: number} | null> = ref(null);
const imageDownloadingId: Ref<null | string> = ref(null)
let downloadCheckInterval: NodeJS.Timeout | null = null;

const statusMap: Record<SiteModelStatus, { name: string; color: string }> = {
  PROPOSAL: { name: "Proposed", color: "orange" },
  REJECTED: { name: "Rejected", color: "error" },
  APPROVED: { name: "Approved", color: "success" },
};

const getSiteProposals = async () => {
  if (props.modelRun !== null) {
    const results = await ApiService.getProposals(props.modelRun);
    proposalList.value = results;
    let newNumbers = 0;
    if (proposalList.value?.proposed_sites) {
      const modList: ProposalDisplay[] = [];
      const regionName: string = proposalList.value.region;
      const accepted: string[] = [];
      const rejected: string[] = [];
      proposalList.value.proposed_sites.forEach((item) => {
        const newNum = item.number.toString().padStart(4, "0");
        if (newNum === "9999") {
          newNumbers += 1;
        }
        let name = `${regionName}_${newNum}`;
        if (newNumbers > 1) {
          name = `${name}-${newNumbers}`;
        }
        if (item.status === "APPROVED") {
          accepted.push(item.id);
        } else if (item.status === "REJECTED") {
          rejected.push(item.id);
        }
        if (item.downloading) {
          anyDownloading.value = true;
        }
        modList.push({
          number: item.number,
          id: item.id,
          name,
          filename: item.filename,
          bbox: item.bbox,
          selected: item.id === props.selectedEval,
          images: item.images,
          startDate: item.start_date,
          endDate: item.end_date,
          S2: item.S2,
          WV: item.WV,
          L8: item.L8,
          PL: item.PL,
          status: item.status,
          timestamp: item.timestamp,
          downloading: item.downloading,
        });
      });
      state.filters.proposals = {
        accepted,
        rejected,
      };
      modifiedList.value = modList;
      // We need to start checking if there are downloading sites to update every once in a while
      if (anyDownloading.value) {
        downloadCheckInterval = setInterval(() => getSiteProposals(), 15000);
      } else {
        if (downloadCheckInterval !== null) {
          clearInterval(downloadCheckInterval);
        }
      }

    }
  }
};
defineExpose({ getSiteProposals });

watch(
  () => props.modelRun,
  () => {
    getSiteProposals();
  }
);
getSiteProposals();
watch(clickedInfo, () => {
  if (clickedInfo.value.siteId.length) {
    const found = modifiedList.value.find(
      (item) => item.id === clickedInfo.value.siteId[0]
    );
    if (found) {
      emit("selected", found);
    }
  } else {
    emit("selected", null);
  }
});

const download = (id: string) => {
  const url = `/api/evaluations/${id}/download`;
  window.location.assign(url);
};

watch(() => hoveredInfo.value.siteId, () => {
  if (hoveredInfo.value.siteId.length) {
    const id = hoveredInfo.value.siteId[0];
    const el = document.getElementById(`proposal-id-${id}`);
    if (el) {
      el.scrollIntoView({block: 'end', behavior: 'smooth'});
    }
  }
});
const setImageDownloadDialog = (item: ProposalDisplay) => {
  if (item.startDate && item.endDate) {
    imageTimeRange.value = {
      min: item.startDate,
      max: item.endDate,
    }
  } else {
    imageTimeRange.value = null;
  }
  imageDownloadDialog.value = true;
  imageDownloadingId.value = item.id;
};

const startDownload = async (data: DownloadSettings) => {
  const id = imageDownloadingId.value;
  imageDownloadDialog.value = false;
  if (id) {
  await ApiService.getObservationImages(id, data);
    // Now we get the results to see if the service is running
    getSiteProposals(); // this will start the interval if downloading items are detected
  }
}

</script>

<template>
  <v-card class="pb-5 proposal-list">
    <div v-if="modelRun === null">
      Select a Model Run to display Site Models
    </div>
    <div v-else>
      <h3>Site Models:</h3>
      <v-card
        v-for="item in modifiedList"
        :id="`proposal-id-${item.id}`"
        :key="`${item.name}_${item.id}_${item.selected}`"
        class="modelRunCard"
        :class="{
          selectedCard: item.id === selectedEval,
          hoveredCard: hoveredInfo.siteId.includes(item.id),
        }"
        @mouseenter="state.filters.hoverSiteId = item.id"
        @mouseleave="state.filters.hoverSiteId = undefined"
        @click="emit('selected', item)"
      >
        <v-card-title class="title">
          {{ item.name }}
        </v-card-title>
        <v-card-text>
          <v-row
            dense
            justify="center"
          >
            <div v-if="item.images">
              <v-chip size="x-small">
                WV: {{ item.WV }}
              </v-chip>
              <v-chip size="x-small">
                S2: {{ item.S2 }}
              </v-chip>
              <v-chip size="x-small">
                L8: {{ item.L8 }}
              </v-chip>
              <v-chip size="x-small">
                PL: {{ item.PL }}
              </v-chip>
            </div>
            <div v-else>
              <v-chip
                size="x-small"
                color="error"
              >
                No Images Loaded
              </v-chip>
            </div>
          </v-row>
          <v-row
            dense
            justify="center"
            class="pa-2"
          >
            <v-chip
              v-if="item.status"
              size="small"
              :color="statusMap[item.status].color"
            >
              {{ statusMap[item.status].name }}
            </v-chip>
          </v-row>
          <v-row dense>
            <v-tooltip open-delay="300">
              <template #activator="{ props: subProps }">
                <v-btn
                  size="x-small"
                  v-bind="subProps"
                  @click.stop="download(item.id)"
                >
                  <v-icon size="small">
                    mdi-export
                  </v-icon>
                </v-btn>
              </template>
              <span>Download JSON</span>
            </v-tooltip>
            <v-spacer />
            <v-tooltip open-delay="300">
              <template #activator="{ props:subProps }">
                <v-btn
                  v-if="!item.downloading"
                  size="x-small"
                  v-bind="subProps"
                  class="mx-1"
                  @click.stop="setImageDownloadDialog(item)"
                >
                  Get <v-icon>mdi-image</v-icon>
                </v-btn>
                <v-btn
                  v-else-if="item.downloading"
                  size="x-small"
                  v-bind="subProps"
                  class="mx-1"
                >
                  <v-icon>mdi-spin mdi-sync</v-icon>
                </v-btn>
              </template>
              <span> {{ item.downloading ? 'Downloading Images' : 'Download Satellite Images' }} </span>
            </v-tooltip>
            <v-spacer />
            <v-tooltip
              v-if="item.filename"
              open-delay="0"
              bottom
            >
              <template #activator="{ props: subProps }">
                <v-icon
                  x-small
                  v-bind="subProps"
                >
                  mdi-file-outline
                </v-icon>
              </template>
              <span>
                {{ item.filename }}
              </span>
            </v-tooltip>
          </v-row>
        </v-card-text>
      </v-card>
      <images-download-dialog
        v-if="imageDownloadDialog"
        :date-range="imageTimeRange"
        @download="startDownload($event)"
        @cancel="imageDownloadDialog = false"
      />
    </div>
  </v-card>
</template>

<style scoped>
.modelRunCard {
  border: 3px solid transparent;
}
.modelRunCard:hover {
  cursor: pointer;
  border: 3px solid blue;
}

.title {
  font-size: 12px;
}
.errorCard {
  background-color: lightcoral;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hoveredCard {
  background-color: orange;
  border: 3px solid orange;
}

.proposal-list {
  position: sticky;
  top: 0px;
  z-index: 2;
  background-color: white;
  overflow-y: auto;
}
.selectedCard {
  background-color: lightblue;
}

</style>
