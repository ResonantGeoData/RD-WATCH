<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ChevronUpDownIcon } from "@heroicons/vue/24/solid";

type FilterOption = Props["options"][0];
type SelectedFilterOption = FilterOption | null;
interface Props {
  modelValue: SelectedFilterOption;
  label: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  options: Record<string | number, any>[];
  valueKey: keyof FilterOption;
}

const props = defineProps<Props>();

const filterOpen = ref(false);
const activeOption = computed(() =>
  props.modelValue === null ? null : props.modelValue[props.valueKey]
);

const optionMap = computed(() => {
  const map = new Map<Props["valueKey"], FilterOption>();
  props.options.forEach((val) => map.set(val[props.valueKey], val));
  return map;
});

const emit = defineEmits<{
  (e: "update:modelValue", selected: SelectedFilterOption): void;
}>();

watch(activeOption, (val) =>
  emit(
    "update:modelValue",
    val === null ? null : (optionMap.value.get(val) as FilterOption)
  )
);
</script>

<template>
  <div>
    <div
      v-if="!filterOpen && activeOption !== null"
      class="tooltip tooltip-right select-none"
      :data-tip="activeOption"
    >
      <span
        class="flex h-5 cursor-pointer items-baseline text-sm text-gray-100"
      >
        <span
          class="h-5 grow self-center rounded-l border-r border-blue-800 bg-blue-600 px-1 hover:bg-blue-400"
          @click="emit('update:modelValue', null)"
        >✕</span>
        <div
          class="flex items-baseline rounded-r bg-blue-600 hover:bg-blue-400"
          @click="filterOpen = true"
        >
          <span class="filter-val ml-2 grow-0 self-center whitespace-nowrap">{{
            activeOption
          }}</span>
          <span class="grow self-center"><ChevronUpDownIcon class="float-right mx-1 w-3" /></span>
        </div>
      </span>
    </div>

    <div
      v-if="!filterOpen && activeOption === null"
      class="h-5 cursor-pointer select-none rounded bg-gray-300 text-sm text-gray-600 hover:bg-gray-400 hover:text-gray-100 tooltip"
      @click="filterOpen = true"
    >
      <span
        class="flex items-baseline"
        @click="filterOpen = !filterOpen"
      >
        <span class="ml-2 grow-0 self-center">{{ label }}</span>
        <span class="grow self-center"><ChevronUpDownIcon class="float-right mx-1 w-3" /></span>
      </span>
    </div>

    <div
      v-if="filterOpen"
      class="cursor-pointer select-none rounded bg-gray-300 text-sm text-gray-600 hover:bg-gray-400 hover:text-gray-100 tooltip"
      @click="filterOpen = false"
    >
      <span class="flex items-baseline">
        <span class="ml-2 grow-0">{{ label }}</span>
        <span class="grow self-center"><ChevronUpDownIcon class="float-right mx-1 w-3" /></span>
      </span>
      <div
        class="dropdown overflow-y-auto overflow-x-hidden rounded-b border bg-white p-1 text-lg text-gray-600 hover:text-gray-600"
      >
        <ul>
          <li
            v-for="option in options"
            :key="option[valueKey]"
            class="whitespace-nowrap rounded px-1 hover:bg-blue-600 hover:text-gray-100"
            @click="
              emit(
                'update:modelValue',
                optionMap.get(option[valueKey]) as FilterOption
              )
            "
          >
            {{ option[valueKey] }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dropdown {
  position: fixed;
  z-index: 10;
  max-height: calc(90vh - 140px);
}

.filter-val {
  max-width: 70px;
  overflow-x: hidden;
  text-overflow: ellipsis;
}
</style>
