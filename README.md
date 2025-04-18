# README #

This app plots the output spectrum files of GGG (typically saved in the GGGPATH/spt folder).

The plotting is done with [bokeh](https://bokeh.org/) in the browser using a local server where spectra can be loaded, standalone plots are saved as html pages. 

### Installation ###

I suggest creating a new python environment with anaconda:

	conda create -n gggspec python=3.6

Activate the environmentL:

	conda activate gggspec

Install the package with:

	python -m pip install git+https://github.com/TCCON/ggg_spectra

### Running ###

After the installation a console entry point is made available and the bokeh server can be started from anywhere with the command:

	ggg_spectra

### Info ###

A browser window will pop up with the app.

There is a textinput widget in which the full path to a different folder containing spectra can be given.

The initial directory of input spectra can be specified with a **-i/--indir** argument. By default the app can see spectrum files in the **ggg_spectra/spectra** folder.

A full spectrum file path can be given to **--indir**, in that case the static html plot will be saved without starting the browser app. 

If you close the browser window, the server is still running and the app still available where indicated in the terminal.

To shut the server down, use ctrl+C in the terminal.

Each time a spectrum is loaded, a static .html file with the plot will be saved by default under the current working directory.

There is a second textinput widget to specify an extension for the name of the saved file, following **spectrum_extension.html** with **spectrum** the chosen spectrum file name and **extension** the content of the textinput. This is there to avoid overwriting a saved file when looking at spectra with the same file names in different folders. 

The output directory can be specified with a **-s/--save-path** argument.

	ggg_spectra -s /path/to/output_dir

The colors of the lines are harcoded for each element in **ggg_spectra/data/colors.json**, you can update that dictionary to add new elements or change colors.

For this it would be best to clone the repo and install it in edit mode:

	git clone https://github.com/TCCON/ggg_spectra

	python -m pip install -e ggg_spectra

To run the code directly just call the main.py program:

	python /path/to/main.py

#### Contact ####

sebastien.roche@alumni.utoronto.ca
