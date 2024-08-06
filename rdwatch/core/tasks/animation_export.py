import os
import uuid

from celery import shared_task
from PIL import Image, ImageDraw

from rdwatch.core.models import SiteEvaluation, SiteImage, SiteObservation


def to_pixel_coords(lon, lat, bbox, xScale, yScale):
    x = (lon - bbox[0]) * xScale
    y = (lat - bbox[1]) * yScale
    return x, y


@shared_task
def create_animated_gif(site_evaluation_id):
    # Fetch the SiteEvaluation instance
    try:
        site_evaluation = SiteEvaluation.objects.get(id=site_evaluation_id)
    except SiteEvaluation.DoesNotExist:
        return

    # Fetch related SiteObservations
    site_observations = SiteObservation.objects.filter(siteeval=site_evaluation)

    # Determine the largest dimensions
    max_width, max_height = 0, 0
    images_data = []

    for observation in site_observations:
        images = SiteImage.objects.filter(observation=observation)
        for image_record in images:
            if image_record.image:
                img = Image.open(image_record.image)
                width, height = image_record.image_dimensions
                max_width = max(max_width, width)
                max_height = max(max_height, height)
                images_data.append((img, width, height, image_record))

    # Process each SiteObservation image
    frames = []
    for img, width, height, image_record in images_data:
        # Resize image to max dimensions
        img = img.resize((max_width, max_height))
        draw = ImageDraw.Draw(img)

        # Extract image dimensions and bounding box
        if not image_record.image_dimensions or not image_record.image_bbox:
            continue

        bbox = image_record.image_bbox.extent  # minx, miny, maxx, maxy
        print(bbox)
        xScale = (bbox[2] - bbox[0]) / (width)
        yScale = (bbox[3] - bbox[1]) / (height)
        print(f'width: {width} height: {height} max: {max_width}, {max_height}')
        print(f'xScale: {xScale} yScale: {yScale}')

        # Draw geometry or point on the image
        observation = image_record.observation
        if observation.geom:
            polygon = observation.geom
            if polygon.geom_type == 'Polygon':
                base_coords = polygon.coords[0]
                pixel_coords = [
                    to_pixel_coords(
                        lon,
                        lat,
                        bbox,
                        xScale,
                        yScale,
                    )
                    for lon, lat in base_coords
                ]
                centerX = max_width / 2.0
                centerY = max_height / 2.0
                bufferX = max_width / 10
                bufferY = max_height / 10
                box_coords = [
                    (centerX - bufferX, centerY - bufferY),
                    (centerX + bufferX, centerY - bufferY),
                    (centerX + bufferX, centerY + bufferY),
                    (centerX - bufferX, centerY + bufferY),
                    (centerX - bufferX, centerY - bufferY),  # Close the polygon
                ]
                print(pixel_coords)
                print(box_coords)
                draw.polygon(box_coords, outline='red')
                draw.polygon(pixel_coords, outline='white')

        if observation.point:
            point = observation.point
            pixel_point = to_pixel_coords(point.x, point.y, bbox, xScale, yScale)
            draw.ellipse(
                (
                    pixel_point[0] - 5,
                    pixel_point[1] - 5,
                    pixel_point[0] + 5,
                    pixel_point[1] + 5,
                ),
                fill='blue',
            )

        frames.append(img)

    # Save frames as an animated GIF
    if frames:
        output_file_path = os.path.join('./', 'animated_gifs', f'{uuid.uuid4()}.gif')
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        frames[0].save(
            output_file_path,
            save_all=True,
            append_images=frames[1:],
            duration=500,
            loop=0,
        )
        return output_file_path
