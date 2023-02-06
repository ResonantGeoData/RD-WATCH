import { Ref, ShallowRef, ref } from "vue";
import { Map } from "maplibre-gl";

const mapReference: Ref<null | Map> = ref(null);
const patternCreation = (map: ShallowRef<Map | null>, thickness=1, opacity=255, color=[0,0,0]) => {
  const size = 10;
  const bytesPerPixel = 4
  const dataRight = new Uint8Array(size * size * bytesPerPixel);
  const dataLeft = new Uint8Array(size * size * bytesPerPixel);
  // Generate our pattern from the pixels
  const X = [color[0], color[1], color[2], opacity]; //RGBA
  const O = [0, 0, 0, 0];
  const patternRight = Array(size*size).fill(O)
  const patternLeft = Array(size*size).fill(O)
  for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
          if (x  >= ((size-1-y) - (thickness/2)) && x <= (size-1-y) + (thickness/2)  ) {
              patternRight[x+(y*size)] = X;
          }
          if (x >= y - (thickness/2) && x  <= y + (thickness/2)  ) {
              patternLeft[x+(y*size)] = X;
          }

      }
  }
  // const patternRight = [ 
  //          O, O, O, O, O, O, X, X,
  //          O, O, O, O, O, X, X, X,
  //          O, O, O, O, X, X, X, O,
  //          O, O, O, X, X, X, O, O,
  //          O, O, X, X, X, O, O, O,
  //          O, X, X, X, O, O, O, O,
  //          X, X, X, O, O, O, O, O,
  //          X, X, O, O, O, O, O, O,
  //         ];
  // const patternLeft = [ 
  //          X, X, O, O, O, O, O, O,
  //          X, X, X, O, O, O, O, O,
  //          O, X, X, X, O, O, O, O,
  //          O, O, X, X, X, O, O, O,
  //          O, O, O, X, X, X, O, O,
  //          O, O, O, O, X, X, X, O,
  //          O, O, O, O, O, X, X, X,
  //          O, O, O, O, O, O, X, X,
  //         ];
  for (let i = 0; i < patternRight.length; i += 1) {
    for (let bit = 0; bit < 4; bit += 1) {
      
      dataRight[(4*i) + bit] = patternRight[i][bit];
      dataLeft[(4*i) + bit] = patternLeft[i][bit];
    }
  }

  if (map.value) {
    if (map.value.hasImage('diagonal-right')) {
      map.value.removeImage('diagonal-right');
    }
    if (map.value.hasImage('diagonal-left')) {
      map.value.removeImage('diagonal-left');
    }

    map.value.addImage('diagonal-right', { width: size, height: size, data: dataRight });
    map.value.addImage('diagonal-left', { width: size, height: size, data: dataLeft });
  }
  return {'diagonal-left': dataLeft, 'diagonal-right': dataRight}

}

const updatePattern = (thickness=1, opacity=255, color=[0,0,0]) => {
  if (mapReference.value) {
    return patternCreation(mapReference, thickness, opacity, color);
  }

}
const generatePatterns = (map: ShallowRef<null | Map>) => {
    if (map.value) {
      mapReference.value = map.value;
    map.value.on('load', () => {
      patternCreation(map);
      });
    } 
};

export { 
    generatePatterns,
    updatePattern,
};
