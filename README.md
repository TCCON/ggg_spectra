# README #

This app plots the output spectrum files of GGG (typically saved in the GGGPATH/spt folder)

### Installation ###

I suggest creating a new python environment with anaconda:

	conda create -n gggspec python=3.6

Activate the environmentL:

	conda activate gggspec

Install the package with:

	python -m pip install /path/to/ggg_spectra

### Running ###

After the installation a console entry point is made available and the bokeh server can be started from anywhere with the command:

	ggg_spectra

### Info ###

A browser window will pop up with the app.

There is a textinput widget in which the full path to a different folder containing spectra can be given.

By default the app can see spectrum files in the ggg_spectra/spectra folder.

If you close the browser window, the server is still running and the app still available where indicated in the terminal.

To shut the server down, use ctrl+C in the terminal

Each time a spectrum is loaded, a static .html file with the plot will be saved in **ggg_spectra/save/**

To use with GGG2014 spectra, revert to this commit: dfb16ed

#### Contact ####

sebastien.roche@mail.utoronto.ca
