import { App, Ref,   nextTick, reactive, ref } from "vue";
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";
import { getSiteObservationDetails, selectedObservationList, state } from "../store";
import  createPopup from '../main';
import { PopUpData, PopUpSiteData } from '../interactions/popUpType';
import { scoringColors, scoringColorsKeys, styles } from "../mapstyle/annotationStyles";


  const hoveredInfo: Ref<{region: string[], siteId: string[]}> = ref({region: [], siteId:[]});

let app: App | null = null;
const popUpProps: Record<string, PopUpData> = reactive({});
const popUpSiteProps: Record<string, PopUpSiteData> = reactive({});

const calculateScoreColor = (score: number) => {
  if (score <= 0.25) {
    return "red";
  }
  if (score > 0.25 && score <= 0.5) {
    return "orange";
  }
  if (score > 0.5 && score <= 0.75) {
    return "yellowgreen";
  }
  if (score > 0.75 && score <= 1.0) {
    return "green";
  }
  return "black";
};
let popup: Popup;
const map:ShallowRef<null | Map> = ref(null)
const popupLogic = async (mapArg: ShallowRef<null | Map>) => {
  popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    maxWidth: '700px',
  });
  map.value = mapArg.value;
};

const leavePopupObservation = async (e: MapLayerMouseEvent) => {
 drawPopupObservation(e, true); 
};
const drawPopupObservation = async (e: MapLayerMouseEvent, remove=false) => {
  if (e.features && e.features[0]?.properties && map.value) {
    const coordinates = e.lngLat;
    const ids = [];
    const htmlMap: Record<string, boolean> = {};
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    const popupData: PopUpData[] = [];
    e.features.forEach(
      (
        item: GeoJSON.GeoJsonProperties & {
          layer?: { paint?: { "fill-color"?: Color } };
        }
      ) => {
        if (item.properties && item.properties.id) {
          const id = item.properties.site_number;
          const region: string = item.properties.region;
          if (!remove) {
            const score = item.properties.score;
            const siteId = item.properties.siteeval_id;
            const configName = item.properties.configuration_name;
            const performerName = item.properties.performer_id;
            const version = item.properties.version;
            const siteLabel = item.properties.site_label;
            hoveredInfo.value.region.push(
              `${item.properties.configuration_id}_${region}_${item.properties.performer_id}`
            );
            hoveredInfo.value.siteId.push(siteId);
            if (!htmlMap[id]) {
              if (item.layer?.paint) {
                const fillColor = item.layer?.paint["fill-color"] as Color;
                if (fillColor) {
                  ids.push(id);
                  htmlMap[id] = true;
                  }
                  const area = Math.round(item.properties.area).toLocaleString('en-US');
                  const data = {
                    siteId: `${region}_${String(id).padStart(4, '0')}`,
                    score,
                    groundTruth: item.properties.groundtruth,
                    obsColor: `rgb(${fillColor.r *255}, ${fillColor.g * 255}, ${fillColor.b * 255})`,
                    siteColor: styles[siteLabel]?.color,
                    scoreColor: calculateScoreColor(score),
                    timestamp: item.properties.timestamp,
                    area,
                    version,
                    configName,
                    performerName,
                    siteLabel,
                }
                popupData.push(data);
                popUpProps[`${region}_${String(id).padStart(4, '0')}`] = data;
              }
            }
          } else {
            delete popUpProps[`${region}_${String(id).padStart(4, '0')}`];
          }
        }
      }
    );
    popup.setLngLat(coordinates).setHTML('<div id="popup-content"></div>').addTo(map.value);
    nextTick(() => {
      if (app !== null) {
        app.unmount();
        app = null;
      }
      app = createPopup(popUpProps, popUpSiteProps);
      app.mount('#popup-content');
    });
  } else if (map.value) {
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    for (const item in popUpProps) {
      delete popUpProps[item];
    }
    if (app !== null) {
      app.unmount();
      app = null;
    }
    map.value.getCanvas().style.cursor = "";
    popup.remove();
  }
};
const clickObservation = async (e: MapLayerMouseEvent) => {
  if (e.features && e.features[0]?.properties && map.value) {
    e.features.forEach(async (feature) => {
    if (feature.properties) {
        const siteId = feature.properties.siteeval_id;
        const obsDetails = {
          region: feature.properties.region as string,
          configurationId: feature.properties.configuration_id as number,
          siteNumber: feature.properties.site_number as number,
          version: feature.properties.version,
          performer: feature.properties.performer_name,
          title: feature.properties.configuration_name,
        }

        if (siteId && !selectedObservationList.value.includes(siteId)) {
          await getSiteObservationDetails(siteId, obsDetails);
        }
      }
    })
  }

}
const clickSite = async (e: MapLayerMouseEvent) => {
  if (e.features && e.features[0]?.properties && map.value) {
    e.features.forEach(async (feature) => {
    if (feature.properties) {
        const siteId = feature.properties.uuid;
        const obsDetails = {
          region: feature.properties.region as string,
          configurationId: feature.properties.configuration_id as number,
          siteNumber: feature.properties.site_number as number,
          version: feature.properties.version,
          performer: feature.properties.performer_name,
          title: feature.properties.configuration_name,
        }
        if (siteId && !selectedObservationList.value.includes(siteId)) {
          await getSiteObservationDetails(siteId, obsDetails);
        }
      }
    })
  }

}


const removeSitePopupObservation = async (e: MapLayerMouseEvent) => {
  drawSitePopupObservation(e, true);
}

const drawSitePopupObservation = async (e: MapLayerMouseEvent, remove=false) => {
  if (e.features && e.features[0]?.properties && map.value) {
    const coordinates = e.lngLat;
    const ids = [];
    const htmlMap: Record<string, boolean> = {};
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    const popupData: PopUpSiteData[] = [];
    e.features.forEach(
      (
        item: GeoJSON.GeoJsonProperties & {
          layer?: { paint?: { "fill-color"?: Color, 'line-color'?: Color } };
        }
      ) => {
        if (item.properties && item.properties.id) {
          const id = item.properties.site_number;
          const region: string = item.properties.region;
          if (!remove) {
            const siteId = item.properties.siteeval_id;
            const configName = item.properties.configuration_name;
            const performerName = item.properties.performer_name;
            const version = item.properties.version;
            const siteLabel = item.properties.label;
            hoveredInfo.value.region.push(
              `${item.properties.configuration_id}_${region}_${item.properties.performer_id}`
            );
            hoveredInfo.value.siteId.push(siteId);
            if (!htmlMap[id]) {
              if (item.layer?.paint) {
                  ids.push(id);
                  htmlMap[id] = true;
                  }
                  const start_date = item.properties.start_date ? item.properties.start_date .substring(0, 10) : 'null';
                  const end_date = item.properties.end_date ? item.properties.end_date.substring(0, 10) : 'null';
                  const colorCode = item.properties.color_code as scoringColorsKeys;
                  const scoreColor  = scoringColors[colorCode] ? scoringColors[colorCode].hex : undefined
                  const scoreLabel  = scoringColors[colorCode] ? scoringColors[colorCode].title : undefined
                  const data = {
                    siteId: `${region}_${String(id).padStart(4, '0')}`,
                    groundTruth: item.properties.groundtruth,
                    siteColor: styles[siteLabel]?.color,
                    timeRange: `${start_date} to ${end_date}`,
                    version,
                    configName,
                    performerName,
                    scoreColor,
                    scoreLabel,
                    siteLabel,
                }
                popupData.push(data);
                popUpSiteProps[`${region}_${String(id).padStart(4, '0')}`] = data;
            }
          } else {
            delete popUpSiteProps[`${region}_${String(id).padStart(4, '0')}`];
          }
        }
      }
    );
    popup.setLngLat(coordinates).setHTML('<div id="popup-content"></div>').addTo(map.value);
    nextTick(() => {
      if (app !== null) {
        app.unmount();
        app = null;
      }
      app = createPopup(popUpProps, popUpSiteProps);
      app.mount('#popup-content');
    });
  } else if (map.value) {
    hoveredInfo.value.region = [];
    hoveredInfo.value.siteId = [];
    for (const item in popUpSiteProps) {
      delete popUpSiteProps[item];
    }
    if (app !== null) {
      app.unmount();
      app = null;
    }
    map.value.getCanvas().style.cursor = "";
    popup.remove();
  }
};

let loadedFunctions: {
  id: string,
  mouseenter: (e: MapLayerMouseEvent) => Promise<void>;
  mouseleave: (e: MapLayerMouseEvent) => Promise<void>;
  mouseenterSite: (e: MapLayerMouseEvent) => Promise<void>;
  mouseleaveSite: (e: MapLayerMouseEvent) => Promise<void>;
  clickObservation: (e: MapLayerMouseEvent) => Promise<void>;
  clickSite: (e: MapLayerMouseEvent) => Promise<void>;
}[] = []
const setPopupEvents = (map: ShallowRef<null | Map>) => {
  if (map.value) {
    for (let i = 0; i< loadedFunctions.length; i += 1){
      const data = loadedFunctions[i];
      map.value.off("mouseenter", `observations-fill-${data.id}`, data.mouseenter);
      map.value.off("mouseleave", `observations-fill-${data.id}`, data.mouseleave);
      map.value.off("mouseenter", `sites-fill-${data.id}`, data.mouseenterSite);
      map.value.off("mouseleave", `sites-fill-${data.id}`, data.mouseenterSite);
      map.value.off("click", `observations-fill-${data.id}`, data.clickObservation);
      map.value.off("click", `sites-fill-${data.id}`, data.clickSite);
    }
    loadedFunctions = []
    for (const m of state.openedModelRuns) {
      const id = m.split('|')[0];
      map.value.on("mouseenter", `observations-fill-${id}`, drawPopupObservation);
      map.value.on("mouseleave", `observations-fill-${id}`, leavePopupObservation);
      map.value.on("mouseenter", `sites-fill-${id}`, drawSitePopupObservation);
      map.value.on("mouseleave", `sites-fill-${id}`, removeSitePopupObservation);
      map.value.on("click", `observations-fill-${id}`, clickObservation);
      map.value.on("click", `sites-fill-${id}`, clickSite);
      loadedFunctions.push({
        id,
        mouseenter: drawPopupObservation,
        mouseleave: leavePopupObservation,
        mouseenterSite: drawSitePopupObservation,
        mouseleaveSite: removeSitePopupObservation,
        clickObservation,
        clickSite,
      });
    }
  }
}

export { popupLogic, hoveredInfo, setPopupEvents };
