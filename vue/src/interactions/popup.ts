import { Color, Map, MapLayerMouseEvent, Popup } from "maplibre-gl";
import { ShallowRef } from "vue";


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
            e.features.forEach((item: GeoJSON.GeoJsonProperties & { layer?: {paint?: { 'fill-color'?: Color}} }) => {
            if (item.properties && item.properties.id) {
                console.log(item);
                const id = item.properties.id
                let fillString = '';
                if (!htmlMap[id]) {
                    if (item.layer?.paint) {
                        const fillColor = item.layer?.paint['fill-color'] as Color;
                        if (fillColor) {
                            fillString = `style="background-color: rgba(${fillColor.r * 255}, ${fillColor.g*255}, ${fillColor.b*255}, ${fillColor.a*255})"`;
                            ids.push(id);
                            htmlMap[id] = true;
                            html = `${html}<li><div class='badge' ${fillString}>ID:${id}</div></li>`;
                        }
                    }
                }
            }
            })
            html += '</ul>'
            popup.setLngLat(coordinates).setHTML(html).addTo(map.value);
        } else if (map.value) {
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

export default popupLogic;