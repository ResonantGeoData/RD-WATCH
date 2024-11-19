<script setup lang="ts">

const props = defineProps<{
  pk: string;
  siteId: string;
  imageUrl: string | null;
  smqtkUuid: string;
  confidence: number;
  status: 'positive' | 'neutral' | 'negative';
}>();

const emit = defineEmits<{
  'status-changed': ['positive' | 'neutral' | 'negative'];
}>();
</script>

<template>
  <div class="d-flex flex-row py-1">
    <div
      class="border-thin"
      style="min-width: 100px"
    >
      <v-img
        v-if="imageUrl"
        :src="imageUrl"
      />
    </div>
    <div
      class="d-flex flex-column justify-space-between"
      style="white-space: nowrap; font-size: 12px;"
    >
      <div class="pa-1">
        <strong>Site</strong>: {{ siteId }}<br>
        <strong>Score</strong>: {{ confidence.toFixed(2) }}
      </div>
      <v-item-group
        :model-value="props.status"
        @update:model-value="emit('status-changed', $event)"
      >
        <v-item
          #="{ isSelected, toggle }"
          value="positive"
        >
          <v-btn
            size="small"
            variant="flat"
            :color="isSelected ? 'primary' : ''"
            @click="toggle"
          >
            P
          </v-btn>
        </v-item>
        <v-item
          #="{ isSelected, toggle }"
          value="neutral"
        >
          <v-btn
            size="small"
            variant="flat"
            :color="isSelected ? 'primary' : ''"
            @click="toggle"
          >
            ?
          </v-btn>
        </v-item>
        <v-item
          #="{ isSelected, toggle }"
          value="negative"
        >
          <v-btn
            size="small"
            variant="flat"
            :color="isSelected ? 'primary' : ''"
            @click="toggle"
          >
            N
          </v-btn>
        </v-item>
      </v-item-group>
    </div>
  </div>
</template>
