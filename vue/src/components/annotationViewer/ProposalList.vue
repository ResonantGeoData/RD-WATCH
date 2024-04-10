<script setup lang="ts">
import { Ref, ref, watch } from "vue";
import { ApiService } from "../../client";
import {
  DownloadSettings,
  SiteList,
} from "../../client/services/ApiService";
import { state } from "../../store";
import { clickedInfo, hoveredInfo } from "../../interactions/mouseEvents";
import ImagesDownloadDialog from "../ImagesDownloadDialog.vue";
import SiteListCard from "../siteList/SiteListCard.vue";
import { SiteDisplay } from "../siteList/SiteListCard.vue";
import SiteListHeader from "../siteList/SiteListHeader.vue";

const props = defineProps<{
  modelRun: string | null;
  selectedEval: string | null;
}>();
const emit = defineEmits<{
  (e: "selected", val: SiteDisplay | null): void;
}>();

const proposalList: Ref<SiteList | null> = ref(null);
const baseModifiedList: Ref<SiteDisplay[]> = ref([]);
const modifiedList: Ref<SiteDisplay[]> = ref([]);
const imageDownloadDialog = ref(false);
const imageTimeRange: Ref<{min: number, max: number} | null> = ref(null);
const imageDownloadingId: Ref<null | string> = ref(null)
const filter = ref("");

const getSiteProposals = async () => {
  if (props.modelRun !== null) {
    const results = await ApiService.getProposals(props.modelRun);
    proposalList.value = results;
    let newNumbers = 0;
    if (proposalList.value?.sites) {
      const modList: SiteDisplay[] = [];
      const regionName: string = proposalList.value.region;
      const accepted: string[] = [];
      const rejected: string[] = [];
      let selected: SiteDisplay | null = null;
      const details = proposalList.value.modelRunDetails ? {
        title: proposalList.value.modelRunDetails.title,
        version: proposalList.value.modelRunDetails.version,
        performer: proposalList.value.modelRunDetails.performer.short_code,
        region: proposalList.value.modelRunDetails.region,
        proposal: proposalList.value.modelRunDetails.proposal,
      } : undefined
      proposalList.value.sites.forEach((item) => {
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
          details,
          proposal: !!details?.proposal,
        });
        if (item.id === props.selectedEval) {
          selected = modList[modList.length - 1];
        }
      });
      state.filters.proposals = {
        accepted,
        rejected,
      };
      modifiedList.value = modList;
      baseModifiedList.value = modList;
      // We need to start checking if there are downloading sites to update every once in a while
      if (selected) {
        emit('selected', selected);
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


watch(() => hoveredInfo.value.siteId, () => {
  if (hoveredInfo.value.siteId.length) {
    const id = hoveredInfo.value.siteId[0];
    const el = document.getElementById(`site-id-${id}`);
    if (el) {
      el.scrollIntoView({block: 'end', behavior: 'smooth'});
    }
  }
});
const setImageDownloadDialog = (item: SiteDisplay) => {
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
    setTimeout(() => getSiteProposals(), 500);
  }
}
watch(filter, () => {
  if (filter.value) {
    modifiedList.value = baseModifiedList.value.filter((item) => item.name.includes(filter.value))
  } else {
    modifiedList.value = baseModifiedList.value;
  }
});

</script>

<template>
  <v-card class="pb-5">
    <v-card-title><h5>Site Models</h5></v-card-title>
    <site-list-header v-model="filter" />
    <div class="proposal-list">
      <site-list-card
        v-for="item in modifiedList"
        :key="item.id"
        :site="item"
        :selected-eval="selectedEval"
        @selected="emit('selected', item)"
        @image-download="setImageDownloadDialog($event)"
      />
    </div>
    <images-download-dialog
      v-if="imageDownloadDialog"
      :date-range="imageTimeRange"
      @download="startDownload($event)"
      @cancel="imageDownloadDialog = false"
    />
  </v-card>
</template>

<style scoped>

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


.proposal-list {
  position: sticky;
  top: 0px;
  z-index: 2;
  background-color: white;
  overflow-y: auto;
  max-height: calc(100vh - 150px);
}

</style>
