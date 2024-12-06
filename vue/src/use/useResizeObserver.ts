import { type MaybeRef, computed, unref, watch } from "vue";

export function useResizeObserver(el: MaybeRef<HTMLElement | null | undefined>, callback: (entries: ResizeObserverEntry[]) => void) {
  const elRef = computed(() => unref(el));
  const observer = new ResizeObserver(callback);

  return watch(elRef, (element, oldElement) => {
    if (oldElement) {
      observer.unobserve(oldElement);
    }

    if (element) {
      observer.observe(element);
    }
  }, { immediate: true });
}
