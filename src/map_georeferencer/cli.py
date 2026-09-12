from pathlib import Path

import typer
from rasterio.enums import Resampling

from map_georeferencer import __version__
from map_georeferencer.pipeline import (
    georeference_from_gcps,
)


app = typer.Typer(
    help=(
        "Georeference raster maps and imagery "
        "from ground control points."
    )
)


RESAMPLING_METHODS = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "cubic": Resampling.cubic,
}


def version_callback(
    value: bool,
) -> None:
    """Print the application version and exit."""

    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the application version and exit.",
    ),
) -> None:
    """Map Georeferencer command-line interface."""


@app.command()
def georeference(
    input_raster: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input raster image.",
    ),
    gcps: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="CSV file containing ground control points.",
    ),
    output: Path = typer.Argument(
        ...,
        help="Output north-up GeoTIFF.",
    ),
    crs: str = typer.Option(
        ...,
        "--crs",
        help=(
            "CRS of the map coordinates, "
            "for example EPSG:31983."
        ),
    ),
    resolution: float | None = typer.Option(
        None,
        "--resolution",
        min=0.0000001,
        help=(
            "Optional output pixel size "
            "in target CRS units."
        ),
    ),
    resampling: str = typer.Option(
        "bilinear",
        "--resampling",
        help=(
            "Resampling method: nearest, "
            "bilinear or cubic."
        ),
    ),
) -> None:
    """Georeference a raster from ground control points."""

    method = RESAMPLING_METHODS.get(
        resampling.lower()
    )

    if method is None:
        valid_methods = ", ".join(
            RESAMPLING_METHODS
        )

        raise typer.BadParameter(
            "Unknown resampling method. "
            f"Choose one of: {valid_methods}."
        )

    try:
        result = georeference_from_gcps(
            input_raster=input_raster,
            gcp_path=gcps,
            output_path=output,
            target_crs=crs,
            resolution=resolution,
            resampling=method,
        )
    except ValueError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )

        raise typer.Exit(
            code=1
        ) from exc

    typer.echo(
        f"Output: {result.output_path}"
    )

    typer.echo(
        f"RMSE: {result.rmse:.6f}"
    )

    typer.echo(
        f"GCPs: {len(result.residuals)}"
    )


if __name__ == "__main__":
    app()