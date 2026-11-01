# ggg_spectra

`ggg_spectra` plots spectrum files produced by GGG. It runs in a local webserver. It provides an interactive, browser-based interface for browsing spectra and saves a standalone HTML plot each time you load one. You can also create a static HTML plot directly from a spectrum file without starting the interactive app.

## Requirements

- Python>=3.10

## Installation

If you do not already have a Python environment, [install Mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html), then create and activate an environment for `ggg_spectra`:

```bash
mamba create -n gggspec python=3.15 pip
mamba activate gggspec
```

Install the package from GitHub:

```bash
python -m pip install git+https://github.com/TCCON/ggg_spectra
```

To install an editable copy, for example if you plan to change the code or line colors:

```bash
python -m pip install -e .
```

After installation, the `ggg_spectra` command is available.

## Run the interactive app

Start the app from anywhere with:

```bash
ggg_spectra
```

By default, the app looks for spectra in the package's `spectra` directory. A browser window opens with a spectrum-selection menu and a field where you can enter a different source folder for spectra.

When you load a spectrum, the app also saves a standalone HTML plot in the current working directory. To stop the server, press `Ctrl+C` in the terminal where you started it.

## Command-line options

```text
ggg_spectra [-h] [-i INDIR] [-s SAVE_PATH] [--sizing-mode MODE]
```

| Option | Description |
| --- | --- |
| `-i`, `--indir` | Input spectra directory. You can also give the path to a single spectrum file to create a static plot. Defaults to the package's `spectra` directory. |
| `-s`, `--save-path` | Directory for saved HTML plots. Defaults to the current working directory. The directory must already exist. |
| `--sizing-mode` | Bokeh layout sizing mode. Defaults to `scale_both`. See `ggg_spectra --help` for the available choices. |
| `-h`, `--help` | Show command-line help. |

For example, to use another spectra folder and save plots to an existing output folder:

```bash
ggg_spectra --indir /path/to/spectra --save-path /path/to/output
```

You can also change the spectra folder from the app after it starts.

## Create a static plot

Pass a spectrum file to `--indir`. This creates an HTML plot and exits without starting the browser app:

```bash
ggg_spectra --indir /path/to/spectrum-file --save-path /path/to/output
```

The output filename is based on the spectrum filename. In the interactive app, you can enter a save extension to distinguish plots with the same spectrum filename; the extension is added after the spectrum name.

## Run directly

From the repository root, you can run the app without using the installed console command:

```bash
python -m ggg_spectra.main
```

To make a static plot this way:

```bash
python -m ggg_spectra.main --indir /path/to/spectrum-file --save-path /path/to/output
```

## Customize line colors

Species colors are defined in `ggg_spectra/data/colors.json`. Edit this file to change existing colors or add species. Species not found in the color file are plotted in hot pink.

## Contact

For questions or issues, contact sebastien.roche@alumni.utoronto.ca.