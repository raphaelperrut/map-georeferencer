from pathlib import Path

import numpy as np
import pytest
import rasterio

from map_georeferencer.pipeline import (
    georeference_from_gcps,
)


def create_input_raster(
    path: Path,
) -> np.ndarray:
    data = np.arange(
        100,
        dtype=np.uint8,
    ).reshape(
        10,
        10,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype=data.dtype,
    ) as dataset:
        dataset.write(
            data,
            1,
        )

    return data


def create_gcp_file(
    path: Path,
) -> None:
    path.write_text(
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "0,0,500000,7400000\n"
            "10,0,500020,7400000\n"
            "0,10,500000,7399980\n"
            "10,10,500020,7399980\n"
        ),
        encoding="utf-8",
    )


def test_georeference_from_gcps(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"

    create_input_raster(input_path)
    create_gcp_file(gcp_path)

    result = georeference_from_gcps(
        input_raster=input_path,
        gcp_path=gcp_path,
        output_path=output_path,
        target_crs="EPSG:31983",
    )

    assert output_path.exists()

    assert result.output_path == output_path.resolve()

    assert result.rmse == pytest.approx(
        0.0,
        abs=1e-9,
    )

    assert len(result.residuals) == 4

    assert result.transformation.a0 == pytest.approx(
        500000.0
    )
    assert result.transformation.a1 == pytest.approx(
        2.0
    )
    assert result.transformation.a2 == pytest.approx(
        0.0,
        abs=1e-9,
    )

    assert result.transformation.b0 == pytest.approx(
        7400000.0
    )
    assert result.transformation.b1 == pytest.approx(
        0.0,
        abs=1e-9,
    )
    assert result.transformation.b2 == pytest.approx(
        -2.0
    )

    with rasterio.open(output_path) as dataset:
        assert dataset.crs is not None
        assert dataset.crs.to_epsg() == 31983

        assert dataset.transform.b == pytest.approx(
            0.0
        )

        assert dataset.transform.d == pytest.approx(
            0.0
        )

        assert dataset.transform.a > 0
        assert dataset.transform.e < 0


def test_pipeline_uses_requested_resolution(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"

    create_input_raster(input_path)
    create_gcp_file(gcp_path)

    georeference_from_gcps(
        input_raster=input_path,
        gcp_path=gcp_path,
        output_path=output_path,
        target_crs="EPSG:31983",
        resolution=1.0,
    )

    with rasterio.open(output_path) as dataset:
        assert dataset.transform.a == pytest.approx(
            1.0
        )

        assert dataset.transform.e == pytest.approx(
            -1.0
        )


def test_pipeline_propagates_invalid_gcps(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"

    create_input_raster(input_path)

    gcp_path.write_text(
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "0,0,500000,7400000\n"
            "10,0,500020,7400000\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="At least three",
    ):
        georeference_from_gcps(
            input_raster=input_path,
            gcp_path=gcp_path,
            output_path=output_path,
            target_crs="EPSG:31983",
        )

    assert not output_path.exists()