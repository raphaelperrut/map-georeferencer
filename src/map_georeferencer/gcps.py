import csv
from dataclasses import dataclass
from math import isfinite
from pathlib import Path


REQUIRED_COLUMNS = (
    "pixel_x",
    "pixel_y",
    "map_x",
    "map_y",
)


@dataclass(frozen=True)
class GroundControlPoint:
    """Ground control point linking image and map coordinates."""

    pixel_x: float
    pixel_y: float
    map_x: float
    map_y: float


def read_gcps(
    input_path: Path,
) -> list[GroundControlPoint]:
    """
    Read and validate ground control points from a CSV file.

    The CSV must contain the following columns:

    - pixel_x
    - pixel_y
    - map_x
    - map_y

    At least three valid and distinct control points are required.

    Parameters
    ----------
    input_path:
        Path to the CSV file containing ground control points.

    Returns
    -------
    list[GroundControlPoint]
        Validated ground control points.

    Raises
    ------
    ValueError
        If the file does not exist, required columns are missing,
        coordinates are invalid, or fewer than three control points
        are provided.
    """

    if not input_path.exists():
        raise ValueError(
            f"Control point file does not exist: {input_path}"
        )

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "Control point file has no header."
            )

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            missing = ", ".join(missing_columns)

            raise ValueError(
                f"Missing required columns: {missing}"
            )

        gcps: list[GroundControlPoint] = []

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                values = {
                    column: float(row[column])
                    for column in REQUIRED_COLUMNS
                }
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid numeric value "
                    f"at CSV row {row_number}."
                ) from exc

            if not all(
                isfinite(value)
                for value in values.values()
            ):
                raise ValueError(
                    "Coordinates must be finite numbers "
                    f"at CSV row {row_number}."
                )

            gcps.append(
                GroundControlPoint(
                    pixel_x=values["pixel_x"],
                    pixel_y=values["pixel_y"],
                    map_x=values["map_x"],
                    map_y=values["map_y"],
                )
            )

    if len(gcps) < 3:
        raise ValueError(
            "At least three ground control points are required."
        )

    pixel_coordinates = {
        (gcp.pixel_x, gcp.pixel_y)
        for gcp in gcps
    }

    if len(pixel_coordinates) != len(gcps):
        raise ValueError(
            "Duplicate image coordinates are not allowed."
        )

    return gcps