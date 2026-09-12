from pathlib import Path

import pytest

from map_georeferencer.gcps import (
    GroundControlPoint,
    read_gcps,
)


def write_csv(
    path: Path,
    content: str,
) -> Path:
    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def test_read_valid_gcps(
    tmp_path: Path,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "100,100,1000,2000\n"
            "200,100,1100,2000\n"
            "100,200,1000,1900\n"
        ),
    )

    gcps = read_gcps(input_path)

    assert len(gcps) == 3

    assert gcps[0] == GroundControlPoint(
        pixel_x=100.0,
        pixel_y=100.0,
        map_x=1000.0,
        map_y=2000.0,
    )


def test_missing_file_raises_error(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "missing.csv"

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        read_gcps(input_path)


def test_missing_required_column_raises_error(
    tmp_path: Path,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x\n"
            "100,100,1000\n"
            "200,100,1100\n"
            "100,200,1000\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        read_gcps(input_path)


def test_invalid_numeric_value_raises_error(
    tmp_path: Path,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "100,100,1000,2000\n"
            "invalid,100,1100,2000\n"
            "100,200,1000,1900\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Invalid numeric value",
    ):
        read_gcps(input_path)


@pytest.mark.parametrize(
    "invalid_value",
    [
        "nan",
        "inf",
        "-inf",
    ],
)
def test_non_finite_coordinate_raises_error(
    tmp_path: Path,
    invalid_value: str,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            f"{invalid_value},100,1000,2000\n"
            "200,100,1100,2000\n"
            "100,200,1000,1900\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="finite numbers",
    ):
        read_gcps(input_path)


def test_fewer_than_three_gcps_raises_error(
    tmp_path: Path,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "100,100,1000,2000\n"
            "200,100,1100,2000\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="At least three",
    ):
        read_gcps(input_path)


def test_duplicate_image_coordinates_raise_error(
    tmp_path: Path,
) -> None:
    input_path = write_csv(
        tmp_path / "gcps.csv",
        (
            "pixel_x,pixel_y,map_x,map_y\n"
            "100,100,1000,2000\n"
            "100,100,1100,2000\n"
            "100,200,1000,1900\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Duplicate image coordinates",
    ):
        read_gcps(input_path)