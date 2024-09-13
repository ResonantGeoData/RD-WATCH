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

export {
    timeRangeFormat,
    downloadPresignedFile,
}