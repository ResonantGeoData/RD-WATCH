import { SiteObservation } from "./store"



const timeRangeFormat = (range: SiteObservation['timerange']) => {
    if (range === null || (range.max === null && range.min === null)) {
      return '--'
    } else {
      const first = range.min ? `${new Date(range.min * 1000).toLocaleString(
        "en",
        {
          dateStyle: "short",
        }
      )}` : 'None'
      const second = range.max ? `${new Date(range.max * 1000).toLocaleString(
        "en",
        {
          dateStyle: "short",
        }
      )}` : 'None'
      return `${first} - ${second}`
    }
    return '--'
  }
  

export {
    timeRangeFormat,
}