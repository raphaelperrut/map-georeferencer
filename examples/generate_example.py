from pathlib import Path

import numpy as np
import rasterio


EXAMPLES_DIR = Path(__file__).resolve().parent
GENERATED_DIR = EXAMPLES_DIR / "generated"

OUTPUT_PATH = GENERATED_DIR / "synthetic_map.tif"

WIDTH = 64
HEIGHT = 48


def create_synthetic_raster() -> None:
    """Create a deterministic synthetic RGB raster for demonstration."""

    GENERATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    x = np.arange(
        WIDTH,
        dtype=np.uint16,
    )

    y = np.arange(
        HEIGHT,
        dtype=np.uint16,
    )

    xx, yy = np.meshgrid(
        x,
        y,
    )

    red = (
        (xx * 4 + yy * 2)
        % 256
    ).astype(np.uint8)

    green = (
        (yy * 5 + 40)
        % 256
    ).astype(np.uint8)

    checkerboard = (
        (
            (xx // 8)
            + (yy // 8)
        )
        % 2
    )

    blue = np.where(
        checkerboard == 0,
        60,
        220,
    ).astype(np.uint8)

    data = np.stack(
        [
            red,
            green,
            blue,
        ]
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        driver="GTiff",
        width=WIDTH,
        height=HEIGHT,
        count=3,
        dtype=np.uint8,
    ) as dataset:
        dataset.write(data)

    print(
        f"Created synthetic raster: {OUTPUT_PATH}"
    )

    print(
        f"Size: {WIDTH} x {HEIGHT} pixels"
    )

    print(
        "Bands: 3 (RGB)"
    )


if __name__ == "__main__":
    create_synthetic_raster()