import json
from pathlib import Path

from map_georeferencer.pipeline import (
    GeoreferencingResult,
)


def write_accuracy_report(
    result: GeoreferencingResult,
    output_path: Path,
) -> None:
    """
    Write georeferencing accuracy information to a JSON file.

    Parameters
    ----------
    result:
        Result returned by the georeferencing pipeline.
    output_path:
        Destination JSON report.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transformation = result.transformation

    report = {
        "output_raster": str(result.output_path),
        "rmse": result.rmse,
        "gcp_count": len(result.residuals),
        "affine_transformation": {
            "a0": transformation.a0,
            "a1": transformation.a1,
            "a2": transformation.a2,
            "b0": transformation.b0,
            "b1": transformation.b1,
            "b2": transformation.b2,
        },
        "residuals": [
            {
                "pixel_x": residual.pixel_x,
                "pixel_y": residual.pixel_y,
                "expected_x": residual.expected_x,
                "expected_y": residual.expected_y,
                "estimated_x": residual.estimated_x,
                "estimated_y": residual.estimated_y,
                "residual_x": residual.residual_x,
                "residual_y": residual.residual_y,
                "error": residual.error,
            }
            for residual in result.residuals
        ],
    }

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )