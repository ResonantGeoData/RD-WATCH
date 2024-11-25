<script setup lang="ts">
import { computed } from 'vue';


const props = defineProps<{
  pk: string;
  index: number;
  siteId: string;
  imageUrl: string | null;
  smqtkUuid: string;
  confidence: number;
  status: 'positive' | 'neutral' | 'negative';
}>();

const emit = defineEmits<{
  'status-changed': ['positive' | 'neutral' | 'negative'];
  'image-click': [];
}>();

const cardColor = computed(() => {
  if (props.status === 'positive') return 'green-lighten-2';
  if (props.status === 'neutral') return '';
  if (props.status === 'negative') return 'red-lighten-2';
  return '';
});
</script>

<template>
  <v-card
    class="my-2"
    :color="cardColor"
  >
    <v-card-title class="text-subtitle-2">
      {{ index }}. <strong>{{ siteId }}</strong>
    </v-card-title>
    <v-card-text class="d-flex flex-row">
      <div
        v-ripple
        class="border-thin d-flex flex-row align-center"
        style="flex-basis: 100px; min-height: 100px; cursor: pointer"
        @click="emit('image-click')"
      >
        <v-img
          v-if="imageUrl"
          :src="imageUrl"
        />
      </div>
      <div class="d-flex flex-column flex-grow-1 ml-2 justify-space-between">
        <v-item-group
          class="w-100 d-flex flex-row justify-space-between"
          :model-value="props.status"
          @update:model-value="emit('status-changed', $event)"
        >
          <v-item
            #="{ isSelected, toggle }"
            value="positive"
          >
            <v-btn
              size="x-small"
              variant="flat"
              :color="isSelected ? 'primary' : ''"
              icon="mdi-check"
              @click="toggle"
            />
          </v-item>
          <v-item
            #="{ isSelected, toggle }"
            value="neutral"
          >
            <v-btn
              size="x-small"
              variant="flat"
              :color="isSelected ? 'primary' : ''"
              icon="mdi-help"
              @click="toggle"
            />
          </v-item>
          <v-item
            #="{ isSelected, toggle }"
            value="negative"
          >
            <v-btn
              size="x-small"
              variant="flat"
              :color="isSelected ? 'primary' : ''"
              icon="mdi-close"
              @click="toggle"
            />
          </v-item>
        </v-item-group>
        <div>
          Similarity: <strong>{{ Math.round(confidence*100) }}%</strong>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>
