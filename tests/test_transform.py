import pytest

from map_georeferencer.gcps import GroundControlPoint
from map_georeferencer.transform import (
    AffineTransformation,
    estimate_affine_transformation,
)


def test_affine_transformation_transform() -> None:
    transformation = AffineTransformation(
        a0=1000.0,
        a1=2.0,
        a2=0.5,
        b0=2000.0,
        b1=-0.25,
        b2=3.0,
    )

    map_x, map_y = transformation.transform(
        10.0,
        20.0,
    )

    assert map_x == pytest.approx(1030.0)
    assert map_y == pytest.approx(2057.5)


def test_estimate_exact_affine_transformation() -> None:
    gcps = [
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=0.0,
            map_x=1000.0,
            map_y=2000.0,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=0.0,
            map_x=1200.0,
            map_y=1975.0,
        ),
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=100.0,
            map_x=1050.0,
            map_y=2300.0,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=100.0,
            map_x=1250.0,
            map_y=2275.0,
        ),
    ]

    result = estimate_affine_transformation(gcps)

    transformation = result.transformation

    assert transformation.a0 == pytest.approx(1000.0)
    assert transformation.a1 == pytest.approx(2.0)
    assert transformation.a2 == pytest.approx(0.5)

    assert transformation.b0 == pytest.approx(2000.0)
    assert transformation.b1 == pytest.approx(-0.25)
    assert transformation.b2 == pytest.approx(3.0)

    assert result.rmse == pytest.approx(
        0.0,
        abs=1e-9,
    )

    assert len(result.residuals) == 4


def test_estimate_affine_with_small_residuals() -> None:
    gcps = [
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=0.0,
            map_x=1000.2,
            map_y=1999.8,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=0.0,
            map_x=1199.9,
            map_y=1975.1,
        ),
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=100.0,
            map_x=1050.1,
            map_y=2299.9,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=100.0,
            map_x=1249.8,
            map_y=2275.2,
        ),
    ]

    result = estimate_affine_transformation(gcps)

    assert result.rmse > 0.0
    assert result.rmse < 1.0

    assert len(result.residuals) == 4


def test_fewer_than_three_gcps_raises_error() -> None:
    gcps = [
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=0.0,
            map_x=1000.0,
            map_y=2000.0,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=0.0,
            map_x=1200.0,
            map_y=1975.0,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="At least three",
    ):
        estimate_affine_transformation(gcps)


def test_collinear_gcps_raise_error() -> None:
    gcps = [
        GroundControlPoint(
            pixel_x=0.0,
            pixel_y=0.0,
            map_x=1000.0,
            map_y=2000.0,
        ),
        GroundControlPoint(
            pixel_x=100.0,
            pixel_y=100.0,
            map_x=1200.0,
            map_y=2200.0,
        ),
        GroundControlPoint(
            pixel_x=200.0,
            pixel_y=200.0,
            map_x=1400.0,
            map_y=2400.0,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="geometrically degenerate",
    ):
        estimate_affine_transformation(gcps)