from dataclasses import dataclass
from math import hypot, sqrt

import numpy as np

from map_georeferencer.gcps import GroundControlPoint


@dataclass(frozen=True)
class AffineTransformation:
    """
    Two-dimensional affine transformation.

    The transformation is defined as:

    map_x = a0 + a1 * pixel_x + a2 * pixel_y
    map_y = b0 + b1 * pixel_x + b2 * pixel_y
    """

    a0: float
    a1: float
    a2: float
    b0: float
    b1: float
    b2: float

    def transform(
        self,
        pixel_x: float,
        pixel_y: float,
    ) -> tuple[float, float]:
        """Transform image coordinates into map coordinates."""

        map_x = (
            self.a0
            + self.a1 * pixel_x
            + self.a2 * pixel_y
        )

        map_y = (
            self.b0
            + self.b1 * pixel_x
            + self.b2 * pixel_y
        )

        return map_x, map_y


@dataclass(frozen=True)
class GCPResidual:
    """Residual error for one ground control point."""

    pixel_x: float
    pixel_y: float
    expected_x: float
    expected_y: float
    estimated_x: float
    estimated_y: float
    residual_x: float
    residual_y: float
    error: float


@dataclass(frozen=True)
class TransformationResult:
    """Affine transformation and its accuracy statistics."""

    transformation: AffineTransformation
    residuals: tuple[GCPResidual, ...]
    rmse: float


def estimate_affine_transformation(
    gcps: list[GroundControlPoint],
) -> TransformationResult:
    """
    Estimate a 2D affine transformation from ground control points.

    At least three control points are required. When more than three
    points are provided, the coefficients are estimated by least squares.

    Parameters
    ----------
    gcps:
        Ground control points relating image coordinates to map coordinates.

    Returns
    -------
    TransformationResult
        Estimated affine transformation, residuals and RMSE.

    Raises
    ------
    ValueError
        If fewer than three GCPs are provided or the control point
        configuration is geometrically degenerate.
    """

    if len(gcps) < 3:
        raise ValueError(
            "At least three ground control points are required "
            "to estimate an affine transformation."
        )

    design_matrix = np.array(
        [
            [1.0, gcp.pixel_x, gcp.pixel_y]
            for gcp in gcps
        ],
        dtype=float,
    )

    target_x = np.array(
        [gcp.map_x for gcp in gcps],
        dtype=float,
    )

    target_y = np.array(
        [gcp.map_y for gcp in gcps],
        dtype=float,
    )

    if np.linalg.matrix_rank(design_matrix) < 3:
        raise ValueError(
            "Ground control points are geometrically degenerate."
        )

    coefficients_x, _, _, _ = np.linalg.lstsq(
        design_matrix,
        target_x,
        rcond=None,
    )

    coefficients_y, _, _, _ = np.linalg.lstsq(
        design_matrix,
        target_y,
        rcond=None,
    )

    transformation = AffineTransformation(
        a0=float(coefficients_x[0]),
        a1=float(coefficients_x[1]),
        a2=float(coefficients_x[2]),
        b0=float(coefficients_y[0]),
        b1=float(coefficients_y[1]),
        b2=float(coefficients_y[2]),
    )

    residuals: list[GCPResidual] = []

    squared_errors = 0.0

    for gcp in gcps:
        estimated_x, estimated_y = transformation.transform(
            gcp.pixel_x,
            gcp.pixel_y,
        )

        residual_x = estimated_x - gcp.map_x
        residual_y = estimated_y - gcp.map_y

        error = hypot(
            residual_x,
            residual_y,
        )

        squared_errors += error**2

        residuals.append(
            GCPResidual(
                pixel_x=gcp.pixel_x,
                pixel_y=gcp.pixel_y,
                expected_x=gcp.map_x,
                expected_y=gcp.map_y,
                estimated_x=estimated_x,
                estimated_y=estimated_y,
                residual_x=residual_x,
                residual_y=residual_y,
                error=error,
            )
        )

    rmse = sqrt(
        squared_errors / len(gcps)
    )

    return TransformationResult(
        transformation=transformation,
        residuals=tuple(residuals),
        rmse=rmse,
    )