from pathlib import Path

import numpy as np
import rasterio

from map_georeferencer.pipeline import (
    georeference_from_gcps,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

WIDTH = 64
HEIGHT = 48


def test_reproducible_example(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    output_path = tmp_path / "output.tif"

    gcp_path = (
        PROJECT_ROOT
        / "examples"
        / "control_points.csv"
    )

    data = np.zeros(
        (3, HEIGHT, WIDTH),
        dtype=np.uint8,
    )

    with rasterio.open(
        input_path,
        "w",
        driver="GTiff",
        width=WIDTH,
        height=HEIGHT,
        count=3,
        dtype=np.uint8,
    ) as dataset:
        dataset.write(data)

    result = georeference_from_gcps(
        input_raster=input_path,
        gcp_path=gcp_path,
        output_path=output_path,
        target_crs="EPSG:31983",
    )

    assert output_path.exists()

    assert result.rmse < 1e-8

    assert len(result.residuals) == 5

    with rasterio.open(output_path) as dataset:
        assert dataset.crs is not None
        assert dataset.crs.to_epsg() == 31983

        assert dataset.transform.b == 0.0
        assert dataset.transform.d == 0.0

        assert dataset.count == 3