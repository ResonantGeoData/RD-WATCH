import { ShallowRef } from "vue";
import { Map } from "maplibre-gl";

const generatePatterns = (map: ShallowRef<null | Map>) => {
    if (map.value) {
    map.value.on('load', () => {
        const size = 8;
        const bytesPerPixel = 4
        const dataRight = new Uint8Array(size * size * bytesPerPixel);
        const dataLeft = new Uint8Array(size * size * bytesPerPixel);
        // Generate our pattern from the pixels
        const X = [0, 0, 0, 255]; //RGBA
        const O = [0, 0, 0, 0];
        const patternRight = Array(8*8).fill(O)
        const patternLeft = Array(8*8).fill(O)
        const thickness = 1;
        for (let y = 0; y < size; y += 1) {
            for (let x = 0; x < size; x += 1) {
                console.log(`x: ${x} y: ${y} ${(size-1-y) + (thickness/2)}:${(size-1-y) - (thickness/2)}`)
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
        console.log(patternRight);
        for (let i = 0; i < patternRight.length; i += 1) {
          for (let bit = 0; bit < 4; bit += 1) {
            
            dataRight[(4*i) + bit] = patternRight[i][bit];
            dataLeft[(4*i) + bit] = patternLeft[i][bit];
          }
        }
  
        if (map.value) {
          map.value.addImage('diagonal-right', { width: size, height: size, data: dataRight });
          map.value.addImage('diagonal-left', { width: size, height: size, data: dataLeft });
        }
      });
    } 
};

export { 
    generatePatterns,
};
