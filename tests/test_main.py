from pathlib import Path

import json
import matplotlib
import numpy as np
import pytest
import subprocess
import sys

matplotlib.use("Agg")  # Use a non-interactive backend for tests.

from ggg_spectra.main import pretty_species_name, read_spt, save_matplotlib_plot


SPECTRA_DIR = Path(__file__).parents[1] / "ggg_spectra" / "spectra"
SPECTRUM_FILES = sorted(SPECTRA_DIR.iterdir())


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("H2O", "H₂O"),
        ("co2", "CO₂"),
        ("13co", "13CO"),
        ("Other", "Other"),
        ("solar", "solar"),
        ("SOLAR", "SOLAR"),
    ],
)
def test_pretty_species_name(name, expected):
    assert pretty_species_name(name) == expected


@pytest.mark.parametrize("spectrum_path", SPECTRUM_FILES, ids=lambda path: path.name)
def test_read_spt_parses_bundled_spectrum(spectrum_path):
    data = read_spt(spectrum_path)

    assert data["header"]
    assert set(data["header"]) == set(data["columns"])
    assert data["columns"]["Freq"].size > 0

    n_points = data["columns"]["Freq"].size
    for column in data["columns"].values():
        assert column.ndim == 1
        assert column.size == n_points

    expected_residuals = 100.0 * (data["columns"]["Tm"] - data["columns"]["Tc"])
    np.testing.assert_allclose(data["resid"], expected_residuals)

    expected_rms = np.sqrt(np.mean(np.square(expected_residuals)))
    assert data["rms_resid"] == pytest.approx(expected_rms)


@pytest.mark.parametrize("spectrum_path", SPECTRUM_FILES, ids=lambda path: path.name)
def test_save_matplotlib_plot_creates_png(tmp_path, spectrum_path):
    data = read_spt(spectrum_path)

    colors_path = SPECTRA_DIR.parent / "data" / "colors.json"
    colors = json.loads(colors_path.read_text(encoding="utf-8"))

    html_path = tmp_path / f"{spectrum_path.stem}.html"

    save_matplotlib_plot(
        spectrum=spectrum_path.name,
        header=data["header"],
        columns=data["columns"],
        residuals=data["resid"],
        rms_resid=data["rms_resid"],
        sza=data["sza"],
        zobs=data["zobs"],
        colors=colors,
        html_path=str(html_path),
    )

    png_path = html_path.with_suffix(".png")
    assert png_path.is_file()
    assert png_path.stat().st_size > 0
    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_main_creates_html_and_png(tmp_path):
    spectrum_path = SPECTRUM_FILES[0]

    subprocess.run(
        [
            sys.executable,
            "-m",
            "ggg_spectra.main",
            "--indir",
            str(spectrum_path),
            "--save-path",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    html_path = tmp_path / f"{spectrum_path.name}.html"
    png_path = tmp_path / f"{spectrum_path.name}.png"

    assert html_path.is_file()
    assert png_path.is_file()
    assert html_path.stat().st_size > 0
    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
