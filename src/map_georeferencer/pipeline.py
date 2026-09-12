from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from rasterio.enums import Resampling

from map_georeferencer.gcps import read_gcps
from map_georeferencer.raster import (
    georeference_raster,
    warp_to_north_up,
)
from map_georeferencer.transform import (
    AffineTransformation,
    GCPResidual,
    estimate_affine_transformation,
)


@dataclass(frozen=True)
class GeoreferencingResult:
    """Result of a complete raster georeferencing workflow."""

    output_path: Path
    transformation: AffineTransformation
    residuals: tuple[GCPResidual, ...]
    rmse: float


def georeference_from_gcps(
    input_raster: Path,
    gcp_path: Path,
    output_path: Path,
    target_crs: str,
    resolution: float | None = None,
    resampling: Resampling = Resampling.bilinear,
) -> GeoreferencingResult:
    """
    Georeference a raster from ground control points.

    This workflow:

    1. Reads and validates ground control points.
    2. Estimates an affine transformation.
    3. Assigns the transformation and target CRS to the source raster.
    4. Warps the raster to a regular north-up grid.
    5. Returns transformation accuracy information.

    Parameters
    ----------
    input_raster:
        Path to the source raster.
    gcp_path:
        Path to the CSV containing ground control points.
    output_path:
        Path for the final north-up GeoTIFF.
    target_crs:
        Coordinate reference system of the map coordinates,
        for example ``EPSG:31983``.
    resolution:
        Optional output pixel size in target CRS units.
    resampling:
        Rasterio resampling method used during warping.

    Returns
    -------
    GeoreferencingResult
        Output path, affine transformation, GCP residuals and RMSE.
    """

    gcps = read_gcps(gcp_path)

    transformation_result = (
        estimate_affine_transformation(gcps)
    )

    output_path = output_path.resolve()

    with TemporaryDirectory() as temporary_directory:
        temporary_path = (
            Path(temporary_directory)
            / "georeferenced_intermediate.tif"
        )

        georeference_raster(
            input_path=input_raster,
            output_path=temporary_path,
            transformation=(
                transformation_result.transformation
            ),
            target_crs=target_crs,
        )

        warp_to_north_up(
            input_path=temporary_path,
            output_path=output_path,
            resolution=resolution,
            resampling=resampling,
        )

    return GeoreferencingResult(
        output_path=output_path,
        transformation=(
            transformation_result.transformation
        ),
        residuals=transformation_result.residuals,
        rmse=transformation_result.rmse,
    )