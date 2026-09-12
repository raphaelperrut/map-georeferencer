from pathlib import Path

import rasterio
from affine import Affine
from rasterio.crs import CRS
from rasterio.errors import RasterioIOError

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