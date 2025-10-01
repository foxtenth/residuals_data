"""
Created on Tue Mar  5 13:35:03 2024
@author: CHCUK-02-Finn
"""

import os
# import ctypes
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as plotly_output
from plotly import graph_objs as go
from plotly.subplots import make_subplots
from configparser import ConfigParser
plotly_output.renderers.default='browser' #or svg

class csv_loader:
   def __init__(self, csv_to_load):
         self.loaded_file_id = csv_to_load[0]
         self.loaded_csv = pd.read_csv(csv_to_load[0])
         self.loaded_csv.columns = self.loaded_csv.columns.str.lower()
         self.loaded_csv.columns = self.loaded_csv.columns.str.replace(' ','')
         self.data_cols = self.loaded_csv.columns.tolist()
         self.data_identifier = False
         
         self.residual_blocks = []
         if 'column' in self.data_cols:
            self.number_blocks = len(list(self.loaded_csv.groupby('column').groups.keys()))
            self.loaded_csv = self.loaded_csv.rename(columns = {'num': 'prn'})
            self.located_residuals = list(self.loaded_csv.groupby('column').groups.keys())
            for frame_obj in self.located_residuals:
               self.residual_blocks.append([frame_obj, self.loaded_csv[self.loaded_csv['column'] == frame_obj]])
            
            # selected_block = 0
            # self.loaded_csv = self.residual_blocks[selected_block][1] #[0][X] -> residual data blocks
            # self.data_identifier = self.residual_blocks[selected_block][0] #[X][0] -> residual names/types
         
         self.stations = list(self.loaded_csv.groupby('station').groups.keys()) 
         self.satellites = list(self.loaded_csv.groupby('sys').groups.keys()) 
         self.output_path = csv_to_load[1]
         self.bar_colors = [
                              [[0, 'rgb(255, 185, 0)' ], [1, 'rgb(78, 70, 57)']],   #gold
                              [[0, 'rgb(43, 176, 238)'], [1, 'rgb(11, 44, 59)']],   #blue
                              [[0, 'rgb(76, 238, 94)'], [1, 'rgb(28, 90, 34)']],    #green
                              [[0, 'rgb(204, 153, 255)'], [1, 'rgb(77, 38, 107)']], #purple
                              [[0, 'rgb(255, 58, 58)'], [1, 'rgb(140, 0, 0)']],    #redorange
                              [[0, 'rgb(238, 76, 216)'], [1, 'rgb(100, 33, 91)']]   #magenta
                           ]
         self.colors_to_buttons = [
                                    '#ffe100',
                                    '#ff3bb0',
                                    '#ff892e',
                                    '#00ffc8',
                                    'rgb(191, 255, 0)',
                                    '#ff3bb0',
                                    '#3bff68',
                                    '#ff893b',
                                    '#3badff',
                                    '#ffe563',
                                  ]
         
class csv_processor(csv_loader): 
   def __init__(self, csv_to_load, plot_range):
         super().__init__(csv_to_load)
         self.data_grouped_by_intervals = []
         self.data_intervals = []
         self.plot_range = plot_range
         
         self.stations_by_mean   = None
         self.stations_by_median = None
         self.stations_by_2sigma = None
         self.stations_by_3sigma = None
         self.station_collections = []
         
         self.sat_blocks_by_mean   = []
         self.sat_blocks_by_median = []
         self.sat_blocks_by_2sigma = []
         self.sat_blocks_by_3sigma = []
         self.sat_collections = []
         
         self.combined_collections = []
        
   def sort_stations_by_col(self, column):
      station_blocks_mean = []
      station_blocks_median = []
      station_blocks_2sigma  = []
      station_blocks_3sigma = []
      
      for station in range(0, len(self.stations)):
         selected_data_by_col = self.loaded_csv.groupby('station').get_group(self.stations[station])[column]
         
         #getting mean, mean for each station
         station_mean_value = selected_data_by_col.mean()
         station_median_value = selected_data_by_col.median()
         #2sigma/3sigma for each station
         station_2sigma_value = sorted(selected_data_by_col.tolist())[round(len(selected_data_by_col)*0.95)]
         station_3sigma_value = sorted(selected_data_by_col.tolist())[-1]
         
         #single station block -> station_name + quality_value
         station_blocks_mean.append([self.stations[station], station_mean_value]) 
         station_blocks_median.append([self.stations[station], station_median_value]) 
         station_blocks_2sigma.append([self.stations[station], station_2sigma_value]) 
         station_blocks_3sigma.append([self.stations[station], station_3sigma_value]) 
      
      #sorting
      self.stations_by_mean   = sorted(station_blocks_mean, key=lambda x: x[1])
      self.stations_by_median = sorted(station_blocks_median, key=lambda x: x[1])
      self.stations_by_2sigma = sorted(station_blocks_2sigma, key=lambda x: x[1])
      self.stations_by_3sigma = sorted(station_blocks_3sigma, key=lambda x: x[1])
      
      self.station_collections = [self.stations_by_mean, self.stations_by_median, self.stations_by_2sigma, self.stations_by_3sigma]
      
   def sort_sats_by_col(self, column):
      selected_sat_data = self.loaded_csv.groupby('sys')      
      sat_blocks_mean = []
      sat_blocks_median = []
      sat_blocks_2sigma  = []
      sat_blocks_3sigma = []
      selected_sys_groups = [
                              ['G', selected_sat_data.get_group(1)],
                              ['C', selected_sat_data.get_group(3)],
                              ['E', selected_sat_data.get_group(4)]
                            ]
      for sys in selected_sys_groups:
         #get satellites
         available_sats = sorted(sys[1]['prn'].unique())
         for sat in available_sats:
            selected_sat_by_col = sys[1][sys[1]['prn'] == sat][column]
            
            #getting mean, mean for each station
            sat_mean_value = selected_sat_by_col.mean()
            sat_median_value = selected_sat_by_col.median()
            
            #2sigma/3sigma for each station
            sat_2sigma_value = sorted(selected_sat_by_col.tolist())[round(len(selected_sat_data)*0.95)]
            sat_3sigma_value = sorted(selected_sat_by_col.tolist())[-1]
            
            #single satellite block -> sat_sys + sat + quality_value
            sat_blocks_mean.append([sys[0], sat, sat_mean_value])
            sat_blocks_median.append([sys[0], sat, sat_median_value])
            sat_blocks_2sigma.append([sys[0], sat, sat_2sigma_value])
            sat_blocks_3sigma.append([sys[0], sat, sat_3sigma_value])
      
      #sorting GPS satellites [0]
      self.sat_blocks_by_mean.append(sorted([sat_list for sat_list in sat_blocks_mean if sat_list[0] == 'G'], key=lambda x: x[2]))
      self.sat_blocks_by_median.append(sorted([sat_list for sat_list in sat_blocks_median if sat_list[0] == 'G'], key=lambda x: x[2]))
      self.sat_blocks_by_2sigma.append(sorted([sat_list for sat_list in sat_blocks_2sigma if sat_list[0] == 'G'], key=lambda x: x[2]))
      self.sat_blocks_by_3sigma.append(sorted([sat_list for sat_list in sat_blocks_3sigma if sat_list[0] == 'G'], key=lambda x: x[2]))
      
      #sorting BDS satellites [1]
      self.sat_blocks_by_mean.append(sorted([sat_list for sat_list in sat_blocks_mean if sat_list[0] == 'C'], key=lambda x: x[2]))
      self.sat_blocks_by_median.append(sorted([sat_list for sat_list in sat_blocks_median if sat_list[0] == 'C'], key=lambda x: x[2]))
      self.sat_blocks_by_2sigma.append(sorted([sat_list for sat_list in sat_blocks_2sigma if sat_list[0] == 'C'], key=lambda x: x[2]))
      self.sat_blocks_by_3sigma.append(sorted([sat_list for sat_list in sat_blocks_3sigma if sat_list[0] == 'C'], key=lambda x: x[2]))
      
      #sorting GAL satellites [2]
      self.sat_blocks_by_mean.append(sorted([sat_list for sat_list in sat_blocks_mean if sat_list[0] == 'E'], key=lambda x: x[2]))
      self.sat_blocks_by_median.append(sorted([sat_list for sat_list in sat_blocks_median if sat_list[0] == 'E'], key=lambda x: x[2]))
      self.sat_blocks_by_2sigma.append(sorted([sat_list for sat_list in sat_blocks_2sigma if sat_list[0] == 'E'], key=lambda x: x[2]))
      self.sat_blocks_by_3sigma.append(sorted([sat_list for sat_list in sat_blocks_3sigma if sat_list[0] == 'E'], key=lambda x: x[2]))
      
      #grouped by order -> mean, median, 2sigma, 3sigma
      self.sat_collections = [self.sat_blocks_by_mean, self.sat_blocks_by_median, self.sat_blocks_by_2sigma, self.sat_blocks_by_3sigma]
         
   def create_intervals(self):
       #finding the min/max values in the whole set
       segments = (np.arange(self.plot_range[0], self.plot_range[1] + self.plot_range[-1], self.plot_range[-1])).tolist()
       segments.insert(0, float('-inf'))
       segments.append(float('inf')) 
       self.data_intervals = segments
       
   def fill_interval_sets(self, column):
      selected_data = self.loaded_csv[['station', column]]
      #create a set to contain all intervals and assign data to them
      for index, data_interval in enumerate(self.data_intervals):
           segmented_data = None
           
           #extract values sectioned to intervals
           if index + 1 != len(self.data_intervals):
                 segmented_data = selected_data[(selected_data[column] >= data_interval) 
                                               & (selected_data[column] < self.data_intervals[index + 1])]
           else:
                 segmented_data = selected_data[(selected_data[column] >= data_interval)] 
           
           #sorting values by column and offloading to a list
           sorted_interval_values = segmented_data.sort_values(by=column, ascending = True).values.tolist()
           
           # fill each interval with data
           if index + 1 != len(self.data_intervals):
               #start value of interval to the next interval value
               data_interval = '[' + str(self.data_intervals[index])[:6] + '_' +  str(self.data_intervals[index + 1])[:6]
               self.data_grouped_by_intervals.append([data_interval, len(sorted_interval_values), sorted_interval_values])   
               
   def export_intervals_to_html(self, column, bar_color):
      #plots all intervals from self.data_grouped_by_intervals
      labels = []
      values = []
      for dataset in self.data_grouped_by_intervals:
          if dataset[1] == 0:
            labels.append(dataset[0])
            values.append(0)
          else:
            labels.append(dataset[0])
            values.append(dataset[1])
      
      fig = px.bar(x = labels, y = values, color = values, color_continuous_scale = bar_color, text_auto = True,
          title = 'source_' + self.loaded_file_id + '<br>' + column.upper(), labels={'x': '<b>Segment</b>', 'y': '<b>Frequency</b>'} )   
      fig.update_xaxes(tickangle = -90)  
      fig.update_traces(width = 0.9, marker_line_width=0)
      fig.update_layout(coloraxis_colorbar = dict(title = ''), barmode = 'relative', bargap = 0.0)
      fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0] + '_' + column + '.html', 
                     auto_open=True)   
      
   def plot_column_by_intervals(self, column, bar_color):
         self.create_intervals()  #initialize/create intervals for data
         self.fill_interval_sets(column)  #load data into intervals / sorted data to be loaded into intervals
         self.export_intervals_to_html(column, bar_color)  #create .html plots for every data column/residual selected
         
         #unload lists
         self.data_intervals = []
         self.data_grouped_by_intervals = []
   def run_all_columns_by_intervals(self, columns): 
         iter_colorlist = iter(self.bar_colors)
         for col in columns:
            bar_color = next(iter_colorlist)
            self.plot_column_by_intervals(col, bar_color)   
         
   def export_stations_singleplots(self, column):   
      self.sort_stations_by_col(column)
      
      for index, station_collection in enumerate(self.station_collections):
         if index == 0:  
            sorting_type = 'Mean'
         elif index == 1: 
            sorting_type = 'Median' 
         elif index == 2: 
            sorting_type = '2Sigma'
            continue
         elif index == 3:
            sorting_type = '3Sigma'
            break
         
         stations, values = [], []
         for station_register in station_collection:
            stations.append(station_register[0])
            values.append(station_register[1])
            
         fig = go.Figure()
         fig.add_trace(go.Bar(
               x = stations,
               y = values,
               text = [str(value)[:5] for value in values],
               marker = dict(
                  color = values,  # Use the 'values' list for coloring the bars
                  colorscale = [
                                 [0, 'rgb(255, 153, 36)'], 
                                 # [0.25, 'rgb(255, 50, 36)'],
                                 [1, 'rgb(255, 0, 15)']
                                 
                                # [0, 'rgb(43, 176, 238)'], 
                                # [0.25, 'rgb(0, 102, 204)'],
                                # [1, 'rgb(11, 44, 59)']
                               ],
                  colorbar = dict(
                     title = '',
                     outlinecolor = 'rgba(0,0,0,0)',
                     ),
                  ),
               insidetextfont = dict(color = 'white')
               ))
         fig.update_yaxes(title = '<b>in metres</b>', range = [0, values[-1]*2])
         fig.update_xaxes(
             title = dict(text = '<b>Station identifier</b>'),
             tickvals = stations,
             tickangle = 0,                  # Rotate tick labels by 45 degrees
             tickfont = dict(size = 12)        # Customize the font size of tick labels
         )
         fig.update_layout(
             title = go.layout.Title(text = "Station performance by: " + sorting_type 
                                     + ' | column seed: ' + column
                                     + '<br>sourced from: ' + self.loaded_file_id),
             title_font = dict(size = 20),  # Customize the title font size
         )
         # fig.show()
         fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0] + '_' + column + '_' 
                        + sorting_type + '_stations.html', 
                        auto_open=False)      
         
   def export_sats_singleplots (self, column):
       self.sort_sats_by_col(column)
       
       for index, sat_collection in enumerate(self.sat_collections):
          if index == 0:  
             sorting_type = 'Mean'
          elif index == 1: 
             sorting_type = 'Median' 
          elif index == 2: 
             sorting_type = '2Sigma'
             continue
          elif index == 3:
             sorting_type = '3Sigma'
             break
             
          for index_sys, nav_sys in enumerate(sat_collection): 
                if index_sys == 0:   #subset 0 -> GPS
                   sys = 'G'
                elif index_sys == 1: #subset 1 -> BDS
                   sys = 'C'
                elif index_sys == 2: #subset 2 -> GAL
                   sys = 'E'
                sats, values = [], []
                
                for sat_data in nav_sys:
                      sats.append(sat_data[1])
                      values.append(sat_data[2])
                      
                fig = go.Figure()
                fig.add_trace(go.Bar(
                      x = sats,
                      y = values,
                      text = [str(value)[:5] for value in values],
                      marker = dict(
                        color = values,  # Use the 'values' list for coloring the bars
                        colorscale = [
                                      # [0, 'rgb(255, 153, 36)'], 
                                      # [0.25, 'rgb(255, 50, 36)'],
                                      # [1, 'rgb(255, 0, 15)']
                                      [0, 'rgb(43, 176, 238)'], 
                                      [0.25, 'rgb(0, 102, 204)'],
                                      [1, 'rgb(11, 44, 59)']
                                      ],
                        colorbar = dict(
                            title = '',
                            outlinecolor = 'rgba(0,0,0,0)',
                            ),
                        ),
                      insidetextfont = dict(color = 'white')
                      ))
                fig.update_yaxes(title = '<b>in metres</b>', range = [0, values[-1]*2])
                fig.update_xaxes(
                    title = dict(text = '<b>PRN identifier</b>'),
                    tickvals = sats,
                    ticktext = [(sys + '0'  + str(sat_id)) if len(str(sat_id)) < 2 else (sys + str(sat_id)) for sat_id in sats],
                    tickangle = 0,                  # Rotate tick labels by 45 degrees
                    tickfont = dict(size = 12)        # Customize the font size of tick labels
                )
                fig.update_layout(
                    title = go.layout.Title(text = "Satellite performance by type: " 
                                            + sorting_type + ' | column seed: ' + column
                                            + '<br>sourced from: ' + self.loaded_file_id),
                    title_font = dict(size = 20),  # Customize the title font size
                )
                # fig.show()
                fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0] + '_' + column + '_' 
                               + sorting_type + '_' + sys + '_sat.html', 
                               auto_open=False) 
                
   def export_all_singleplots(self, columns): 
      for col in columns:
         self.export_stations_single_plots(col)
      for col in columns:
         self.export_sats_single_plots(col)
   
   def display_stations_multiplot(self, columns):
      master_fig = go.Figure()
      selected_datasets = []
      
      for selected_col in columns:
         self.sort_stations_by_col(selected_col)
         
         for index, station_collection in enumerate(self.station_collections):
            if index == 0:  
               sorting_type = 'Mean'
            elif index == 1: 
               sorting_type = 'Median' 
               continue
            elif index == 2: 
               sorting_type = '2sigma'
               #continue
               
            elif index == 3:
               sorting_type = '3sigma'
               # continue
            
            
         #2sigma of 2sigma  - > 2sigma (2sigma)
         #mean of Max -> Max (mean)
         #highest of Max -> Max (max/3sigma)
         #mean of min
         #mean of mean - > Mean ()
            
            stations, values = [], []
            for station_register in station_collection:
               stations.append(station_register[0])
               values.append(station_register[1])
               
            selected_datasets.append([selected_col, sorting_type, stations, values])
            
      trace_tabs = []
      for idx, dataset in enumerate(selected_datasets):
          trace_set = go.Bar(
                              dict(
                                   visible=False, # width = 1,
                                   x = dataset[2],
                                   y = dataset[3],
                                   text = ['<b>' + str(value)[:5] + '</b>' for value in dataset[3]],
                                   textposition='outside',
                                   insidetextfont = {'color': 'white'},
                                   outsidetextfont= {'color': '#333333'},
                                   marker = dict(
                                       line=dict(color='rgba(0,0,0,0)', width=0),
                                       color = dataset[3], #pattern = dict(shape = '.')
                                       colorbar = {'title': '', 'outlinecolor': 'rgba(0,0,0,0)'},
                                       colorscale = [[0, 'rgb(255, 219, 59)'], [0.8, 'rgb(255, 50, 36)'], [1, 'rgb(156, 2, 2)']]
                                     # colorscale =     [[0, 'rgb(238, 76, 216)'], [0.5, 'rgb(100, 33, 91)'], [1, 'rgb(52, 29, 66)']]
                                  )
                               )
                           )
          if idx == 0:
             trace_set.visible = True
          master_fig.add_trace(go.Bar(trace_set))
          
          #create a tab for every trace
          trace_button = dict(
             label = dataset[0] + '_' + dataset[1],
             method='update',
             args=[
                    {'visible': [True if cycle  == idx else False for cycle in range(len(selected_datasets))]},
                    {
                       'title': {
                                'text': '<b>source ~ ' + self.loaded_file_id + '<br>[column seed: ' 
                                + dataset[0].title() + ']  [sorting type: ' + dataset[1].title() + ']' 
                                + '  [data: ' + self.data_identifier + ']</b>',
                                'x': 0.186,  # Align the title to the left
                                },
                        'xaxis': {'tickvals': dataset[2], 'ticktext': dataset[2], 'title': '<b>Station identifier</b>'},
                        'yaxis': {'tickmode': 'auto', 'range': [0, max(dataset[3]) * 2]}, #'title': trace_setting['y_title']
                    }
             ]
          )
          trace_tabs.append(trace_button)

      # Add buttons to layout as individual buttons
      master_fig.update_layout(
          updatemenus=[
                       dict(
                              type="buttons",
                              direction="down",
                              buttons=trace_tabs[:len(trace_tabs)],  # First half of the buttons
                              # x = 0.1,  # Position the first stack on the left
                              pad={"r": 150, "t": 0},  # Adjust the padding as needed
                              showactive=False,
                              bgcolor='#292726',  # Change button background color
                              bordercolor='#FFFFFF', 
                              font=dict(color='#ff4124'), 
                          ),
                       # dict(
                       #        type="buttons",
                       #        direction="down",
                       #        buttons=trace_tabs[len(trace_tabs)//2:],  # First half of the buttons
                       #        showactive=False,
                       #        bgcolor='#292726',  # Change button background color
                       #        bordercolor='#FFFFFF', 
                       #        font=dict(color='#ff4124'), 
                       #    ),
          ],
          # width = int(ctypes.windll.user32.GetSystemMetrics(0)) * 0.90,
          # width = 1280 * 0.90,
          template = 'ggplot2',
          # margin = dict(l=int(ctypes.windll.user32.GetSystemMetrics(0)) * 0.90),
          # margin = dict(l = int(ctypes.windll.user32.GetSystemMetrics(0)) * 0.90 * 0.2),
          plot_bgcolor = '#fcf8f7',
          bargap = 0.4,   
          barmode='group',  # Group bars in the same subplot
      )
      master_fig.update_traces(marker_line_color='#292726', marker_line_width=2, opacity=1, textfont_size=13)
      #marker_color='rgb(158,202,225)
      # marker_line_color='rgb(8,48,107)'
      
      #Apply properties defined in the first button setting to the initial plot
      initial_layout_settings = trace_tabs[0]['args'][1]
      master_fig.update_layout(**initial_layout_settings)
      master_fig.show()
      master_fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0]
                     + '_' + self.data_identifier + '_multiStationPlot.html', auto_open=False) 
      #clear pipe
      for sorted_list in self.station_collections:
          sorted_list.clear()
      self.station_collections.clear()
      
   def display_sats_multiplot(self, columns):
     master_fig = make_subplots(rows=3, cols=1,  shared_xaxes = False, shared_yaxes = False, vertical_spacing = 0.1)
     selected_datasets = []
     
     for selected_col in columns:
        self.sort_sats_by_col(selected_col)
        
        for index, sat_collection in enumerate(self.sat_collections):
           if index == 0:  
              sorting_type = 'Mean'
           elif index == 1: 
              sorting_type = 'Median' 
           elif index == 2: 
              sorting_type = '2Sigma'
              # continue
           elif index == 3:
              sorting_type = '3Sigma'
              # continue
           
           #sat_sys GPS, BDS, GAL
           for sys_set in sat_collection:  
              sat_prn, residuals = [], []
              for sat_data in sys_set:
                 sat_prn.append(sat_data[1])
                 residuals.append(sat_data[2])
              selected_datasets.append([sat_data[0], selected_col, sorting_type, sat_prn, residuals])
        
        for sorting_type_dataset in self.sat_collections:
           sorting_type_dataset.clear()
      
     false_series = []
     for idx, false_set in enumerate(selected_datasets):
          false_subset = [False] * len(selected_datasets)
          if idx % 3 == 0:
             false_subset[idx:idx+3] = [True] * 3
             false_series.append(false_subset)
     false_selector = iter(false_series)
            
     trace_tabs = []
     for idx, dataset in enumerate(selected_datasets):
         if dataset[0] == 'G':
            color_set = [[0, 'rgb(43, 176, 238)'], [0.25, 'rgb(0, 102, 204)'], [1, 'rgb(11, 44, 59)']]
         elif dataset[0] == 'C':
            color_set = self.bar_colors[4]
         elif dataset[0] == 'E':
            color_set = self.bar_colors[2]
            
         #create a plot for every dataset loaded   
         trace_set = go.Bar(
                             dict(
                                  name = dataset[0],
                                  visible = False,
                                  x = dataset[3],
                                  y = dataset[4],
                                  text = [str(value)[:5] for value in dataset[4]], #
                                  insidetextfont = {'color': 'white'},  # outsidetextfont = {'color': 'white'}, 
                                  showlegend = True,
                                  marker = dict(
                                                line=dict(color='rgba(0,0,0,0)', width=0),
                                                color = dataset[4],
                                                colorscale = color_set,  #colorbar = {'title': '', 'outlinecolor': 'rgba(0,0,0,0)'},
                                               )
                              ),
                          )
         if idx in [0, 1, 2]:
             trace_set.visible = True  # trace_set.name = dataset[0]    
         
         #tracegroup
         if dataset[0] == 'G':   
            master_fig.add_trace(go.Bar(trace_set), row = 1, col = 1)
            master_fig.update_xaxes(title_text="<b>GPS identifier</b>", row=1, col=1)
            axis_G = dataset
         elif dataset[0] == 'C':
            master_fig.add_trace(go.Bar(trace_set), row = 2, col = 1)
            master_fig.update_xaxes(title_text="<b>BDS identifier</b>", row=2, col=1)
            axis_C = dataset
         elif dataset[0] == 'E':
            master_fig.add_trace(go.Bar(trace_set), row = 3, col = 1)
            master_fig.update_xaxes(title_text="<b>GAL identifier</b>", row=3, col=1)
            axis_E = dataset
            
            trace_button = dict(
                                 label = dataset[1] + '_' + dataset[2],
                                 method='update',
                                 args=[
                                           {'visible': next(false_selector)},
                                           {'title': {
                                                 'text': '<b>source ~ ' + self.loaded_file_id + '<br>[column seed: ' 
                                                 + dataset[1].title() + ']  [sorting type: ' + dataset[2].title() + ']' 
                                                 + '  [data: ' + self.data_identifier + ']</b>',
                                                 'x': 0.186,  # Align the title to the left
                                                 }
                                           }
                                       ],
                                 
                                 # 'text': '<b>source ~ ' + self.loaded_file_id + '<br>[column seed: ' 
                                 # + dataset[0].title() + ']  [sorting type: ' + dataset[1].title() + ']' 
                                 # + '  [' + self.data_identifier + ']</b>',
                                 # 'x': 0.2,  # Align the title to the left
                               )
            trace_tabs.append(trace_button)
     
     #adding ticknames to subplots        
     master_fig.update_layout(
               xaxis1_ticktext=[(axis_G[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_G[0]+str(sat_id)) for sat_id in axis_G[3]],
               xaxis1_tickvals=axis_G[3],
               xaxis2_ticktext=[(axis_C[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_C[0]+str(sat_id)) for sat_id in axis_C[3]],
               xaxis2_tickvals=axis_C[3],
               xaxis3_ticktext=[(axis_E[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_E[0]+str(sat_id)) for sat_id in axis_E[3]],
               xaxis3_tickvals=axis_E[3],
               template='ggplot2',
               plot_bgcolor='#e8f6ff',
               updatemenus=[
                             dict(
                                    type="buttons",
                                    direction="down",
                                    buttons=trace_tabs[:len(trace_tabs)//2],  # First half of the buttons
                                    # x = 0.1,  # Position the first stack on the left
                                    pad={"r": 150, "t": 0},  # Adjust the padding as needed
                                    showactive=False,
                                    bgcolor='#292726',  # Change button background color
                                    bordercolor='#FFFFFF', 
                                    font=dict(color='#ff4124'), 
                                ),
                             dict(
                                    type="buttons",
                                    direction="down",
                                    buttons=trace_tabs[len(trace_tabs)//2:],  # First half of the buttons
                                    showactive=False,
                                    bgcolor='#292726',  # Change button background color
                                    bordercolor='#FFFFFF', 
                                    font=dict(color='#ff4124'), 
                                )
                            ]
               )
     
     #Apply properties defined in the first button setting to the initial plot
     initial_layout_settings = trace_tabs[0]['args'][1]
     master_fig.update_layout(**initial_layout_settings)
     master_fig.show()
     master_fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0]
                    + '_' + self.data_identifier + '_multiSatSystemPlot.html', auto_open=False) 
     
     #clear pipe
     for sorted_list in self.sat_collections:
        sorted_list.clear()
     self.sat_collections.clear()
     
   def display_combined_plot(self, columns):
         master_fig = make_subplots(rows=4, cols=1,  shared_xaxes = False, shared_yaxes = False, 
                                    row_heights = [0.2, 0.2, 0.2, 0.15], vertical_spacing = 0.11)
         
         #creating datasets for traces
         selected_datasets, available_identifiers = [], []
         for residual_idx in range(self.number_blocks):
            self.loaded_csv = self.residual_blocks[residual_idx][1] #[0][X] -> residual data blocks
            self.data_identifier = self.residual_blocks[residual_idx][0] #[X][0] -> residual names/types
            available_identifiers.append(self.data_identifier)
            
            #initializing datasets for traces, tracegroups of different sets matching the same type
            for selected_col in columns:
               self.sort_sats_by_col(selected_col)
               self.sort_stations_by_col(selected_col)
               
               #adding an extra vector (stations) to the sats: sats + stations combined
               for idx, dataset in enumerate(self.sat_collections):
                  self.sat_collections[idx].append(self.station_collections[idx])
               
               for index, sat_collection in enumerate(self.sat_collections):
                  #mean of mean_col          
                  #mean of max_col -> Max (mean)
                  #mean of min_col
                  #2sigma of 2sigma_col  - > 2sigma (2sigma)
                  #highest/3sigma of max_col -> Max (max/3sigma)
                  
                  if index == 0:  #mean
                     if selected_col == 'mean':
                        sorting_type = 'Mean'
                     elif selected_col == 'max':
                        sorting_type = 'Mean'
                     elif selected_col == 'min':
                        sorting_type = 'Mean'
                     else:
                        continue
                  elif index == 1:  #median
                     sorting_type = 'Median' 
                     continue
                  elif index == 2: #2sigma
                     if selected_col == '2sigma':
                        sorting_type = '2S'
                     else:
                        continue
                  elif index == 3: #3sigma
                     if selected_col == 'max':
                        sorting_type = 'Upper'
                     else:
                        continue
                  
                  #sat_sys GPS, BDS, GAL
                  for sys_set in sat_collection:  
                     data_ids, residuals = [], []
                     for sat_data in sys_set:
                        if len(sat_data) > 2:
                           data_ids.append(sat_data[1])
                           residuals.append(sat_data[2])
                        else:
                           data_ids.append(sat_data[0])
                           residuals.append(sat_data[1])
                           sat_data[0] = 'Stations'
                     selected_datasets.append([sat_data[0], selected_col, sorting_type, data_ids, residuals, self.data_identifier])
               
               for sorting_type_dataset in self.sat_collections:
                  sorting_type_dataset.clear()
         
         #preparing traces
         false_series = []
         for idx, false_set in enumerate(selected_datasets):
              false_subset = [False] * len(selected_datasets)
              if idx % 4 == 0:
                 false_subset[idx:idx + 4] = [True] * 4
                 false_series.append(false_subset)
         false_selector = iter(false_series)
         
         colors_to_buttons = iter(self.colors_to_buttons)
         
         #creating traces
         trace_tabs = []
         for idx, dataset in enumerate(selected_datasets):
             if dataset[0] == 'G':
                color_set = [[0, 'rgb(43, 176, 238)'], [0.25, 'rgb(0, 102, 204)'], [1, 'rgb(11, 44, 59)']]
             elif dataset[0] == 'C':
                color_set = self.bar_colors[4]
             elif dataset[0] == 'E':
                color_set = self.bar_colors[2]
             elif dataset[0] == 'Stations':
                color_set = self.bar_colors[3]
                
             #create a plot for every dataset loaded   
             trace_set = go.Bar(
                                 dict(
                                      name = dataset[0],
                                      visible = False,
                                      x = dataset[3],
                                      y = dataset[4],
                                      text = [str(value)[:5] for value in dataset[4]], #
                                      insidetextfont = {'color': 'white'},  # outsidetextfont = {'color': 'white'}, 
                                      showlegend = True,
                                      marker = dict(
                                                    line = dict(color='rgba(0,0,0,0)', width = 0),
                                                    color = dataset[4],
                                                    colorscale = color_set,  #colorbar = {'title': '', 'outlinecolor': 'rgba(0,0,0,0)'},
                                                   )
                                  ),
                              )
             if idx in [0, 1, 2, 3]:
                 trace_set.visible = True  # trace_set.name = dataset[0]    
             
             #tracegroup
             if dataset[0] == 'G':   
                master_fig.add_trace(go.Bar(trace_set), row = 1, col = 1)
                master_fig.update_xaxes(title_text='<b>GPS identifier</b>',title_font=dict(size=12), row=1, col=1)
                axis_G = dataset
             elif dataset[0] == 'C':
                master_fig.add_trace(go.Bar(trace_set), row = 2, col = 1)
                master_fig.update_xaxes(title_text='<b>BDS identifier</b>', title_font=dict(size=12), row=2, col=1)
                axis_C = dataset
             elif dataset[0] == 'E':
                master_fig.add_trace(go.Bar(trace_set), row = 3, col = 1)
                master_fig.update_xaxes(title_text='<b>GAL identifier</b>', title_font=dict(size=12), row=3, col=1)
                axis_E = dataset
             elif dataset[0] == 'Stations':
                master_fig.add_trace(go.Bar(trace_set), row = 4, col = 1)
                master_fig.update_xaxes(title_text='<b>Station identifier</b>', title_font=dict(size=12), row=4, col=1)
                axis_ST = dataset
                
                if dataset[5] in available_identifiers:
                   passed_color = next(colors_to_buttons)
                   available_identifiers.remove(dataset[5])
                   
                trace_button = dict(
                                     # label = dataset[1] + '_' + dataset[2],
                                     label = dataset[2].capitalize() + ' of ' + dataset[1].upper() 
                                     + ' [<span style="color:{0}">'.format(passed_color) + dataset[5] + '</span>]',
                                     method='update',
                                     args=[
                                               {'visible': next(false_selector)},
                                               {'title': {
                                                     'text': '<b>source ~ ' + self.loaded_file_id + '<br>[column seed: ' 
                                                     + dataset[1].title() + ']  [sorting type: ' + dataset[2].title() + ']' 
                                                     + '  [data: ' + dataset[5] + ']</b>',
                                                     'x': 0.25,  # Align the title to the left
                                                     'font': {'size': 15}  
                                                     }
                                               }
                                           ],
                                   )
                trace_tabs.append(trace_button)
         
         #adding ticknames to subplots        
         master_fig.update_layout(
                   xaxis1_ticktext=[
                      (axis_G[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_G[0]+str(sat_id)) for sat_id in axis_G[3]
                      ],
                   xaxis1_tickvals=axis_G[3],
                   
                   xaxis2_ticktext=[
                      (axis_C[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_C[0]+str(sat_id)) for sat_id in axis_C[3]
                      ],
                   xaxis2_tickvals=axis_C[3],
                   # xaxis2_tickmode='array',
                   
                   xaxis3_ticktext=[
                      (axis_E[0]+'0'+str(sat_id)) if len(str(sat_id)) < 2 else (axis_E[0]+str(sat_id)) for sat_id in axis_E[3]
                      ],
                   xaxis3_tickvals=axis_E[3],
                   
                   xaxis4_ticktext=[
                      str(sat_id) for sat_id in axis_ST[3]
                      ],
                   xaxis4_tickvals=axis_ST[3],
                   
                   template='ggplot2',
                   plot_bgcolor='#e8f6ff',
                   )
         
         #
         master_fig.update_layout(
            updatemenus=[
                          dict(
                                  type='buttons',
                                  direction="down",
                                  buttons=trace_tabs[:len(trace_tabs)//2],  # First half of the buttons
                                  # x = 0.1,  # Position the first stack on the left
                                  pad={"r": 180, "t": 0},  # Adjust the padding as needed
                                  showactive=False,
                                  bgcolor='#292726',  # Change button background color
                                  bordercolor='#FFFFFF', 
                                  font=dict(color='#bad6e3'), ##ff4124
                              ),
                          dict(
                                 type='buttons',
                                 direction='down',
                                 buttons=trace_tabs[len(trace_tabs)//2:],  # First half of the buttons
                                 showactive=False,
                                 bgcolor='#292726',  # Change button background color
                                 bordercolor='#FFFFFF', 
                                 font=dict(color='#bad6e3'), #78c4ff
                             )
                         ]
            )
         
         #Apply properties defined in the first button setting to the initial plot
         initial_layout_settings = trace_tabs[0]['args'][1]
         master_fig.update_layout(**initial_layout_settings)
         master_fig.show()
         master_fig.write_html(self.output_path + '\\' + (self.loaded_file_id.split('\\'))[-1].split('.')[0]
                         + '_fullSystemPlot.html', auto_open=False) 
         
         #clear pipe
         for idx in range(len(self.sat_collections)):
            self.sat_collections[idx].clear()
            self.station_collections[idx].clear()
         self.sat_collections.clear()
         self.station_collections.clear()
         pass
           
   def load_all_multiplots(self, columns):
      
      for residual_type in self.residual_blocks:
         self.loaded_csv = residual_type[1]
         self.data_identifier = residual_type[0]
         
         self.display_sats_multiplot(columns)
         self.display_stations_multiplot(columns)

class csv_scanner: 
   def __init__(self, config_file, plot_range):
         cfg = ConfigParser()
         cfg.read(r'%s' %config_file)
         print('CSV file scanner initializing..')
         
         for key in cfg['work_directories']:
             if cfg['work_directories'][key] != '':
                 if key == 'csv_source_dir':
                     self.source_dir = cfg['work_directories'][key]
                 elif key == 'output_processed_dir':
                     self.output_dir = cfg['work_directories'][key]
         
         self.csv_dir_scanned = os.listdir(self.source_dir)
         # self.csv_dir_scanned = [self.csv_dir_scanned[0]] #single file
         self.plot_range = plot_range
   
   def run_dir_to_intervals(self, columns):
      for file in self.csv_dir_scanned:
         print('Processing: ' +file+ ' ..')
         file_passed = [self.source_dir + '\\' + file, self.output_dir]
         csv_data = csv_processor(file_passed, self.plot_range)
         csv_data.run(columns)
         del csv_data
         
   def export_dir_to_singleplots(self, columns):
      for file in self.csv_dir_scanned:
         print('Processing: ' +file+ ' ..')
         file_passed = [self.source_dir + '\\' + file, self.output_dir]
         csv_data = csv_processor(file_passed, self.plot_range)
         csv_data.export_all_single_plots(columns)
         del csv_data
         
      
# csv_to_load = [r'C:\Users\CHCUK-02-Finn\Desktop\csvdata_proc\csv_data\2024_009_ppprtk1.csv', 
#                 r'C:\Users\CHCUK-02-Finn\Desktop\csvdata_proc\data_output']
csv_to_load = [
                r'C:\Users\CHCUK-02-Finn\Desktop\general_scan_csv_data\general_scan_full.csv', 
                r'C:\Users\CHCUK-02-Finn\Desktop\general_scan_csv_data\output',
                ]
run_single_file = csv_processor(csv_to_load, [0, 1, 1/40])


run_single_file.display_combined_plot(['max', '2sigma', 'min', 'mean', '3sigma'])
# run_single_file.display_stations_multiplot(['max', '2sigma', 'min', 'mean'])
# run_single_file.load_all_multiplots(['max', '2sigma', 'min', 'mean', 'std', '3sigma'])

# run_single_file.plot_stations('Mean')
# run_single_file.plot_satellites('Mean')

# run_single_file.sort_stations('Max')
# run_single_file.plot_column_by_intervals('Max', [[0, 'rgb(238, 76, 216)'], [1, 'rgb(100, 33, 91)']])

# csv_scan = csv_scanner('csv_settings.conf',  [0, 20, 0.5])
# csv_scan.run_csv_files(['Max','Min'])
   
# csv_scan = csv_scanner('csv_settings.conf',  [0, 20, 0.5])
# csv_scan.export_dir_to_singleplots(['Max','Mean','Min','2sigma','3sigma'])




















# aliceblue, antiquewhite, aqua, aquamarine, azure,
# beige, bisque, black, blanchedalmond, blue,
# blueviolet, brown, burlywood, cadetblue,
# chartreuse, chocolate, coral, cornflowerblue,
# cornsilk, crimson, cyan, darkblue, darkcyan,
# darkgoldenrod, darkgray, darkgrey, darkgreen,
# darkkhaki, darkmagenta, darkolivegreen, darkorange,
# darkorchid, darkred, darksalmon, darkseagreen,
# darkslateblue, darkslategray, darkslategrey,
# darkturquoise, darkviolet, deeppink, deepskyblue,
# dimgray, dimgrey, dodgerblue, firebrick,
# floralwhite, forestgreen, fuchsia, gainsboro,
# ghostwhite, gold, goldenrod, gray, grey, green,
# greenyellow, honeydew, hotpink, indianred, indigo,
# ivory, khaki, lavender, lavenderblush, lawngreen,
# lemonchiffon, lightblue, lightcoral, lightcyan,
# lightgoldenrodyellow, lightgray, lightgrey,
# lightgreen, lightpink, lightsalmon, lightseagreen,
# lightskyblue, lightslategray, lightslategrey,
# lightsteelblue, lightyellow, lime, limegreen,
# linen, magenta, maroon, mediumaquamarine,
# mediumblue, mediumorchid, mediumpurple,
# mediumseagreen, mediumslateblue, mediumspringgreen,
# mediumturquoise, mediumvioletred, midnightblue,
# mintcream, mistyrose, moccasin, navajowhite, navy,
# oldlace, olive, olivedrab, orange, orangered,
# orchid, palegoldenrod, palegreen, paleturquoise,
# palevioletred, papayawhip, peachpuff, peru, pink,
# plum, powderblue, purple, red, rosybrown,
# royalblue, rebeccapurple, saddlebrown, salmon,
# sandybrown, seagreen, seashell, sienna, silver,
# skyblue, slateblue, slategray, slategrey, snow,
# springgreen, steelblue, tan, teal, thistle, tomato,
# turquoise, violet, wheat, white, whitesmoke,
# yellow, yellowgreen


# # Calculate the number of buttons in each section
# buttons_per_section = len(trace_tabs) // 5

# # Initialize an empty list to store buttons for each section
# button_sections = []

# # Slice the trace_tabs list into 5 sections
# for i in range(5):
#     start_index = i * buttons_per_section
#     end_index = (i + 1) * buttons_per_section
#     if i == 4:  # For the last section, include remaining buttons
#         button_sections.append(trace_tabs[start_index:])
#     else:
#         button_sections.append(trace_tabs[start_index:end_index])

# # Create updatemenus using button_sections
# updatemenus = []
# for buttons in button_sections:
#     menu = dict(
#         type='buttons',
#         direction="down",
#         buttons=buttons,
#         showactive=False,
#         bgcolor='#292726',  # Change button background color
#         bordercolor='#FFFFFF',
#         font=dict(color='#5ec1ff'),
#     )
#     updatemenus.append(menu)
