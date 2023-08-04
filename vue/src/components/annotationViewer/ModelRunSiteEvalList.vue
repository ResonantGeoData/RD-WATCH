<script setup lang="ts">
import { Ref, computed, ref, watch } from "vue";
import { ApiService } from "../../client";
import { ModelRunEvaluations, SiteModelStatus } from "../../client/services/ApiService";

export interface ModelRunEvaluationDisplay {
  number: number;
  id: number;
  name: string;
  bbox: { xmin: number; ymin: number; xmax: number; ymax: number };
  startDate: number,
  endDate: number,
  selected:boolean;
  images: number;
  S2: number;
  WV: number,
  L8: number;
  status: SiteModelStatus;
  timestamp: number;
}


const props = defineProps<{
  modelRun: number | null;
  selectedEval: number | null;
}>();

const emit = defineEmits<{
  (e: "selected", val: ModelRunEvaluationDisplay): void;
}>();

const evaluationsList: Ref<ModelRunEvaluations | null> = ref(null);

const statusMap: Record<SiteModelStatus, { name: string, color: string }> = {
  'PROPOSAL': { name: 'Proposed', color: 'orange'},
  'REJECTED': { name: 'Rejected', color: 'error'},
  'APPROVED': { name: 'Approved', color: 'success'},
  
}

const getSiteEvalIds = async () => {
  if (props.modelRun !== null) {
    const results = await ApiService.getModelRunEvaluations(props.modelRun);
    evaluationsList.value = results;
  }
};

defineExpose({ getSiteEvalIds });

watch(() => props.modelRun, () => {
  getSiteEvalIds();
});
getSiteEvalIds();

const modifiedList = computed(() => {
  const modList: ModelRunEvaluationDisplay[] = []
  if (evaluationsList.value?.evaluations) {
    const regionName = evaluationsList.value.region.name;
    evaluationsList.value.evaluations.forEach((item) => {
      const newNum = item.number.toString().padStart(4, '0')
      modList.push(
        {
          number: item.number, id: item.id, name: `${regionName}_${newNum}`,
          bbox: item.bbox,
          selected: item.id === props.selectedEval,
          images: item.images,
          startDate: item.start_date,
          endDate: item.end_date,
          S2: item.S2,
          WV: item.WV,
          L8: item.L8,
          status: item.status,
          timestamp: item.timestamp,
        }
        );
    });
  }
  return modList;
});

const download = (id: number) => {
  const url = `/api/evaluations/${id}/download`
  window.location.assign(url)
}


</script>

<template>
  <v-navigation-drawer
    location="right"
    floating
    width="200"
    sticky
    permanent
    class="fill-height"
    style="overflow-y: hidden;"
  >
    <v-container class="overflow-y-auto">
      <div v-if="modelRun === null">
        Select a Model Run to display Site Models
      </div>
      <div v-else>
        <h3>Site Models:</h3>
        <v-card 
          v-for="item in modifiedList"
          :key="`${item.name}_${item.id}_${item.selected}`"
          class="modelRunCard"
          :class="{selectedCard: item.selected}"
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
              <v-tooltip>
                <template #activator="{ props:subProps }">
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
            </v-row>
          </v-card-text>
        </v-card>
      </div>
    </v-container>
  </v-navigation-drawer>
</template>

<style scoped>
.modelRunCard{
  border: 3px solid transparent;
}
.modelRunCard:hover {
  cursor: pointer;
  border: 3px solid blue;
}
.title {
  font-size: 12px;
}
.selectedCard{
  background-color: lightblue;
}
.errorCard{
  background-color: lightcoral;
}
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
