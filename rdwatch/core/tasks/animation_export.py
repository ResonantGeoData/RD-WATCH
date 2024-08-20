import os
import uuid

import cv2
import numpy as np
from celery import shared_task
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

from rdwatch.core.models import SiteEvaluation, SiteImage

label_mapping = {
    'active_construction': {
        'color': (192, 0, 0),
        'label': 'Active Construction',
    },
    'post_construction': {
        'color': (91, 155, 213),
        'label': 'Post Construction',
    },
    'site_preparation': {
        'color': (255, 217, 102),
        'label': 'Site Preparation',
    },
    'unknown': {
        'color': (112, 48, 160),
        'label': 'Unknown',
    },
    'no_activity': {
        'color': (166, 166, 166),
        'label': 'No Activity',
    },
    'positive_annotated': {
        'color': (127, 0, 0),
        'label': 'Positive Annotated',
    },
    'positive': {
        'color': (127, 0, 0),
        'label': 'Positive Annotated',
    },
    'positive_partial': {
        'color': (0, 0, 139),
        'label': 'Positive Partial',
    },
    'positive_annotated_static': {
        'color': (255, 140, 0),
        'label': 'Positive Annotated Static',
    },
    'positive_partial_static': {
        'color': (255, 255, 0),
        'label': 'Positive Partial Static',
    },
    'positive_pending': {
        'color': (30, 144, 255),
        'label': 'Positive Pending',
    },
    'positive_excluded': {
        'color': (0, 255, 255),
        'label': 'Positive Excluded',
    },
    'negative': {
        'color': (255, 0, 255),
        'label': 'Negative',
    },
    'ignore': {
        'color': (0, 255, 0),
        'label': 'Ignore',
    },
    'transient_positive': {
        'color': (255, 105, 180),
        'label': 'Transient Positive',
    },
    'transient_negative': {
        'color': (255, 228, 196),
        'label': 'Transient Negative',
    },
    'system_proposed': {
        'color': (31, 119, 180),
        'label': 'System Proposed',
    },
    'system_confirmed': {
        'color': (31, 119, 180),
        'label': 'System Confirmed',
    },
    'system_rejected': {
        'color': (31, 119, 180),
        'label': 'System Rejected',
    },
}


def to_pixel_coords(lon, lat, bbox, xScale, yScale):
    x = (lon - bbox[0]) * xScale
    y = (lat - bbox[1]) * yScale
    return x, y


def draw_text_in_box(
    draw,
    text,
    position,
    box_size,
    box_color=(80, 80, 80),
    text_color=(255, 255, 255),
    font_path=None,
    initial_font_size=30,
):
    """
    Draws text within a given box with adjustable font size and a background square.
    If the text is larger than the box, the box size is adjusted to fit the text.

    :param draw: ImageDraw object to draw on the image.
    :param text: Text to draw.
    :param position: Position (x, y) to start drawing the box and text.
    :param box_size: Tuple (width, height) specifying the initial box size.
    :param box_color: Background color of the box (R, G, B).
    :param text_color: Color of the text (R, G, B).
    :param font_path: Path to a .ttf font file, or None to use default font.
    :param initial_font_size: Starting font size.
    """
    max_width, max_height = box_size

    # Load font
    if font_path:
        font = ImageFont.truetype(font_path, initial_font_size)
    else:
        font = ImageFont.load_default()

    # Measure text size
    text_bbox = draw.textbbox((0, 0), text, font=font)  # (left, top, right, bottom)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Adjust font size to fit the box
    while (
        text_width > max_width or text_height > max_height
    ) and initial_font_size > 10:
        initial_font_size -= 2
        font = (
            ImageFont.truetype(font_path, initial_font_size)
            if font_path
            else ImageFont.load_default()
        )
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

    # Adjust the box size if the text is larger
    box_width = max(text_width, max_width)
    box_height = max(text_height, max_height)

    # Draw background box
    draw.rectangle(
        [position, (position[0] + box_width, position[1] + box_height)], fill=box_color
    )

    # Calculate text position to center it in the box
    text_x = position[0] + (box_width - text_width) / 2
    text_y = position[1] + (box_height - text_height) / 2

    # Draw text
    draw.text((text_x, text_y), text, font=font, fill=text_color)


@shared_task
def create_animated_gif(
    site_evaluation_id,
    output_format='mp4',
    fps=1,
    sources=['WV', 'S2', 'L8', 'PL'],  # noqa
):
    # Fetch the SiteEvaluation instance
    try:
        site_evaluation = SiteEvaluation.objects.get(id=site_evaluation_id)
    except SiteEvaluation.DoesNotExist:
        return

    # Determine the largest dimensions
    max_width, max_height = 0, 0
    images_data = []
    # Create a transformer from EPSG:3857 to EPSG:4326
    transformer = Transformer.from_crs('epsg:3857', 'epsg:4326', always_xy=True)

    images = SiteImage.objects.filter(
        site=site_evaluation_id, source__in=sources
    ).order_by('timestamp')
    for image_record in images:
        if image_record.image:
            img = Image.open(image_record.image)
            width, height = image_record.image_dimensions
            max_width = max(max_width, width)
            max_height = max(max_height, height)
            images_data.append((img, width, height, image_record))

    # Process each SiteObservation image
    frames = []
    np_array = []
    polygon = None
    point = None
    for img, width, height, image_record in images_data:
        # Resize image to max dimensions
        img = img.resize((max_width, max_height))
        draw = ImageDraw.Draw(img)

        # Extract image dimensions and bounding box
        if not image_record.image_dimensions or not image_record.image_bbox:
            continue

        bbox = image_record.image_bbox.extent  # minx, miny, maxx, maxy
        widthScale = max_width / width
        heightScale = max_height / height
        xScale = (width / (bbox[2] - bbox[0])) * widthScale
        yScale = (height / (bbox[3] - bbox[1])) * heightScale

        # Draw geometry or point on the image
        observation = image_record.observation
        if observation:
            polygon = observation.geom
            label = observation.label
            label_mapped = label_mapping.get(label.slug, {})
        elif not polygon:
            polygon = site_evaluation.geom
            site_evaluation.label
        if polygon:
            if polygon.geom_type == 'Polygon':
                base_coords = polygon.coords[0]
                transformed_coords = [
                    transformer.transform(lon, lat) for lon, lat in base_coords
                ]

                pixel_coords = [
                    to_pixel_coords(
                        lon,
                        lat,
                        bbox,
                        xScale,
                        yScale,
                    )
                    for lon, lat in transformed_coords
                ]
                color = label_mapped.get('color', 'white')
                draw.polygon(pixel_coords, outline=color)
        if not polygon:
            point = observation.point
        if not point:
            point = site_evaluation.point
        if point:
            transformed_point = transformer.transform(point.x, point.y)
            pixel_point = to_pixel_coords(
                transformed_point[0], transformed_point[1], bbox, xScale, yScale
            )
            draw.ellipse(
                (
                    pixel_point[0] - 5,
                    pixel_point[1] - 5,
                    pixel_point[0] + 5,
                    pixel_point[1] + 5,
                ),
                fill='blue',
            )

        # Drawing labels of timestamp and other imformation
        center = (max_width / 2.0, max_height / 2.0)
        # Draw date as 1/3 of the center of the image at the top
        date_width = max_width / 3.0
        date_height = max(max_height / 15.0, 10)
        date_box_point = (center[0] - (date_width / 2.0), 0)
        date_box_size = (date_width, date_height)
        draw_text_in_box(
            draw,
            image_record.timestamp.strftime('%Y-%m-%d'),
            date_box_point,
            date_box_size,
        )
        # Draw Source
        source_point = (0, 0)
        source_size = (max_width / 10.0, date_height)
        draw_text_in_box(
            draw,
            image_record.source,
            source_point,
            source_size,
        )
        # Draw Observation
        obs_width = max_width / 10.0
        obs_point = (max_width - obs_width, 0)
        obs_size = (max_width / 10.0, date_height)
        obs_text = '+obs'
        if image_record.observation is None:
            obs_text = '-obs'
        draw_text_in_box(
            draw,
            obs_text,
            obs_point,
            obs_size,
        )
        # Draw Label
        label_width = max_width / 3.0
        label_height = max(max_height / 15.0, 10)

        label_point = (center[0] - (label_width / 2.0), max_height - label_height)
        label_size = (label_width, label_height)
        if label_mapped:
            draw_text_in_box(
                draw,
                label_mapped['label'],
                label_point,
                label_size,
                label_mapped['color'],
            )

        frames.append(img)
        np_array.append(np.array(img))  # Convert PIL image to NumPy array

    # Save frames as an animated GIF
    if frames:
        output_dir = os.path.join('./', 'animations')
        os.makedirs(output_dir, exist_ok=True)
        if output_format == 'gif':
            output_file_path = os.path.join(output_dir, f'{uuid.uuid4()}.gif')
            frames[0].save(
                output_file_path,
                save_all=True,
                append_images=frames[1:],
                duration=1 / fps,
                loop=0,
                optimize=True,
                quality=100,
            )
        else:  # 'mp4'
            output_file_path = os.path.join(output_dir, f'{uuid.uuid4()}.mp4')

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                output_file_path, fourcc, 1, (max_width, max_height)
            )

            # Write each frame to the video
            for frame in np_array:
                frame_bgr = cv2.cvtColor(
                    frame, cv2.COLOR_RGB2BGR
                )  # Convert RGB to BGR for OpenCV
                video_writer.write(frame_bgr)

            video_writer.release()  # Close the video writer
        return output_file_path
