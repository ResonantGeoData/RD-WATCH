<template>
  <v-container>
    <v-card>
      <v-card-title>
        SmartFlow
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="dagRuns"
          :items-per-page="5"
          class="elevation-1"
        >
          <template #item.actions="{ item }">
            <v-icon
              color="primary"
              @click="startRun(item)"
            >
              mdi-play
            </v-icon>
            <v-icon
              color="error"
              @click="stopRun(item)"
            >
              mdi-stop
            </v-icon>
          </template>
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
          @click="showRegionDialog"
        >
          Start New DAG Run
        </v-btn>
        <v-dialog
          v-model="regionDialog"
          max-width="500"
        >
          <v-card>
            <v-card-title>Select Region</v-card-title>
            <v-card-text>
              <v-select
                v-model="selectedRegion"
                :items="regions"
                label="Region"
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
                @click="regionDialog = false"
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
import { onMounted, ref } from 'vue';

interface DagRun {
  dag_id: string;
  region: string;
  last_run: string;
  next_run: string;
  status: string;
}

const headers = [
  { title: 'DAG ID', key: 'dag_id' },
  { title: 'Region', key: 'region' },
  { title: 'Last Run', key: 'last_run' },
  { title: 'Next Run', key: 'next_run' },
  { title: 'Status', key: 'status' },
  { title: 'Actions', key: 'actions' },
];

const dagRuns = ref<DagRun[]>([
  {
    dag_id: 'example_dag_1',
    region: 'EX_R001',
    last_run: '2024-05-15T10:05:00Z',
    next_run: '2024-05-16T10:05:00Z',
    status: 'success',
  },
  {
    dag_id: 'example_dag_2',
    region: 'EX_R002',
    last_run: '2024-05-15T11:05:00Z',
    next_run: '2024-05-16T11:05:00Z',
    status: 'failed',
  },
  {
    dag_id: 'example_dag_3',
    region: 'EX_R003',
    last_run: '2024-05-15T12:05:00Z',
    next_run: '2024-05-16T12:05:00Z',
    status: 'running',
  },
  {
    dag_id: 'example_dag_4',
    region: 'EX_R004',
    last_run: '2024-05-15T13:05:00Z',
    next_run: '2024-05-16T13:05:00Z',
    status: 'success',
  },
  {
    dag_id: 'example_dag_5',
    region: 'EX_R005',
    last_run: '2024-05-15T14:05:00Z',
    next_run: '2024-05-16T14:05:00Z',
    status: 'failed',
  },
  {
    dag_id: 'example_dag_6',
    region: 'EX_R006',
    last_run: '2024-05-15T15:05:00Z',
    next_run: '2024-05-16T15:05:00Z',
    status: 'running',
  },
  {
    dag_id: 'example_dag_7',
    region: 'EX_R007',
    last_run: '2024-05-15T16:05:00Z',
    next_run: '2024-05-16T16:05:00Z',
    status: 'success',
  },
  {
    dag_id: 'example_dag_8',
    region: 'EX_R008',
    last_run: '2024-05-15T17:05:00Z',
    next_run: '2024-05-16T17:05:00Z',
    status: 'failed',
  },
  {
    dag_id: 'example_dag_9',
    region: 'EX_R009',
    last_run: '2024-05-15T18:05:00Z',
    next_run: '2024-05-16T18:05:00Z',
    status: 'running',
  },
  {
    dag_id: 'example_dag_10',
    region: 'EX_R010',
    last_run: '2024-05-15T19:05:00Z',
    next_run: '2024-05-16T19:05:00Z',
    status: 'success',
  },
]);

const regions = ['EX_R001', 'EX_R002', 'EX_R003', 'EX_R004', 'EX_R005']; // Sample region list

const regionDialog = ref<boolean>(false);
const selectedRegion = ref<string>('');

const fetchDagRuns = async () => {
  // Placeholder function, no actual API call
  // In the future, replace this with the actual API call
};

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

const startRun = (item: DagRun) => {
  // Placeholder for starting a run
  console.log(`Starting run for DAG: ${item.dag_id}`);
};

const stopRun = (item: DagRun) => {
  // Placeholder for stopping a run
  console.log(`Stopping run for DAG: ${item.dag_id}`);
};

const showRegionDialog = () => {
  regionDialog.value = true;
};

const startNewRun = () => {
  if (selectedRegion.value) {
    // Placeholder for starting a new run with selected region
    console.log(`Starting new DAG run on region: ${selectedRegion.value}`);
    regionDialog.value = false;
  }
};

onMounted(fetchDagRuns);
</script>
