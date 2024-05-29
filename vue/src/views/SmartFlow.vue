<template>
  <v-container>
    <v-card>
      <v-card-title>
        SmartFlow
      </v-card-title>
      <v-card-text>
        <v-data-table
          v-model:items-per-page="itemsPerPage"
          :headers="headers"
          :items="dagRuns"
          :items-length="totalItems"
          :loading="loading"
          :search="dagSearch"
          item-name="dag_run_id"
          class="elevation-1"
        >
          <template #top>
            <v-autocomplete
              v-model="dag"
              :items="dagResults"
              item-text="dag_id"
              item-value="dag_id"
              label="Search DAG by ID"
              hide-details
              no-filter
              solo
              clearable
              @update:search="fetchDags"
            />
          </template>
          <!-- <template #item.actions="{ item }">
            <v-icon color="primary" @click="startRun(item)">
              mdi-play
            </v-icon>
            <v-icon color="error" @click="stopRun(item)">
              mdi-stop
            </v-icon>
          </template> -->
          <template #[`item.status`]="{ item }">
            <v-chip
              :color="statusColor(item.status)"
              dark
            >
              {{ item.status }}
              <v-progress-circular
                v-if="item.status === 'running'"
                indeterminate
                :size="20"
                class="ml-2"
              />
            </v-chip>
          </template>
        </v-data-table>
        <v-btn
          color="primary"
          @click="showNewDagRunDialog"
        >
          Start New DAG Run
        </v-btn>
        <v-dialog
          v-model="newDagRunDialog"
          max-width="500"
        >
          <v-card>
            <v-card-title>Enter Region</v-card-title>
            <v-card-text>
              <v-text-field
                v-model="newDagRunTitle"
                label="DAG Run Title"
              />
            </v-card-text>
            <v-card-text>
              <v-textarea
                v-model="newDagRunConf"
                label="conf"
              />
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="primary"
                @click="startNewRun"
              >
                Start
              </v-btn>
              <v-btn
                color="error"
                @click="newDagRunDialog = false"
              >
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { debounce } from 'lodash';
import { SmartflowService } from '../client';

interface DagRun {
  dag_id: string;
  dag_run_id: string;
  data_interval_end: string;
  data_interval_start: string;
  end_date: string;
  execution_date: string;
  external_trigger: boolean;
  last_scheduling_decision: string;
  logical_date: string;
  note: string | null;
  run_type: string;
  start_date: string;
  state: string;
}

const headers = [
  { title: 'DAG ID', key: 'dag_id' },
  { title: 'DAG Run ID', key: 'dag_run_id' },
  { title: 'Status', key: 'state' },
  { title: 'Actions', key: 'actions' },
];

const dag = ref('');
const dagRuns = ref<DagRun[]>([]);
const itemsPerPage = ref(10);
const totalItems = ref(0);
const loading = ref(false);

const dagSearch = ref('');
const dagResults = ref<string[]>([]);

const newDagRunDialog = ref<boolean>(false);
const newDagRunTitle = ref<string>('');
const newDagRunConf = ref<string>('');

const fetchDags = debounce(async (searchTerm: string) => {
  loading.value = true;
  const query = searchTerm ? { dag_id_pattern: searchTerm } : {};
  const res = await SmartflowService.rdwatchSmartflowViewsListDags(query);
  dagResults.value = res.dags.map((dag: any) => dag.dag_id);
  loading.value = false;
}, 500);

watch(dagSearch, fetchDags);

const fetchDagRuns = async ({ page = 1, itemsPerPage = 10 }) => {
  loading.value = true;
  const { dag_runs, total_entries } = await SmartflowService.rdwatchSmartflowViewsListDagRuns(dag.value, { limit: itemsPerPage, offset: (page - 1) * itemsPerPage });
  totalItems.value = total_entries;
  dagRuns.value = dag_runs;
  loading.value = false;
};

watch(dag, () => fetchDagRuns({ page: 1, itemsPerPage: itemsPerPage.value }));

const statusColor = (status: string): string => {
  switch (status) {
    case 'success':
      return 'green';
    case 'failed':
      return 'red';
    default:
      return 'grey';
  }
};

const showNewDagRunDialog = () => {
  newDagRunDialog.value = true;
};

const startNewRun = async () => {
  // Placeholder for starting a new run with selected region
  await SmartflowService.rdwatchSmartflowViewsCreateDagRun(dag.value, { dag_run_title: newDagRunTitle.value, conf: JSON.parse(newDagRunConf.value)});
  newDagRunDialog.value = false;
};

onMounted(() => fetchDags);
</script>
