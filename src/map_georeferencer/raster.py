from pathlib import Path
from math import ceil, floor

import rasterio
from affine import Affine
from rasterio.crs import CRS
from rasterio.errors import RasterioIOError
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
from rasterio.warp import reproject

from map_georeferencer.transform import AffineTransformation


def to_rasterio_affine(
    transformation: AffineTransformation,
) -> Affine:
    """
    Convert the internal affine transformation to Rasterio format.

    Internal model:

        map_x = a0 + a1 * pixel_x + a2 * pixel_y
        map_y = b0 + b1 * pixel_x + b2 * pixel_y

    Rasterio Affine model:

        map_x = a * column + b * row + c
        map_y = d * column + e * row + f
    """

    return Affine(
        transformation.a1,
        transformation.a2,
        transformation.a0,
        transformation.b1,
        transformation.b2,
        transformation.b0,
    )


def georeference_raster(
    input_path: Path,
    output_path: Path,
    transformation: AffineTransformation,
    target_crs: str,
) -> None:
    """
    Assign an affine georeferencing transformation and CRS to a raster.

    Pixel values are preserved exactly. No resampling or reprojection
    is performed at this stage.

    Parameters
    ----------
    input_path:
        Source raster image.
    output_path:
        Destination GeoTIFF path.
    transformation:
        Affine transformation mapping pixel coordinates to map coordinates.
    target_crs:
        Target coordinate reference system, for example ``EPSG:31983``.

    Raises
    ------
    ValueError
        If the input raster cannot be found/read or the CRS is invalid.
    """

    if not input_path.exists():
        raise ValueError(
            f"Input raster does not exist: {input_path}"
        )

    try:
        crs = CRS.from_user_input(target_crs)
    except Exception as exc:
        raise ValueError(
            f"Invalid target CRS: {target_crs}"
        ) from exc

    raster_transform = to_rasterio_affine(
        transformation
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with rasterio.open(input_path) as source:
            profile = source.profile.copy()

            profile.update(
                driver="GTiff",
                crs=crs,
                transform=raster_transform,
            )

            with rasterio.open(
                output_path,
                "w",
                **profile,
            ) as destination:
                for band_index in range(
                    1,
                    source.count + 1,
                ):
                    destination.write(
                        source.read(band_index),
                        band_index,
                    )

    except RasterioIOError as exc:
        raise ValueError(
            f"Unable to read raster: {input_path}"
        ) from exc

def warp_to_north_up(
    input_path: Path,
    output_path: Path,
    resolution: float | None = None,
    resampling: Resampling = Resampling.bilinear,
) -> None:
    """
    Warp a georeferenced raster to a north-up regular grid.

    The source and destination CRS remain the same. This operation
    removes raster rotation and shear by resampling the source into
    an axis-aligned grid.

    Parameters
    ----------
    input_path:
        Georeferenced source raster.
    output_path:
        Destination GeoTIFF.
    resolution:
        Output pixel size in map units. If omitted, an approximate
        resolution is derived from the source transform.
    resampling:
        Rasterio resampling method.

    Raises
    ------
    ValueError
        If the input raster does not exist, is not georeferenced,
        or the requested resolution is invalid.
    """

    if not input_path.exists():
        raise ValueError(
            f"Input raster does not exist: {input_path}"
        )

    if resolution is not None and resolution <= 0:
        raise ValueError(
            "Resolution must be greater than zero."
        )

    try:
        with rasterio.open(input_path) as source:
            if source.crs is None:
                raise ValueError(
                    "Input raster has no coordinate reference system."
                )

            transform = source.transform

            if resolution is None:
                pixel_width = (
                    transform.a**2
                    + transform.d**2
                ) ** 0.5

                pixel_height = (
                    transform.b**2
                    + transform.e**2
                ) ** 0.5

                resolution = (
                    pixel_width
                    + pixel_height
                ) / 2.0

            left, bottom, right, top = array_bounds(
                source.height,
                source.width,
                transform,
            )

            left = floor(left / resolution) * resolution
            bottom = floor(bottom / resolution) * resolution
            right = ceil(right / resolution) * resolution
            top = ceil(top / resolution) * resolution

            width = int(
                ceil(
                    (right - left)
                    / resolution
                )
            )

            height = int(
                ceil(
                    (top - bottom)
                    / resolution
                )
            )

            destination_transform = Affine(
                resolution,
                0.0,
                left,
                0.0,
                -resolution,
                top,
            )

            profile = source.profile.copy()

            profile.update(
                driver="GTiff",
                width=width,
                height=height,
                transform=destination_transform,
                crs=source.crs,
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with rasterio.open(
                output_path,
                "w",
                **profile,
            ) as destination:
                for band_index in range(
                    1,
                    source.count + 1,
                ):
                    reproject(
                        source=rasterio.band(
                            source,
                            band_index,
                        ),
                        destination=rasterio.band(
                            destination,
                            band_index,
                        ),
                        src_transform=source.transform,
                        src_crs=source.crs,
                        dst_transform=destination_transform,
                        dst_crs=source.crs,
                        resampling=resampling,
                    )

    except RasterioIOError as exc:
        raise ValueError(
            f"Unable to read raster: {input_path}"
        ) from exc