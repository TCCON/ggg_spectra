import os
import sys
import subprocess
import json
import argparse

import collections
from collections import OrderedDict

from tornado.ioloop import IOLoop
import bokeh
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.server.server import Server
from bokeh.io import curdoc
from bokeh.io.state import curstate
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    Button,
    Div,
    TextInput,
    Select,
    Legend,
    Range1d,
    CheckboxGroup,
    HoverTool,
    CrosshairTool,
)
from bokeh.layouts import gridplot, widgetbox, Column
from bokeh.resources import CDN
from bokeh.embed import file_html

import numpy as np


def read_spt(path):
    """
    spt files are the spectrum files output by GFIT/GFIT2
    """

    DATA = {}

    with open(path, "r") as infile:
        content = infile.readlines()

    head = content[2].split()

    DATA["header"] = head

    content_T = np.array(
        [[elem for elem in line.split()] for line in content[3:]], dtype=np.float
    ).T

    DATA["columns"] = {}
    for var in head:
        DATA["columns"][var] = content_T[head.index(var)]

    DATA["params"] = content[1].split()
    DATA["sza"] = float(DATA["params"][4])
    DATA["zobs"] = float(DATA["params"][5])
    DATA["xzo"] = float(DATA["params"][10])

    # the % residuals, tm and tc are transmittances so we just need to multiply by 100 to get %
    if "Cont" in DATA["columns"].keys():
        cont = DATA["columns"]["Cont"]
        xzo = DATA["xzo"]
        DATA["columns"]["Tm"] = (DATA["columns"]["Tm"] / cont - xzo) / (1 - xzo)
        DATA["columns"]["Tc"] = (DATA["columns"]["Tc"] / cont - xzo) / (1 - xzo)
    resid = 100.0 * (DATA["columns"]["Tm"] - DATA["columns"]["Tc"])
    rms_resid = np.sqrt(np.mean(np.square(resid)))  # rms of residuals

    DATA["resid"] = resid
    DATA["rms_resid"] = rms_resid

    return DATA


def save_x_bounds(attr, old, new):
    global spt_data
    if attr == "start":
        spt_data["fig_x"][0] = new
    else:
        spt_data["fig_x"][1] = new


def save_y_bounds(attr, old, new):
    global spt_data
    if attr == "start":
        spt_data["fig_y"][0] = new
    else:
        spt_data["fig_y"][1] = new


def save_y_resid_bounds(attr, old, new):
    global spt_data
    if attr == "start":
        spt_data["fig_resid_y"][0] = new
    else:
        spt_data["fig_resid_y"][1] = new


def update_bounds():
    """
    When loading a new spectrum, keep the same axis limits that were last used with the previous spectrum.
    """
    global spt_data

    if "prev_spec" not in spt_data.keys():
        return
    cur_spec = spt_data["cur_spec"]

    fig = curdoc().select_one({"name": "spec_fig"})
    fig_resid = curdoc().select_one({"name": "resid_fig"})

    cur_x = spt_data[cur_spec]["columns"]["Freq"]
    prev_x = spt_data["fig_x"]

    cur_xhw = (
        cur_x[-1] - cur_x[0]
    ) / 2.0  # window half-width, will allow to keep zooms that slightly exceed the window wavenumber range

    # only update horizontal bounds if they fit in the new spectrum data
    if cur_x[0] - cur_xhw < prev_x[0] and cur_x[-1] + cur_xhw > prev_x[1]:
        fig.x_range.start, fig.x_range.end = spt_data["fig_x"]

    # since it is all transmittance we can always update the vertical bounds
    fig.y_range.start, fig.y_range.end = spt_data["fig_y"]
    fig_resid.y_range.start, fig_resid.y_range.end = spt_data["fig_resid_y"]


def load_spectrum():
    """
    Callback for the load_spectrum button
    """

    global spt_data

    spectrum = curdoc().select_one({"name": "select_spectrum"}).value
    if spectrum == "":
        return

    cur_path = curdoc().select_one({"name": "path_input"}).value

    # read the spectrum file
    spt_data[spectrum] = read_spt(os.path.join(cur_path, spectrum))

    spt_data["cur_spec"] = spectrum

    doc_maker()

    update_bounds()

    spt_data["prev_spec"] = spectrum


def update_spec_path(attr, old, new):
    """
    Changes the path to the spectra
    """
    global custom_path

    custom_path = new

    select_spectrum = curdoc().select_one({"name": "select_spectrum"})

    if not os.path.isdir(custom_path):
        print("The given path is not an existing directory\nReverting to default spectrum folder")
        select_spectrum.options = [""] + sorted(os.listdir(spec_path))
    else:
        select_spectrum.options = [""] + sorted(os.listdir(custom_path))


def add_vlinked_crosshairs(fig1, fig2):
    """
    Make a crosshair to follow the mouse
    """
    js_move = """if(cb_obj.x >= fig.x_range.start && cb_obj.x <= fig.x_range.end && cb_obj.y >= fig.y_range.start && cb_obj.y <= fig.y_range.end)
                    { cross.spans.height.computed_location = cb_obj.sx }
                else 
                    { cross.spans.height.computed_location = null }"""
    js_leave = "cross.spans.height.computed_location = null"

    cross1 = CrosshairTool()
    cross2 = CrosshairTool()
    fig1.add_tools(cross1)
    fig2.add_tools(cross2)
    args = {"cross": cross2, "fig": fig1}
    fig1.js_on_event("mousemove", CustomJS(args=args, code=js_move))
    fig1.js_on_event("mouseleave", CustomJS(args=args, code=js_leave))
    args = {"cross": cross1, "fig": fig2}
    fig2.js_on_event("mousemove", CustomJS(args=args, code=js_move))
    fig2.js_on_event("mouseleave", CustomJS(args=args, code=js_leave))


def doc_maker():
    """
    Build the document layout
    """

    global spt_data, custom_path

    app_path = os.path.abspath(os.path.dirname(__file__))  # full path to ggg_spectra
    spec_path = os.path.join(app_path, "spectra")  # default fodler to look for spectra

    custom_path = ""  # optional user specified path to the spectra

    TOOLS = "box_zoom,wheel_zoom,pan,undo,redo,reset,crosshair,save"  # tools for bokeh figures

    # The color of each element is hardcoded in app_path/data/colors.json
    # this should include all the standard tccon species
    # it is ok for different species to have the same color if they are not retrieved in the same window
    with open(os.path.join(app_path, "data", "colors.json"), "rb") as infile:
        colors = json.load(infile)

    curdoc().clear()  # removes everything in the current document

    # dropdown to select a spectrum
    select_spectrum = Select(
        title="Select a spectrum:",
        value="",
        options=[""] + sorted(os.listdir(spec_path)),
        name="select_spectrum",
        width=200,
    )

    # textinput to give the full path to the location of spectra
    path_input = TextInput(title="Spectra folder", width=200, name="path_input")
    path_input.on_change("value", update_spec_path)

    # button to load the spectrum selected in the 'select_spectrum' dropdown
    load_button = Button(label="Load spectrum", width=200, css_classes=["custom_button"])
    load_button.on_click(load_spectrum)

    if spt_data == {}:
        curdoc().add_root(widgetbox(path_input, select_spectrum, load_button))
        if custom_path:
            path_input.value = custom_path
        else:
            path_input.value = spec_path
        return

    spectrum = spt_data["cur_spec"]

    header = spt_data[spectrum]["header"]

    species = np.array([spt_data[spectrum]["columns"][var] for var in header])
    SZA = str(spt_data[spectrum]["sza"])
    zobs = str(spt_data[spectrum]["zobs"])

    freq = spt_data[spectrum]["columns"]["Freq"]  # the frequency list
    tm = spt_data[spectrum]["columns"]["Tm"]  # measured transmittance list
    tc = spt_data[spectrum]["columns"]["Tc"]  # calculated transmittance list
    if "Cont" in header:
        not_gas = 4
    else:
        not_gas = 3  # number of column that are not retrieved species
    residuals = spt_data[spectrum]["resid"]  # 100*(calculated - measured)
    sigma_rms = spt_data[spectrum]["rms_resid"]  # sqrt(mean(residuals**2))

    # spectrum figure
    fig = figure(
        name="spec_fig",
        title=spectrum
        + "; SZA="
        + SZA
        + "; zobs="
        + zobs
        + "km; %resid=100*(Measured-Calculated); RMSresid="
        + ("%.4f" % sigma_rms)
        + "%",
        plot_width=1000,
        plot_height=400,
        tools=TOOLS,
        y_range=Range1d(-0.04, 1.04),
        outline_line_alpha=0,
        active_inspect="crosshair",
        active_drag="box_zoom",
    )
    # residual figure
    fig_resid = figure(
        name="resid_fig",
        plot_width=1000,
        plot_height=150,
        x_range=fig.x_range,
        tools=TOOLS,
        y_range=Range1d(-3, 3),
        outline_line_alpha=0,
        active_inspect="crosshair",
        active_drag="box_zoom",
    )

    # axes labels
    fig_resid.xaxis.axis_label = "Wavenumber (cm\u207B\u00B9)"
    fig_resid.yaxis.axis_label = "% Residuals"

    fig.yaxis.axis_label = "Transmittance"
    # fig.xaxis.axis_label = u'Wavenumber (cm\u207B\u00B9)'

    for elem in [fig, fig_resid]:
        elem.yaxis.axis_label_text_font_size = "14pt"
        elem.yaxis.major_label_text_font_size = "13pt"

        elem.xaxis.axis_label_text_font_size = "14pt"
        elem.xaxis.major_label_text_font_size = "13pt"

    N_plots = list(
        range(len(species) - not_gas + 2)
    )  # a range list from 0 to the number of plots, used by the checkbox group

    # group of checkboxes that will be used to toggle line and HoverTool visibility
    checkbox = CheckboxGroup(
        labels=header[not_gas:] + ["Measured", "Calculated"], active=N_plots, width=200
    )

    # plotting species lines
    plots = []
    for j in range(len(species) - not_gas):

        if header[j + not_gas] not in colors.keys():
            colo = "hotpink"
            print(
                '/!\\ header[j+not_gas] not in the "colors" dictionary, using hotpink by default; update the colors dictionary to use a specific color !'
            )
        else:
            colo = colors[header[j + not_gas]]
        plots.append(
            fig.line(
                x=freq, y=species[j + not_gas], color=colo, line_width=2, name=header[j + not_gas]
            )
        )
        # each line has a associated hovertool with a callback that looks at the checkboxes status for the tool visibility.
        fig.add_tools(
            HoverTool(
                mode="vline",
                line_policy="prev",
                renderers=[plots[j]],
                names=[header[j + not_gas]],
                tooltips=OrderedDict(
                    [
                        ("name", header[j + not_gas]),
                        ("index", "$index"),
                        ("(x;y)", "(@x{0.00} ; @y{0.000})"),
                    ]
                ),
            )
        )

    # adding the measured spectrum
    plots.append(fig.line(x=freq, y=tm, color="black", line_width=2, name="Tm"))
    fig.add_tools(
        HoverTool(
            mode="vline",
            line_policy="prev",
            renderers=[plots[j + 1]],
            names=["Tm"],
            tooltips=OrderedDict(
                [("name", "Measured"), ("index", "$index"), ("(x;y)", "(@x{0.00} ; @y{0.000})")]
            ),
        )
    )

    # adding the calculated spectrum
    plots.append(fig.line(x=freq, y=tc, color="chartreuse", line_width=2, name="Tc"))
    # fig.add_tools( HoverTool(mode='vline',line_policy='prev',renderers=[plots[j+2]],names=['Tc'],tooltips=OrderedDict( [('name','Calculated'),('index','$index'),('(x;y)','(@x{0.00} ; @y{0.000})')] )) )

    # legend outside of the figure
    fig_legend = Legend(
        items=[(header[j + not_gas], [plots[j]]) for j in range(len(species) - not_gas)]
        + [("Measured", [plots[-2]]), ("Calculated", [plots[-1]])],
        location=(0, 0),
        border_line_alpha=0,
    )
    fig.add_layout(fig_legend, "right")
    fig.legend.click_policy = "hide"
    fig.legend.inactive_fill_alpha = 0.6

    # now the residual figure
    fig_resid.line(x=freq, y=residuals, color="black", name="residuals")
    fig_resid.line(x=freq, y=np.zeros(len(freq)), color="red")
    fig_resid.add_tools(
        HoverTool(
            mode="vline",
            line_policy="prev",
            names=["residuals"],
            tooltips={"index": "$index", "(x;y)": "($x{0.00} ; $y{0.000})"},
        )
    )

    # set up a dummy legend for the residual figure so that it aligns with the spectrum figure
    dummy = fig_resid.line(
        x=freq, y=[0 for i in range(len(freq))], color="white", visible=False, alpha=0
    )
    fig_resid_legend = Legend(
        items=[("               ", [dummy])], location=(0, 0), border_line_alpha=0
    )
    fig_resid.add_layout(fig_resid_legend, "right")

    # checkbox group callback
    checkbox_iterable = [("p" + str(i), plots[i]) for i in N_plots] + [("checkbox", checkbox)]
    checkbox_code = "".join(
        ["p" + str(i) + ".visible = checkbox.active.includes(" + str(i) + ");" for i in N_plots]
    )
    checkbox.callback = CustomJS(
        args={key: value for key, value in checkbox_iterable}, code=checkbox_code
    )

    # button to uncheck all checkboxes
    clear_button = Button(label="Hide all lines", width=200)
    clear_button_code = """checkbox.active=[];""" + checkbox_code
    clear_button.callback = CustomJS(
        args={key: value for key, value in checkbox_iterable}, code=clear_button_code
    )

    # button to check all checkboxes
    check_button = Button(label="Show all lines", width=200)
    check_button_code = """checkbox.active=""" + str(N_plots) + """;""" + checkbox_code
    check_button.callback = CustomJS(
        args={key: value for key, value in checkbox_iterable}, code=check_button_code
    )

    # extension for the saved file name based on the path to spectra
    try:
        ext = os.path.basename(os.path.split(custom_path)[0])
    except:
        ext = ""

    if ext:
        save_file = os.path.join(save_path, "{}_{}.html".format(spectrum, ext))
    else:
        save_file = os.path.join(save_path, "{}.html".format(spectrum))

    # title div
    div = Div(
        text='<p align="center"><font size=4><b>{}</b></font></p>'.format(ext),
        width=fig.plot_width - 100,
    )

    add_vlinked_crosshairs(fig, fig_resid)

    sub_grid = gridplot([[fig], [fig_resid], [div]], toolbar_location="left")

    # button to activate/deactivate hover tools
    hover_button = Button(label="Enable hover tools", button_type="success", width=200)
    hover_list = [i for i in sub_grid.select({"type": HoverTool})]
    # in 'comp' mode, each plot has a different hover tool, I hide them and this button will click them all at once.
    hover_button_code = """
    if(cb_obj.button_type.includes("success")){
    cb_obj.button_type = 'warning';
    cb_obj.label = 'Disable hover tools'
    } else {
    cb_obj.button_type = 'success';
    cb_obj.label= 'Enable hover tools';
    }
    """ + "".join(
        ["hover{}.active = !hover{}.active;".format(i, i) for i in range(len(hover_list))]
    )
    hover_button.callback = CustomJS(
        args={"hover{}".format(i): elem for i, elem in enumerate(hover_list)},
        code=hover_button_code,
    )

    # put all the widgets in a box
    group = widgetbox(clear_button, check_button, hover_button, width=200, name="group")

    # the final grid for static plots
    grid = gridplot([[sub_grid, group]], toolbar_location=None)

    # save a standalone html document in ggg_spectra/save
    with open(save_file, "w") as outfile:
        outfile.write(file_html(grid, CDN, spectrum[:12] + spectrum[-3:]))
    print(f"Wrote {save_file}")

    group = widgetbox(
        clear_button,
        check_button,
        hover_button,
        path_input,
        select_spectrum,
        load_button,
        width=200,
    )

    app_grid = gridplot([[sub_grid, group]], toolbar_location=None)

    # Callbacks on axis ranges of figures, do this after the doc was saved as standalone html
    if "fig_x" not in spt_data.keys():
        spt_data.update(
            {
                "fig_x": [fig.x_range.start, fig.x_range.end],
                "fig_y": [fig.y_range.start, fig.y_range.end],
                "fig_resid_y": [fig_resid.y_range.start, fig_resid.y_range.end],
            }
        )
    fig.x_range.on_change("start", save_x_bounds)
    fig.x_range.on_change("end", save_x_bounds)
    fig.y_range.on_change("start", save_y_bounds)
    fig.y_range.on_change("end", save_y_bounds)
    fig_resid.y_range.on_change("start", save_y_resid_bounds)
    fig_resid.y_range.on_change("end", save_y_resid_bounds)

    # add that grid to the document
    curdoc().add_root(app_grid)

    if custom_path:
        path_input.value = custom_path
    else:
        path_input.value = spec_path


def modify_doc(doc):

    global spt_data

    spt_data = {}

    curstate().document = doc

    # this is displayed in the browser tab
    curdoc().title = "TCCON"

    # fill the document
    doc_maker()


def start_server():
    """
    Start the bokeh server and connect to it.
    """
    print("Preparing a bokeh application.")
    io_loop = IOLoop.current()
    bokeh_app = Application(FunctionHandler(modify_doc))

    server = Server({"/": bokeh_app}, io_loop=io_loop)
    server.start()
    print("Opening Bokeh application")

    io_loop.add_callback(server.show, "/")
    io_loop.start()


def main():

    global save_path

    parser = argparse.ArgumentParser(
        description="Plot the contents of spectrum files created by GGG using a bokeh server"
    )
    parser.add_argument(
        "-s",
        "--save-path",
        default=os.getcwd(),
        help="full path to the directory where the html plots will be saved, defaults to the current working directory",
    )
    args = parser.parse_args()

    save_path = args.save_path

    print(f"Each open spectrum will be saved as a standalone html file under {save_path}")

    start_server()


if __name__ == "__main__":
    main()
