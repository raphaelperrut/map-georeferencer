from pathlib import Path

import numpy as np
import rasterio
from typer.testing import CliRunner

from map_georeferencer.cli import app


runner = CliRunner()


def create_input_raster(
    path: Path,
) -> None:
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


def test_georeference_command(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"

    create_input_raster(input_path)
    create_gcp_file(gcp_path)

    result = runner.invoke(
        app,
        [
            "georeference",
            str(input_path),
            str(gcp_path),
            str(output_path),
            "--crs",
            "EPSG:31983",
        ],
    )

    assert result.exit_code == 0

    assert output_path.exists()

    assert "Output:" in result.stdout
    assert "RMSE:" in result.stdout
    assert "GCPs: 4" in result.stdout


def test_invalid_resampling_method(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"

    create_input_raster(input_path)
    create_gcp_file(gcp_path)

    result = runner.invoke(
        app,
        [
            "georeference",
            str(input_path),
            str(gcp_path),
            str(output_path),
            "--crs",
            "EPSG:31983",
            "--resampling",
            "invalid",
        ],
    )

    assert result.exit_code != 0

    assert (
        "Unknown resampling method"
        in result.output
    )


def test_invalid_gcps_return_error(
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

    result = runner.invoke(
        app,
        [
            "georeference",
            str(input_path),
            str(gcp_path),
            str(output_path),
            "--crs",
            "EPSG:31983",
        ],
    )

    assert result.exit_code == 1

    assert "At least three" in result.output

    assert not output_path.exists()

def test_georeference_command_writes_report(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "input.tif"
    gcp_path = tmp_path / "gcps.csv"
    output_path = tmp_path / "output.tif"
    report_path = tmp_path / "accuracy.json"

    create_input_raster(input_path)
    create_gcp_file(gcp_path)

    result = runner.invoke(
        app,
        [
            "georeference",
            str(input_path),
            str(gcp_path),
            str(output_path),
            "--crs",
            "EPSG:31983",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0

    assert output_path.exists()
    assert report_path.exists()

    assert "Report:" in result.stdout