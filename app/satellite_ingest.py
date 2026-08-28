"""
Satellite image ingestion.

Real mode: pulls a Sentinel-2 L2A RGB composite via the `sentinelhub` package.
Mock mode (default, no SH_CLIENT_ID/SECRET set): generates a synthetic PNG so
the rest of the pipeline can be exercised without any cloud credentials.
"""
import os
import random
from PIL import Image, ImageDraw

from app.config import SENTINEL_HUB_ENABLED, DATA_DIR


def fetch_satellite_image(region_id: str, bbox_coords, date: str) -> str:
    """
    bbox_coords: [min_lon, min_lat, max_lon, max_lat]
    date: 'YYYY-MM-DD'
    Returns the local path of the saved image.
    """
    output_path = os.path.join(DATA_DIR, f"{region_id}_{date}.png")

    if SENTINEL_HUB_ENABLED:
        return _fetch_real(bbox_coords, date, output_path)
    return _fetch_mock(region_id, output_path)


def _fetch_real(bbox_coords, date, output_path):
    from sentinelhub import SentinelHubRequest, BBox, CRS, MimeType, DataCollection, SHConfig

    config = SHConfig()
    # SH_CLIENT_ID / SH_CLIENT_SECRET are read from env by SHConfig automatically
    # if configured via `sentinelhub.config` CLI, or set them explicitly here.

    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    request = SentinelHubRequest(
        evalscript="""
            //VERSION=3
            function setup() {
                return { input: ["B02", "B03", "B04"], output: { bands: 3 } };
            }
            function evaluatePixel(sample) {
                return [sample.B04, sample.B03, sample.B02];
            }
        """,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(date, date),
                maxcc=0.3,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=(512, 512),
        config=config,
    )
    image = request.get_data()[0]
    Image.fromarray(image).save(output_path)
    return output_path


def _fetch_mock(region_id: str, output_path: str) -> str:
    """Generates a plausible-looking synthetic satellite tile for demos/tests."""
    random.seed(region_id)  # deterministic-ish per region so repeat runs are stable-ish
    img = Image.new("RGB", (512, 512), (90, 110, 90))  # terrain green/brown base
    draw = ImageDraw.Draw(img)

    # Fake a lake as a blue blob whose size varies slightly run to run
    cx, cy = 256, 256
    r = random.randint(60, 90)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 90, 160))

    # Occasionally draw a "new channel" line leading away from the lake
    if random.random() > 0.5:
        draw.line([cx + r, cy, cx + r + 80, cy + random.randint(-40, 40)], fill=(40, 90, 160), width=6)

    img.save(output_path)
    return output_path
