<script setup lang="ts">
import { state } from "../../store";
import type { SiteEvaluationList } from "../../client";

const props = defineProps<{
  evaluations: SiteEvaluationList;
}>();

const emit = defineEmits<{
  (e: "filter", by: string, value: string): void;
}>();
</script>

<template>
  <div class="dropdown">
    <label tabindex="0" class="btn m-1">Performer</label>
    <ul
      tabindex="0"
      class="dropdown-content menu rounded-box w-52 bg-base-100 p-2 shadow"
    >
      <li
        v-for="(performer, i) in props.evaluations.performers"
        :key="`performer-filter-${i}`"
      >
        <a
          :class="state.filters.performer === performer ? 'bg-info' : ''"
          @click="emit('filter', 'performer', performer)"
          >{{ performer }}</a
        >
      </li>
    </ul>
  </div>
</template>
