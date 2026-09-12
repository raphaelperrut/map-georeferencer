from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from map_georeferencer.raster import (
    georeference_raster,
    to_rasterio_affine,
    warp_to_north_up,
)
from map_georeferencer.transform import (
    AffineTransformation,
)


def create_test_raster(
    path: Path,
) -> np.ndarray:
    data = np.array(
        [
            [10, 20, 30],
            [40, 50, 60],
            [70, 80, 90],
        ],
        dtype=np.uint8,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=3,
        height=3,
        count=1,
        dtype=data.dtype,
    ) as dataset:
        dataset.write(
            data,
            1,
        )

    return data


def test_to_rasterio_affine() -> None:
    transformation = AffineTransformation(
        a0=1000.0,
        a1=2.0,
        a2=0.5,
        b0=2000.0,
        b1=-0.25,
        b2=-3.0,
    )

    result = to_rasterio_affine(
        transformation
    )

    expected = Affine(
        2.0,
        0.5,
        1000.0,
        -0.25,
        -3.0,
        2000.0,
    )

    assert result == expected


def test_georeference_raster(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    output_path = tmp_path / "output.tif"

    original_data = create_test_raster(
        input_path
    )

    transformation = AffineTransformation(
        a0=191000.0,
        a1=1.0,
        a2=0.0,
        b0=8252000.0,
        b1=0.0,
        b2=-1.0,
    )

    georeference_raster(
        input_path=input_path,
        output_path=output_path,
        transformation=transformation,
        target_crs="EPSG:31983",
    )

    assert output_path.exists()

    with rasterio.open(output_path) as dataset:
        assert dataset.crs is not None
        assert dataset.crs.to_epsg() == 31983

        assert dataset.transform == Affine(
            1.0,
            0.0,
            191000.0,
            0.0,
            -1.0,
            8252000.0,
        )

        output_data = dataset.read(1)

    assert np.array_equal(
        output_data,
        original_data,
    )


def test_georeference_preserves_multiple_bands(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "rgb.tif"
    output_path = tmp_path / "output.tif"

    data = np.array(
        [
            [
                [10, 20],
                [30, 40],
            ],
            [
                [50, 60],
                [70, 80],
            ],
            [
                [90, 100],
                [110, 120],
            ],
        ],
        dtype=np.uint8,
    )

    with rasterio.open(
        input_path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=3,
        dtype=data.dtype,
    ) as dataset:
        dataset.write(data)

    transformation = AffineTransformation(
        a0=500000.0,
        a1=2.0,
        a2=0.0,
        b0=7400000.0,
        b1=0.0,
        b2=-2.0,
    )

    georeference_raster(
        input_path,
        output_path,
        transformation,
        "EPSG:31983",
    )

    with rasterio.open(output_path) as dataset:
        result = dataset.read()

        assert dataset.count == 3

    assert np.array_equal(
        result,
        data,
    )


def test_missing_input_raster_raises_error(
    tmp_path: Path,
) -> None:
    transformation = AffineTransformation(
        a0=0.0,
        a1=1.0,
        a2=0.0,
        b0=0.0,
        b1=0.0,
        b2=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        georeference_raster(
            input_path=tmp_path / "missing.tif",
            output_path=tmp_path / "output.tif",
            transformation=transformation,
            target_crs="EPSG:31983",
        )


def test_invalid_target_crs_raises_error(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"

    create_test_raster(input_path)

    transformation = AffineTransformation(
        a0=0.0,
        a1=1.0,
        a2=0.0,
        b0=0.0,
        b1=0.0,
        b2=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="Invalid target CRS",
    ):
        georeference_raster(
            input_path=input_path,
            output_path=tmp_path / "output.tif",
            transformation=transformation,
            target_crs="INVALID_CRS",
        )

def test_warp_to_north_up_removes_rotation(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "rotated.tif"
    output_path = tmp_path / "north_up.tif"

    data = np.arange(
        100,
        dtype=np.uint8,
    ).reshape(
        10,
        10,
    )

    rotated_transform = Affine(
        0.95,
        0.25,
        500000.0,
        0.25,
        -0.95,
        7400000.0,
    )

    with rasterio.open(
        input_path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:31983",
        transform=rotated_transform,
    ) as dataset:
        dataset.write(
            data,
            1,
        )

    warp_to_north_up(
        input_path,
        output_path,
    )

    assert output_path.exists()

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

        assert dataset.width > 0
        assert dataset.height > 0


def test_warp_to_north_up_uses_requested_resolution(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    output_path = tmp_path / "output.tif"

    data = np.ones(
        (10, 10),
        dtype=np.uint8,
    )

    transform = Affine(
        2.0,
        0.0,
        500000.0,
        0.0,
        -2.0,
        7400000.0,
    )

    with rasterio.open(
        input_path,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:31983",
        transform=transform,
    ) as dataset:
        dataset.write(
            data,
            1,
        )

    warp_to_north_up(
        input_path,
        output_path,
        resolution=1.0,
    )

    with rasterio.open(output_path) as dataset:
        assert dataset.transform.a == pytest.approx(
            1.0
        )
        assert dataset.transform.e == pytest.approx(
            -1.0
        )


def test_warp_preserves_multiple_bands(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "rgb.tif"
    output_path = tmp_path / "output.tif"

    data = np.array(
        [
            [
                [10, 20],
                [30, 40],
            ],
            [
                [50, 60],
                [70, 80],
            ],
            [
                [90, 100],
                [110, 120],
            ],
        ],
        dtype=np.uint8,
    )

    with rasterio.open(
        input_path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=3,
        dtype=data.dtype,
        crs="EPSG:31983",
        transform=Affine(
            2.0,
            0.5,
            500000.0,
            0.0,
            -2.0,
            7400000.0,
        ),
    ) as dataset:
        dataset.write(data)

    warp_to_north_up(
        input_path,
        output_path,
    )

    with rasterio.open(output_path) as dataset:
        assert dataset.count == 3


def test_warp_missing_input_raises_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        warp_to_north_up(
            tmp_path / "missing.tif",
            tmp_path / "output.tif",
        )


def test_warp_invalid_resolution_raises_error(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"

    create_test_raster(input_path)

    with pytest.raises(
        ValueError,
        match="Resolution must be greater than zero",
    ):
        warp_to_north_up(
            input_path,
            tmp_path / "output.tif",
            resolution=0.0,
        )