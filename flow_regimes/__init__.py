import os
import numpy as np
import pandas as pd
import ipywidgets as widgets
import bqplot as bq


path_root = os.path.normpath(os.getcwd())
path_data_processed = os.path.join(path_root, 'data', 'processed')
history = pd.read_csv(os.path.join(path_data_processed, 'history.csv'),
                      index_col=['UNIQUE_ID', 'PROD_DATE'],
                      parse_dates=True)
# transform data for diagnostic
# required: unique_id, prod_date, days_on, mbt, rate, ratio
history = history[['CAL_DAYS_ON', 'OIL_MBT_CAL', 'CDOR', 'GOR']]
history.columns = ['DAYS_ON', 'MBT', 'RATE', 'RATIO']

well_list = history.index.get_level_values('UNIQUE_ID').unique()


def generate_well_data(data, well_id=well_list[0]):
    data_grouped = data.groupby('UNIQUE_ID')
    well_data = data_grouped.get_group(well_id)
    well_data = well_data.reset_index(drop=False)

    well_data = well_data.replace([np.inf, -np.inf], np.nan)
    well_data.dropna(inplace=True)

    return well_data

# Generate slopes


def generate_lf(data, index_selected=0, m=-0.5):
    """Point slope form equation of straight line in Log-Log scale.

    Args:
        data (df): index(int), MBT, RATE.
        index_selected (int): index of the selected point. Defaults to 0.
        m (float): slope. Defaults to -1/2.

    Returns:
        tuple of lists with x, y coordinates"""

    selected = data.iloc[index_selected]
    x1 = selected['MBT']
    y1 = selected['RATE']
    x = [data['MBT'].min(), data['MBT'].max()]
    y = [np.power(10, (m * (np.log10(i) - np.log10(x1)) + np.log10(y1))) for i in x]
    return x, y


def generate_bdf(data, index_selected=1, m=-1):
    """Point slope form equation of straight line in Log-Log scale.

    Args:
        data (df): index(int), MBT, RATE.
        index_selected (int): index of the selected point. Defaults to 1.
        m (float): slope. Defaults to -1.

    Returns:
        tuple of lists with x, y coordinates"""

    selected = data.iloc[index_selected]
    x1 = selected['MBT']
    y1 = selected['RATE']
    x = [data['MBT'].min(), data['MBT'].max() + 1000]
    y = [np.power(10, (m * (np.log10(i) - np.log10(x1)) + np.log10(y1))) for i in x]
    return x, y


# Defaults
well_data = generate_well_data(history)
x_lf, y_lf = generate_lf(well_data)
x_bdf, y_bdf = generate_bdf(well_data)

# select list widget to select a well
well_select_w = widgets.Select(options=well_list,
                               rows=47,
                               description='',
                               disabled=False,
                               layout=widgets.Layout(width='10%'))
# slider widget to move LF
slider_lf_w = widgets.SelectionSlider(options=well_data.index,
                                      value=0,
                                      description='Linear Flow: ',
                                      disabled=False,
                                      continuous_update=True,
                                      orientation='horizontal',
                                      readout=True)
# slider widget to move LF
slider_bdf_w = widgets.SelectionSlider(options=well_data.index,
                                       value=1,
                                       description='BDF: ',
                                       disabled=False,
                                       continuous_update=True,
                                       orientation='horizontal',
                                       readout=True)
# Label widget to display results
results_widget = widgets.Label(value='Results go here...')

# match lf line with slider for the first well
# need it here to draw slopes for the first well, before 'change' of well


def draw_lf(change):
    x_lf, y_lf = generate_lf(well_data, change['new'], -0.5)
    mbt_lf.x = x_lf
    mbt_lf.y = y_lf


slider_lf_w.observe(draw_lf, names='value')


def draw_bdf(change):
    x_bdf, y_bdf = generate_bdf(well_data, change['new'], -1)
    mbt_bdf.x = x_bdf
    mbt_bdf.y = y_bdf


slider_bdf_w.observe(draw_bdf, names='value')

# MBT Plot
sc_x = bq.LogScale()
sc_y = bq.LogScale()

mbt_scatter = bq.Scatter(x=well_data['MBT'],
                         y=well_data['RATE'],
                         scales={'x': sc_x, 'y': sc_y},
                         marker='circle',
                         colors=['#4CAF50'],
                         default_size=25,
                         interactions={'click': 'select'},
                         selected_style={'fill': '#f44336', 'stroke': '#f44336'},
                         unselected_style={'opacity': 0.7})

mbt_lf = bq.Lines(x=x_lf, y=y_lf,
                  scales={'x': sc_x, 'y': sc_y},
                  line_style='dashed',
                  stroke_width=1,
                  colors=['#795548'],
                  opacities=[0.9])

mbt_bdf = bq.Lines(x=x_bdf, y=y_bdf,
                   scales={'x': sc_x, 'y': sc_y},
                   line_style='solid',
                   stroke_width=1,
                   colors=['#795548'],
                   opacities=[0.9])

mbt_ax_x = bq.Axis(label='Material Balance Time',
                   label_color='#616161',
                   label_offset='3em',
                   scale=sc_x,
                   grid_lines='solid',
                   grid_color='#F5F5F5',
                   tick_values=[30, 60, 90, 180, 360, 1000, 5000, 10000, 100000, 1000000],
                   tick_format='f',
                   tick_style={'font-size': '0.95em', 'fill': '#757575'})

mbt_ax_y = bq.Axis(label='Oil Rate',
                   label_color='#616161',
                   label_offset='3em',
                   orientation='vertical',
                   scale=sc_y,
                   grid_lines='solid',
                   grid_color='#F5F5F5',
                   tick_format='f',
                   tick_style={'font-size': '0.95em', 'fill': '#757575'})

mbt_fig = bq.Figure(title='Log-Log Rate-MBT',
                    title_style={'font-size': '1.4em', 'fill': '#212121'},
                    axes=[mbt_ax_x, mbt_ax_y],
                    marks=[mbt_scatter, mbt_lf, mbt_bdf],
                    padding_x=0.01,
                    padding_y=0.01,
                    background_style={'fill': '#ffffff'})
# Rate Time Plot
rt_sc_x = bq.LinearScale()
rt_sc_y = bq.LogScale()

rt_scatter = bq.Scatter(x=well_data['DAYS_ON'],
                        y=well_data['RATE'],
                        scales={'x': rt_sc_x, 'y': rt_sc_y},
                        marker='circle',
                        colors=['#4CAF50'],
                        default_size=25,
                        interactions={'click': 'select'},
                        selected_style={'fill': '#f44336', 'stroke': '#f44336'},
                        unselected_style={'opacity': 0})

rt_line = bq.Lines(x=well_data['DAYS_ON'],
                   y=well_data['RATE'],
                   scales={'x': rt_sc_x, 'y': rt_sc_y},
                   line_style='solid',
                   colors=['#4CAF50'],
                   stroke_width=1.5,
                   opacities=[0.8])

rt_ax_x = bq.Axis(label='Days',
                  label_color='#616161',
                  label_offset='3em',
                  scale=rt_sc_x,
                  grid_lines='solid',
                  grid_color='#F5F5F5',
                  tick_format='d',
                  tick_style={'font-size': '0.9em', 'fill': '#757575'})

rt_ax_y = bq.Axis(label='Oil Rate',
                  label_color='#616161',
                  label_offset='3em',
                  orientation='vertical',
                  scale=rt_sc_y,
                  grid_lines='solid',
                  grid_color='#F5F5F5',
                  tick_format='f',
                  tick_style={'font-size': '0.9em', 'fill': '#757575'})

rt_fig = bq.Figure(title='Semi-Log Rate-Time',
                   title_style={'font-size': '1.4em', 'fill': '#212121'},
                   axes=[rt_ax_x, rt_ax_y],
                   marks=[rt_scatter, rt_line],
                   padding_x=0.01,
                   padding_y=0.01,
                   background_style={'fill': '#ffffff'})

# GOR Plot
gor_sc_x = bq.LinearScale()
gor_sc_y = bq.LinearScale()

gor_scatter = bq.Scatter(x=well_data['DAYS_ON'],
                         y=well_data['RATIO'],
                         scales={'x': gor_sc_x, 'y': gor_sc_y},
                         marker='circle',
                         colors=['#AFB42B'],
                         default_size=25,
                         interactions={'click': 'select'},
                         selected_style={'fill': '#f44336', 'stroke': '#f44336'},
                         unselected_style={'opacity': 0})

gor_line = bq.Lines(x=well_data['DAYS_ON'],
                    y=well_data['RATIO'],
                    scales={'x': gor_sc_x, 'y': gor_sc_y},
                    line_style='solid',
                    colors=['#AFB42B'],
                    stroke_width=1.5,
                    opacities=[0.8])

gor_ax_x = bq.Axis(label='Days',
                   label_color='#616161',
                   label_offset='3em',
                   scale=gor_sc_x,
                   grid_lines='solid',
                   grid_color='#F5F5F5',
                   tick_format='d',
                   tick_style={'font-size': '0.9em', 'fill': '#757575'})

gor_ax_y = bq.Axis(label='Gas Oil Ratio',
                   label_color='#616161',
                   label_offset='3em',
                   orientation='vertical',
                   scale=gor_sc_y,
                   grid_lines='solid',
                   grid_color='#F5F5F5',
                   tick_format='f',
                   tick_style={'font-size': '0.9em', 'fill': '#757575'})

gor_fig = bq.Figure(title='Cartesian Gas Oil Ratio',
                    title_style={'font-size': '1.4em', 'fill': '#212121'},
                    axes=[gor_ax_x, gor_ax_y],
                    marks=[gor_scatter, gor_line],
                    padding_x=0.01,
                    padding_y=0.01,
                    background_style={'fill': '#ffffff'})
# Time MBT Plot
time_mbt_sc_x = bq.LogScale()
time_mbt_sc_y = bq.LogScale()

time_mbt_scatter = bq.Scatter(x=well_data['DAYS_ON'],
                              y=well_data['MBT'],
                              scales={'x': time_mbt_sc_x, 'y': time_mbt_sc_y},
                              marker='circle',
                              colors=['#616161'],
                              default_size=25,
                              interactions={'click': 'select'},
                              selected_style={'fill': '#f44336', 'stroke': '#f44336'},
                              unselected_style={'opacity': 0.7})

time_mbt_ax_x = bq.Axis(label='Days',
                        label_color='#616161',
                        label_offset='3em',
                        scale=time_mbt_sc_x,
                        grid_lines='solid',
                        grid_color='#F5F5F5',
                        tick_format='f',
                        tick_style={'font-size': '0.9em', 'fill': '#757575'})

time_mbt_ax_y = bq.Axis(label='Material Balance Time',
                        label_color='#616161',
                        label_offset='3em',
                        orientation='vertical',
                        scale=time_mbt_sc_y,
                        grid_lines='solid',
                        grid_color='#F5F5F5',
                        tick_values=[30, 60, 90, 180, 360, 1000, 5000, 10000, 100000, 1000000],
                        tick_format='f',
                        tick_style={'font-size': '0.95em', 'fill': '#757575'})

time_mbt_fig = bq.Figure(title='Log-Log Time-MBT',
                         title_style={'font-size': '1.4em', 'fill': '#212121'},
                         axes=[time_mbt_ax_x, time_mbt_ax_y],
                         marks=[time_mbt_scatter],
                         padding_x=0.01,
                         padding_y=0.01,
                         background_style={'fill': '#ffffff'})
# controller


def on_well_select(change):
    global well_data
    well_data = generate_well_data(history, change['new'])

    # update MBT plot
    mbt_scatter.x = well_data['MBT']
    mbt_scatter.y = well_data['RATE']

    # update RT plot
    rt_scatter.x = well_data['DAYS_ON']
    rt_scatter.y = well_data['RATE']
    rt_line.x = well_data['DAYS_ON']
    rt_line.y = well_data['RATE']

    # update GOR plot
    gor_scatter.x = well_data['DAYS_ON']
    gor_scatter.y = well_data['RATIO']
    gor_line.x = well_data['DAYS_ON']
    gor_line.y = well_data['RATIO']

    # update Time MBT plot
    time_mbt_scatter.x = well_data['DAYS_ON']
    time_mbt_scatter.y = well_data['MBT']

    # update LF line on MBT plot
    x_lf, y_lf = generate_lf(well_data)
    mbt_lf.x = x_lf
    mbt_lf.y = y_lf

    # update BDF line on MBT plot
    x_bdf, y_bdf = generate_bdf(well_data)
    mbt_bdf.x = x_bdf
    mbt_bdf.y = y_bdf

    # reset slider options
    slider_bdf_w.options = well_data.index
    slider_bdf_w.value = 1
    slider_lf_w.options = well_data.index
    slider_lf_w.value = 0

    # match lf line with slider
    def draw_lf(change):
        x_lf, y_lf = generate_lf(well_data, change['new'], -0.5)
        mbt_lf.x = x_lf
        mbt_lf.y = y_lf

    slider_lf_w.observe(draw_lf, names='value')

    # match bdf with slider
    def draw_bdf(change):
        x_bdf, y_bdf = generate_bdf(well_data, change['new'], -1)
        mbt_bdf.x = x_bdf
        mbt_bdf.y = y_bdf

    slider_bdf_w.observe(draw_bdf, names='value')


well_select_w.observe(on_well_select, names='value')

widgets.jslink((mbt_scatter, 'selected'), (rt_scatter, 'selected'))
widgets.jslink((mbt_scatter, 'selected'), (gor_scatter, 'selected'))
widgets.jslink((mbt_scatter, 'selected'), (time_mbt_scatter, 'selected'))

# refactor into layout for the whole app
mbt_fig.layout.height = '60%'
gor_fig.layout.height = '40%'
rt_fig.layout.height = '60%'
time_mbt_fig.layout.height = '40%'

sliders = widgets.VBox([widgets.HBox([slider_lf_w, slider_bdf_w])])
results = widgets.VBox([results_widget])
sliders_mbt_gor = widgets.VBox([sliders, mbt_fig, gor_fig])
results_rt_timembt = widgets.VBox([results, rt_fig, time_mbt_fig])
flow_regimes = widgets.HBox([well_select_w, sliders_mbt_gor, results_rt_timembt])
