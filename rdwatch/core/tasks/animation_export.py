import os
import uuid

from celery import shared_task
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

from rdwatch.core.models import SiteEvaluation, SiteImage


def to_pixel_coords(lon, lat, bbox, xScale, yScale):
    x = (lon - bbox[0]) * xScale
    y = (lat - bbox[1]) * yScale
    return x, y


def draw_text_in_box(
    draw, text, position, box_size, font_path=None, initial_font_size=30
):
    """
    Draws text within a given box with adjustable font size.

    :param draw: ImageDraw object to draw on the image.
    :param text: Text to draw.
    :param position: Position (x, y) to start drawing text.
    :param box_size: Tuple (width, height) specifying the box size.
    :param font_path: Path to a .ttf font file, or None to use default font.
    :param initial_font_size: Starting font size.
    """
    width, height = box_size

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
    while (text_width > width or text_height > height) and initial_font_size > 10:
        initial_font_size -= 2
        font = (
            ImageFont.truetype(font_path, initial_font_size)
            if font_path
            else ImageFont.load_default()
        )
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

    # Draw text
    draw.text(position, text, font=font, fill=(255, 255, 255))  # White text


def wrap_text(text, font, max_width):
    """
    Wraps text to fit within a given width.
    :param text: Text to wrap.
    :param font: Font object.
    :param max_width: Maximum width for the text.
    :return: List of lines with wrapped text.
    """
    lines = []
    words = text.split(' ')
    line = ''
    for word in words:
        test_line = line + word + ' '
        if font.getbbox(test_line)[2] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word + ' '
    lines.append(line)
    return lines


@shared_task
def create_animated_gif(
    site_evaluation_id,
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
            observation.label
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
                draw.polygon(pixel_coords, outline='white')
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
        date_height = max(max_height / 10.0, 20)
        date_box_point = (center[0] - (date_width / 2.0), 0)
        date_box_size = (date_width, date_height)
        draw_text_in_box(
            draw,
            image_record.timestamp.strftime('%Y-%m-%d'),
            date_box_point,
            date_box_size,
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
            duration=750,
            loop=0,
        )
        return output_file_path
