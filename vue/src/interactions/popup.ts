import { Ref, ref } from 'vue';
import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";

const checkBadge = '<svg style="display:inline;" width="20" height="20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="replacementColor" aria-hidden="true"><path fill-rule="evenodd" d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd"></path></svg>';

const hoveredInfo: Ref<string[]> = ref([]);

const calculateScoreColor = (score: number) => {
    if (score <= .25) {
        return 'red';
      } if (score > .25 && score <= .50) {
        return 'orange';
      } if (score > .50 && score <= .75) {
        return 'yellowgreen';
      } if (score > .75 && score <= 1.00) {
        return 'green';
      }
    return 'black';
}

const popupLogic = (map: ShallowRef<null | Map>) => {
    const popup = new Popup({
        closeButton: false,
        closeOnClick: false
        });
    let insideObservation = false;
    const drawPopup = (e:MapLayerMouseEvent) => {
        if (e.features && e.features[0]?.properties && map.value) {
            const coordinates = e.lngLat;
            const ids = []
            let html = '<ul>';
            const htmlMap: Record<string, boolean> = {};
            insideObservation = true;
            hoveredInfo.value = [];
            e.features.forEach((item: GeoJSON.GeoJsonProperties & { layer?: {paint?: { 'fill-color'?: Color}} }) => {
                if (item.properties && item.properties.id) {
                    const id = item.properties.id
                    const score = item.properties.score;
                    hoveredInfo.value.push(`${item.properties.configuration_id}_${item.properties.region_id}_${item.properties.performer_id}`);
                    let fillString = '';
                    if (!htmlMap[id]) {
                        if (item.layer?.paint) {
                            const fillColor = item.layer?.paint['fill-color'] as Color;
                            if (fillColor) {
                                fillString = `style="background-color: rgba(${fillColor.r * 255}, ${fillColor.g*255}, ${fillColor.b*255}, ${fillColor.a*255}); font-weight: bolder"`;
                                ids.push(id);
                                htmlMap[id] = true;
                                let groundtruth = checkBadge;
                                if (item.properties.groundtruth) {
                                    groundtruth = groundtruth.replace('replacementColor',`rgba(${fillColor.r * 255}, ${fillColor.g*255}, ${fillColor.b*255}, ${fillColor.a*255})`);
                                } else 
                                {
                                    groundtruth = groundtruth.replace('replacementColor',`rgba(0,0,0,0)`);

                                }
                                const scoreStyle = `style="background-color:${calculateScoreColor(score.toFixed(2))};color: black; font-weight:bolder;"`
                                html = `${html}<li>${groundtruth}<div class='badge' ${fillString}>ID:${id}</div> <div class='badge' ${scoreStyle}>Score:${score.toFixed(2)}</div></li>`;
                            }
                        }
                    }
                }
                });
            html += '</ul>'
            popup.setLngLat(coordinates).setHTML(html).addTo(map.value);
        } else if (map.value) {
            hoveredInfo.value = [];
            insideObservation = false;
            map.value.getCanvas().style.cursor = '';
            popup.remove();  
        }
    }
    if (map.value) {
        map.value.on('mouseenter', 'observations-fill', function (e) {
            drawPopup(e);
        });
        map.value.on('mouseleave', 'observations-fill', function (e) {
            drawPopup(e);
        });
        map.value.on('mousemove', 'observations-fill', function (e) {
            if (insideObservation) {
                drawPopup(e)
            }
        });
    }
}

export { popupLogic, hoveredInfo };