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
  

export {
    timeRangeFormat,
}