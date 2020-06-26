# README #

This app plots the output spectrum files of GGG (typically saved in the GGGPATH/spt folder)

By default the app can see spectrum files in the spectra_app/spectra folder.

There is a textinput widget in which the full path to a different folder containing spectra can be given.

Run the app from a terminal, in the **parent** directory of ggg_spectra run:

>	**bokeh serve --show ggg_spectra**

A browser window will pop up with the app.

If you close the browser window, the server is still running and the app still available at http://localhost:5006/spectra_app

To shut the server down, use ctrl+C in the terminal

Each time a spectrum is loaded, a static .html file with the plot will be saved in **spectra_app/save/**

To use with GGG2014 spectra, revert to this commit: dfb16ed
