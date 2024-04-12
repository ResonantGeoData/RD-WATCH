// Helper function for handling image scaling needed for SAM
const handleImageScale = (image: HTMLImageElement) => {
  // Input images to SAM must be resized so the longest side is 1024
  const LONG_SIDE_LENGTH = 1024;
  const w = image.naturalWidth;
  const h = image.naturalHeight;
  const samScale = LONG_SIDE_LENGTH / Math.max(h, w);
  return { height: h, width: w, samScale };
};

// Given a GeoJSON in the scaled sense this will unscale it
const handlePolyUnscale = (scaledImageWidth: number, scaledImageHeight: number, unscaledImageWidth: number, unscaledImageHeight: number, scaledGeoJSON: GeoJSON.Polygon): GeoJSON.Polygon | null => {
  const unscaledGeoJSON: GeoJSON.Position[][] = [];

  scaledGeoJSON.coordinates.forEach((ring) => {
    const unscaledRing: GeoJSON.Position[] = [];
    ring.forEach((coord) => {
      const unscaled_x = (coord[0] / scaledImageWidth) * unscaledImageWidth;
      const unscaled_y = unscaledImageHeight - (coord[1] / scaledImageHeight) * unscaledImageHeight;
      unscaledRing.push([unscaled_x, unscaled_y]);
    });
    unscaledGeoJSON.push(unscaledRing);
  });

  return { type: "Polygon", coordinates: unscaledGeoJSON };
};


export { handleImageScale, handlePolyUnscale };
