import json
from pathlib import Path

import pytest

from map_georeferencer.pipeline import (
    GeoreferencingResult,
)
from map_georeferencer.report import (
    write_accuracy_report,
)
from map_georeferencer.transform import (
    AffineTransformation,
    GCPResidual,
)


def create_result(
    output_path: Path,
) -> GeoreferencingResult:
    transformation = AffineTransformation(
        a0=500000.0,
        a1=2.0,
        a2=0.0,
        b0=7400000.0,
        b1=0.0,
        b2=-2.0,
    )

    residual = GCPResidual(
        pixel_x=10.0,
        pixel_y=20.0,
        expected_x=500020.0,
        expected_y=7399960.0,
        estimated_x=500020.2,
        estimated_y=7399959.9,
        residual_x=0.2,
        residual_y=-0.1,
        error=0.22360679775,
    )

    return GeoreferencingResult(
        output_path=output_path,
        transformation=transformation,
        residuals=(residual,),
        rmse=0.22360679775,
    )


def test_write_accuracy_report(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.json"

    result = create_result(
        tmp_path / "output.tif"
    )

    write_accuracy_report(
        result,
        report_path,
    )

    assert report_path.exists()

    report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    assert report["gcp_count"] == 1

    assert report["rmse"] == pytest.approx(
        0.22360679775
    )

    assert (
        report["affine_transformation"]["a0"]
        == pytest.approx(500000.0)
    )

    assert (
        report["affine_transformation"]["a1"]
        == pytest.approx(2.0)
    )

    assert len(report["residuals"]) == 1

    assert (
        report["residuals"][0]["error"]
        == pytest.approx(0.22360679775)
    )


def test_write_accuracy_report_creates_parent_directory(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "reports"
        / "accuracy.json"
    )

    result = create_result(
        tmp_path / "output.tif"
    )

    write_accuracy_report(
        result,
        report_path,
    )

    assert report_path.exists()