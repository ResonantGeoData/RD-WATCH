<script setup lang="ts">
import { Ref, computed, ref, watch } from "vue";
import { ApiService } from "../../client";
import { ModelRunEvaluations } from "../../client/services/ApiService";

interface MdoelRunEvaluationDisplay {
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
  status: ModelRunEvaluations['evaluations'][0]['status'];
}


const props = defineProps<{
  modelRun: number | null;
  selectedEval: number | null;
}>();

const emit = defineEmits<{
  (e: "selected", val: MdoelRunEvaluationDisplay): void;
}>();

const evaluationsList: Ref<ModelRunEvaluations | null> = ref(null);

const statusMap: Record<ModelRunEvaluations['evaluations'][0]['status'], { name: string, color: string }> = {
  'PROPOSAL': { name: 'Proposed', color: 'orange'},
  'REJECTED': { name: 'Rejected', color: 'error'},
  'ACCEPTED': { name: 'Accepted', color: 'success'},
  
}


const getSiteEvalIds = async () => {
  if (props.modelRun !== null) {
    const results = await ApiService.getModelRunEvaluations(props.modelRun);
    evaluationsList.value = results;
  }
}

watch(() => props.modelRun, () => {
  getSiteEvalIds();
});
getSiteEvalIds();

const modifiedList = computed(() => {
  const modList: MdoelRunEvaluationDisplay[] = []
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
        }
        );
    });
  }
  return modList;
});


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
        Select a Model Run to display Site Evaluations
      </div>
      <div v-else>
        <h3>Site Evaluations:</h3>
        <v-card 
          v-for="item in modifiedList"
          :key="`${item.name}_${item.id}_${item.selected}`"
          class="modelRunCard"
          :class="{selectedCard: item.selected, errorCard: item.images === 0}"
          @click="emit('selected', item)"
        >
          <v-card-title class="title">
            {{ item.name }}
          </v-card-title>
          <v-card-text>
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
              <b> 0 Images Downloaded</b>
            </div>
            <v-row dense justify="center" class="pa-2">
              <v-chip
                size="small"
                :color="statusMap[item.status].color"
              >
                {{ statusMap[item.status].name }}
              </v-chip>
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
