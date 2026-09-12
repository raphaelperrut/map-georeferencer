# Map Georeferencer

A Python toolkit for georeferencing raster maps and imagery from ground
control points, with affine transformation estimation, residual
analysis, RMSE calculation, north-up warping and GeoTIFF export.

The project is designed as a reproducible geospatial processing workflow
with a clean separation between control point validation, transformation
estimation, raster processing and command-line interaction.

## Features

-   Read and validate ground control points from CSV
-   Estimate 2D affine transformations using least squares
-   Detect geometrically degenerate control point configurations
-   Calculate per-GCP residuals
-   Calculate global positional RMSE
-   Assign affine georeferencing and CRS metadata
-   Warp rotated or sheared rasters to a north-up grid
-   Preserve multi-band raster data
-   Support configurable output resolution
-   Support nearest, bilinear and cubic resampling
-   Export georeferenced GeoTIFF files
-   Generate JSON accuracy reports
-   Command-line interface
-   Reproducible synthetic example
-   Automated tests

## Processing workflow

``` text
Raster image
    +
Ground control points
        │
        ▼
GCP validation
        │
        ▼
Affine transformation estimation
        │
        ▼
Residuals + RMSE
        │
        ▼
Georeferencing
        │
        ▼
North-up warp
        │
        ▼
GeoTIFF
        +
Accuracy report
```

The affine transformation is modeled as:

``` text
X = a0 + a1*x + a2*y
Y = b0 + b1*x + b2*y
```

where:

-   `x`, `y` are image pixel coordinates
-   `X`, `Y` are coordinates in the target reference system

When more than three GCPs are available, the transformation coefficients
are estimated using least squares.

## Requirements

-   Python 3.12+
-   NumPy
-   Rasterio
-   PyProj
-   Typer

Rasterio provides the GDAL-based raster processing backend used by the
project.

## Installation

Clone the repository:

``` bash
git clone https://github.com/raphaelperrut/map-georeferencer.git
cd map-georeferencer
```

Create and activate a virtual environment.

### Windows PowerShell

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the package:

``` powershell
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Verify the CLI:

``` powershell
map-georeferencer --help
```

Check the installed version:

``` powershell
map-georeferencer --version
```

## Quick start

The repository includes a fully reproducible synthetic example.

Generate the input raster:

``` powershell
python examples/generate_example.py
```

This creates:

``` text
examples/generated/synthetic_map.tif
```

Then run the complete georeferencing workflow:

``` powershell
map-georeferencer georeference `
    examples\generated\synthetic_map.tif `
    examples\control_points.csv `
    examples\generated\georeferenced_map.tif `
    --crs EPSG:31983 `
    --report examples\generated\accuracy_report.json
```

Expected output:

``` text
Output: ...\examples\generated\georeferenced_map.tif
RMSE: 0.000000
GCPs: 5
Report: ...\examples\generated\accuracy_report.json
```

The example uses synthetic GCPs generated from an exact affine
transformation, so the expected RMSE is approximately zero.

## Ground control point format

GCPs are provided as CSV files with four required columns:

``` csv
pixel_x,pixel_y,map_x,map_y
0,0,500000.0,7400000.0
64,0,500128.0,7400016.0
0,48,500016.8,7399904.0
64,48,500144.8,7399920.0
32,24,500072.4,7399960.0
```

  Column      Description
  ----------- -------------------------
  `pixel_x`   Image column coordinate
  `pixel_y`   Image row coordinate
  `map_x`     Target map X coordinate
  `map_y`     Target map Y coordinate

At least three distinct and non-collinear control points are required.

## CLI

General help:

``` powershell
map-georeferencer --help
```

Command help:

``` powershell
map-georeferencer georeference --help
```

Basic usage:

``` powershell
map-georeferencer georeference `
    input.tif `
    control_points.csv `
    output.tif `
    --crs EPSG:31983
```

### Output resolution

The output pixel size can be specified explicitly:

``` powershell
map-georeferencer georeference `
    input.tif `
    control_points.csv `
    output.tif `
    --crs EPSG:31983 `
    --resolution 1
```

If no resolution is provided, an approximate output resolution is
derived from the estimated affine transformation.

### Resampling

Available methods are `nearest`, `bilinear` and `cubic`. The default is
`bilinear`.

``` powershell
map-georeferencer georeference `
    input.tif `
    control_points.csv `
    output.tif `
    --crs EPSG:31983 `
    --resampling cubic
```

## Accuracy report

An optional JSON report can be generated with:

``` powershell
--report accuracy.json
```

The report includes the output raster path, GCP count, global RMSE,
affine transformation coefficients, expected and estimated coordinates,
X/Y residuals and Euclidean error for each GCP.

``` json
{
  "output_raster": "georeferenced_map.tif",
  "rmse": 0.42,
  "gcp_count": 5,
  "affine_transformation": {
    "a0": 500000.0,
    "a1": 2.0,
    "a2": 0.35,
    "b0": 7400000.0,
    "b1": 0.25,
    "b2": -2.0
  },
  "residuals": []
}
```

RMSE is calculated from the two-dimensional positional error of the
control points.

## Python API

``` python
from pathlib import Path
from map_georeferencer.pipeline import georeference_from_gcps

result = georeference_from_gcps(
    input_raster=Path("input.tif"),
    gcp_path=Path("control_points.csv"),
    output_path=Path("output.tif"),
    target_crs="EPSG:31983",
)

print(result.rmse)
print(result.output_path)
```

The returned result contains `output_path`, `transformation`,
`residuals` and `rmse`.

## Architecture

``` text
src/map_georeferencer/
├── cli.py
├── gcps.py
├── pipeline.py
├── raster.py
├── report.py
└── transform.py
```

-   `gcps.py` --- CSV parsing and GCP validation
-   `transform.py` --- affine estimation, residuals and RMSE
-   `raster.py` --- raster georeferencing and north-up warping
-   `pipeline.py` --- end-to-end workflow orchestration
-   `report.py` --- machine-readable accuracy reports
-   `cli.py` --- command-line interface

The CLI contains no georeferencing logic itself. It delegates processing
to the high-level pipeline API.

## Testing

Run the complete test suite:

``` powershell
pytest -v
```

The test suite covers GCP validation, malformed and non-finite
coordinates, duplicate and insufficient control points, collinearity,
affine estimation, residuals and RMSE, raster georeferencing, multi-band
preservation, CRS assignment, north-up warping, output resolution, the
end-to-end pipeline, CLI behavior, JSON reports and the reproducible
example.

## Example data

``` text
examples/
├── control_points.csv
└── generate_example.py
```

Generated outputs are written to `examples/generated/`. That directory
is excluded from version control because all example artifacts can be
reproduced locally.

## Current scope

Version `0.1.0` focuses on affine georeferencing from manually supplied
ground control points.

The current implementation intentionally does not include automatic
feature matching, projective or polynomial transformations, thin plate
spline transformations, automatic GCP detection, interactive GUI-based
GCP collection, or orthorectification using DEMs or sensor models. These
capabilities are outside the scope of the initial release.

## Development status

The core georeferencing workflow is implemented and under active
preparation for the first public release.

## License

MIT
