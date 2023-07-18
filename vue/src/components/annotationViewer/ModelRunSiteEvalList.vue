<script setup lang="ts">
import { Ref, computed, ref, watch } from "vue";
import { ApiService } from "../../client";
import { ModelRunEvaluations } from "../../client/services/ApiService";

const props = defineProps<{
  modelRun: number | null;
  selectedEval: number | null;
}>();

const emit = defineEmits<{
  (e: "selected", val: {id: number, bbox: { xmin: number; ymin: number; xmax: number; ymax: number }}): void;
}>();

const evaluationsList: Ref<ModelRunEvaluations | null> = ref(null);


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
  const modList: {number: number, id: number; name: string, bbox: { xmin: number; ymin: number; xmax: number; ymax: number }, selected:boolean}[] = []
  if (evaluationsList.value?.evaluations) {
    const regionName = evaluationsList.value.region.name;
    evaluationsList.value.evaluations.forEach((item) => {
      const newNum = item.number.toString().padStart(4, '0')
      modList.push({number: item.number, id: item.id, name: `${regionName}_${newNum}`, bbox: item.bbox, selected: item.id === props.selectedEval});
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
          :key="`${item.name}_${item.selected}`"
          class="modelRunCard"
          :class="{selectedCard: item.selected}"
          @click="emit('selected', { id: item.id, bbox: item.bbox })"
        >
          <v-card-title class="title">{{ item.name }}</v-card-title>
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
.model-title {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
