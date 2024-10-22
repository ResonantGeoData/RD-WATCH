import { SiteOverview } from "./store"

const timeRangeFormat = (range: SiteOverview['timerange']) => {
    if (range === null || (range.max === null && range.min === null)) {
      return '--'
    } else {
      const first = range.min ? `${new Date(range.min * 1000).toISOString().substring(0, 10)}` : 'None'
      const second = range.max ? `${new Date(range.max * 1000).toISOString().substring(0, 10)}` : 'None'
      return `${first} - ${second}`
    }
    return '--'
  }

  async function downloadPresignedFile(url: string, filename: string) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Response error');
        }
        const blob = await response.blob();
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(a.href);
    } catch (error) {
        console.error('Error downloading file:', error);
    }
}

export type EventCallback<T> = (e: T) => void;

const createEventHook = <T = unknown>() => {
  const cbs = new Set<EventCallback<T>>();

  const off = (fn: EventCallback<T>) => {
    cbs.delete(fn);
  };

  const on = (fn: EventCallback<T>) => {
    cbs.add(fn);
    return { off: () => off(fn) };
  };

  const trigger = (e: T) => {
    Array.from(cbs).forEach((fn) => fn(e));
  };

  return { on, off, trigger };
}

export type BoundingBox = { xmin: number; ymin: number; xmax: number; ymax: number };

export {
    timeRangeFormat,
    downloadPresignedFile,
}