#!/c/Python25 python
#---------------------------------------------------------------------------------------
"""
 LSMetrics - Ecologically Scaled Landscape Metrics
 Version 1.0.0
 
 Milton C. Ribeiro - mcr@rc.unesp.br
 John W. Ribeiro - jw.ribeiro.rc@gmail.com
 Bernardo B. S. Niebuhr - bernardo_brandaum@yahoo.com.br
 
 Laboratorio de Ecologia Espacial e Conservacao (LEEC)
 Universidade Estadual Paulista - UNESP
 Rio Claro - SP - Brasil
 
 LSMetrics is a software designed to calculate landscape metrics and
 landscape statistics and generate maps of landscape connectivity.
 Also, the software is designed to prepare maps and enviroment for running 
 BioDIM, an individual-based model of animal movement in fragmented landscapes.
 The software runs in a GRASS GIS environment and uses raster images as input.

 To run LSMetrics:
 
 python LSMetrics_v1_0_0.py
 
 Copyright (C) 2015-2016 by Milton C. Ribeiro, John W. Ribeiro, and Bernardo B. S. Niebuhr.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 2 of the license, 
 or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
#---------------------------------------------------------------------------------------

# Import modules
import os, platform
import grass.script as grass
from PIL import Image
import wx
import numpy as np
import math # SUBSTITUIR POR NUMPY? numpy.log(number)
from sets import Set
import collections
import warnings

# Platform in which LSMetrics is being run
CURRENT_OS = platform.system()

# LSMetrics Version:
VERSION = 'v. 1.0.0'

################
# CONFERIR LISTA DE PATTERN MULTIPLE COM O JOHN (E TODAS AS VEZES QUE APARECEU O [PERMANENT] OU [userbase])

########################
# -arrumar script R para gerar as figuras que queremos
# como conversa o R com o grass? da pra rodar o script R em BATCH mode?

#try:
  #self.escalas = map(int, event.GetString().split(','))
  #self.logger.AppendText('Landscape scale(s): \n'+','.join(str(i) for i in self.escalas)+ '\n')            
  #except:
    #self.escalas = [-1]
    #print "Could not convert at least one of the scale values to an integer."

#----------------------------------------------------------------------------------
def reclass_frag_cor(mappidfrag,dirs):
  """
  essa funcao abre o txt cross separa os de transicao validos
  reclassifica o mapa de pidfrag onde 1
  """
  os.chdir(dirs)
  with open("table_cross.txt") as f:
      data = f.readlines()
  
  contfirst=0
  list_pidfrag=[]
  list_pid_cor=[]
  for i in data:
      if contfirst>0: # pulando a primeira linha da tabela 
          if "no data" in i:
              pass
          else:
              lnsplit=i.split(' ')
              list_pidfrag.append(lnsplit[2].replace(';',''))
              list_pid_cor.append(lnsplit[4])    
      contfirst=1
  list_pidfrag=map(int, list_pidfrag)   
  list_pid_cor=map(int, list_pid_cor)   
  counter=collections.Counter(list_pid_cor)
  txt_rules=open("table_cross_reclass_rules.txt",'w')
  for i in counter.keys():
    if counter[i]>=2:
        temp=2
    else:
        temp=1
    txt_rules.write(`i`+'='+`temp`+'\n')
  txt_rules.close() 
  grass.run_command('r.reclass',input=mappidfrag,output=mappidfrag+'_reclass',rules='table_cross_reclass_rules.txt', overwrite = True)
  
  
  


#----------------------------------------------------------------------------------
# Auxiliary functions

#-------------------------------
# Function selectdirectory
def selectdirectory():
  '''
  Function selectdirectory
  
  This function opens a dialog box in the GUI and asks the user to select the output folder
  for saving files. It then returns the path to this folder as a string.
  '''
  
  # Create a dialog box asking for the output folder
  dialog = wx.DirDialog(None, "Select the folder where the output files will be saved:",
                        style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
  
  # After selected, the box closes and the path to the chosen folder is returned
  if dialog.ShowModal() == wx.ID_OK:
    #print ">>..................",dialog.GetPath()
    return dialog.GetPath()

#-------------------------------
# Function create_TXTinputBIODIM
def create_TXTinputBIODIM(list_maps, outputfolder, filename):
  '''
  Function create_TXTinputBIODIM
  
  This function creates the output text files that BioDIM package need to the names of the maps
  within the GRASS GIS location and read them.
  
  Input:
  list_maps: list with strings; a python list of map names generated within the GRASS GIS location.
  outputfolder: string; a folder where the output text files will be saved/written.
  filename: string; the name of the file to be created.
  
  Output:
  A file with the names of the maps within GRASS GIS.
  '''
  
  # Open a file in the output folder
  txtMap = open(outputfolder+"/"+filename+".txt", "w")

  # For each map in the list of maps, it writes a line
  for i in list_maps:
    txtMap.write(i+'\n')
    
  txtMap.close() # Close the file
    
#-------------------------------
# Function createtxt
def createtxt(input_map, outputfolder, filename = ''):
  """
  Function createtxt
  
  This function creates text files with statistics (area, percentage) regarding the classes within maps
  generated by a function in LSMetrics.
  
  Input:
  input_map: string; the name of the input map the user wants statistics from
  outputfolder: string; a folder where the output text files will be saved/written.
  filename: string; the name of the file to be created.
  
  Output:
  This function creates a text file with:
  - Values of area, in hectares, for edge, interior and core areas (for EDGE metrics)
  - Values of area, in hectares, for each patch (for PATCH, FRAG and CON metrics)
  """
  
  # Define region
  grass.run_command('g.region', rast=input_map)  
  # Calculate area and percentage statistics for the input map using r.stats
  x = grass.read_command('r.stats', flags = 'ap', input = input_map)
  
  # Separating values by line
  y = x.split('\n')
  
  # Change to the output folder and select the name of the output text file
  os.chdir(outputfolder)
  if filename != '': 
    name = filename+'.txt'
  else:
    name = input_map+'.txt' # If no specific name is given, call it 'input_map'
  
  # Initialize arrays
  idd = []
  areas = []
  
  if len(y) != 0:
    # For each element in the list of values
    for i in y:
      if i != '':
        ##print i
        # Split by space
        f = i.split(' ')
        
        # In the last line we may have *; stop in this case
        if '*' in f :
          break
        # If it is not the last line
        else:
          ##print f
          # Get id (raster value)
          ids = f[0]
          ids = int(ids)
          idd.append(ids)
          ##print ids
          # Get area in m2 and transforms to hectares
          ha = f[1]
          ha = float(ha)
          haint = float(ha)
          haint = haint/10000+1
          areas.append(haint)
          ##print haint
          
    # Calculate the percentage
    percentages = [float(i)/sum(areas) for i in areas]
    
    # Open output file
    txt_file = open(name, 'w')
    
    # Write header
    txt_file.write('CODE'+','+'AREA_HA'+','+'PROPORTION\n')    

    # For each element
    for i in range(len(idd)):
      # Write line in the output file
      txt_file.write(`idd[i]`+','+`areas[i]`+','+`percentages[i]`+'\n')
          
    # Close the output file
    txt_file.close()
    
#-------------------------------
# Function rulesreclass
def rulesreclass(input_map, outputfolder):
  """
  Function rulesreclass
  
  This function sets the rules for area reclassification for patch ID, using stats -a for each patch.
  The output is a text file with such rules. 
  
  Input:
  input_map: string; the name of the input map the user wants statistics from
  outputfolder: string; a folder where the output text files will be saved/written.
  
  Output:
  This function creates a text file area values for each patch ID, used to reclassify and 
  generate maps area maps. It returns the name of the text files with reclassification rules
  """
  
  # Define region
  grass.run_command('g.region', rast=input_map)  
  # Calculate area and percentage statistics for the input map using r.stat  
  x = grass.read_command('r.stats', flags='a', input=input_map)
  
  # Separating values by line
  y=x.split('\n')
 
  # Change to the output folder and select the name of the output text file
  os.chdir(outputfolder)
  txt_file_name = input_map+'_rules.txt'
    
  if y!=0:
    
    # Open output file 
    txtreclass = open(txt_file_name, 'w')
    
    # For each element in the list of values
    for i in y:
      if i != '':
        ##print i
        # Split by space
        f=i.split(' ')
        
        # In the last line we may have *; stop in this case
        if '*' in f or 'L' in f :
          break
        # If it is not the last line
        else:
          ##print f
          # Get id (raster value)
          ids=f[0]
          ids=int(ids)
          ##print ids
          # Get area in m2 and transforms to hectares
          ha=f[1]
          ha=float(ha)
          haint=float(round(ha))
          haint2=haint/10000+1
          
          # Write line in the output file
          txtreclass.write(`ids`+'='+`haint2`+ '\n')
          
    txtreclass.close()
    
  # Return the name of the reclass file generated
  return txt_file_name

#----------------------------------------------------------------------------------
# Leading with scales, lengths, and pixel sizes - organization

#-------------------------------
# Function connectivity_scales
def connectivity_scales(input_map, list_gap_crossing):
  """
  Function connectivity_scales
  
  This function calculates the size(s) and number of pixels corresponding to the scales maps will be dilatated
  to be integrated by gap crossing distances.
  If the gap crossing distance is 120m for example, maps are dilatated by 60m (half of it), so that patches
  distant less that 120m are considered functionally connected. Then, this half-distance is returned, and its
  equivalent in number of pixels.
  
  Input:
  input_map: string; name of the input map (from where the resolution is assessed).
  list_gap_crossing: python list with float numbers; list of gap crossing distances, in meters, to be considered.
  
  Output:
  The number of pixels and distance by which habitat patches must be dilatated to assess functional connectivity
  of habitat patches.
  """
  
  # Assess the resolution of the input map
  map_info = grass.parse_command('g.region', rast = input_map, flags = 'm')
  res = float(map_info['ewres'])
  
  # Initialize list of edge depth in meters and corridor width in pixels
  list_gap_crossing_meters = []
  list_gap_crossing_pixels = []
  
  # For each value in the list of edge depths
  for i in list_gap_crossing:
    
    # Trasform into float
    cross = float(i)
    # Number of pixels that corresponds to each gap crossing distance
    fine_scale = cross/res
    # Gap crossing is devided by two, since this is the scale that will be dilatated in maps
    gap_crossing_pixels = fine_scale/2
    
    gap_crossing_pixels = int(round(gap_crossing_pixels, ndigits=0))

    # Rounding to an integer odd number of pixels
    # If the number is even, we sum 1 to have an odd number of pixel to the moving window    
    if gap_crossing_pixels %2 == 0:
      gap_crossing_pixels = int(gap_crossing_pixels)
      gap_crossing_pixels = 2*gap_crossing_pixels + 1
      list_gap_crossing_meters.append(int(cross/2)) # append the gap crossing in meters to the list
      list_gap_crossing_pixels.append(gap_crossing_pixels) # append the gap crossing in pixels to the list
      
    # If the number is already odd, it is ok    
    else:
      gap_crossing_pixels = int(round(gap_crossing_pixels, ndigits=0))
      gap_crossing_pixels = 2*gap_crossing_pixels + 1
      list_gap_crossing_meters.append(int(cross/2)) # append the gap crossing in meters to the list
      list_gap_crossing_pixels.append(gap_crossing_pixels) # append the gap crossing in pixels to the list
        
  # Return both lists
  return list_gap_crossing_meters, list_gap_crossing_pixels

#-------------------------------
# Function frag_scales 
def frag_scales(input_map, list_edge_depths):
  """
  Function frag_scales
  
  This function calculates the size(s) and number of pixels corresponding to
  to corridor width to be removed from fragment size maps, based on a (list of) value(s) of edge depth.
  The size of corridors to be removed is considered as twice the edge depth.
  
  Input:
  input_map: string; name of the input map (from where the resolution is assessed).
  list_edge_depths: python list with float numbers; list of edge depths, in meters, to be considered.
  
  Output:
  The number of pixels which correspond to the width of the corridors to be excluded from habitat patch maps - 
  corridor width is considered as twice the edge depth.
  As this values in pixels are used in the GRASS GIS function as the size of the moving window in r.neighbors, 
  remind that this size must be always odd, and the function already does that.
  """
  
  # Assess the resolution of the input map
  map_info = grass.parse_command('g.region', rast = input_map, flags='m')
  res = float(map_info['ewres'])

  # Initialize list of edge depth in meters and corridor width in pixels
  list_edge_depths_meters = []
  list_corridor_width_pixels =[]
  
  # For each value in the list of edge depths
  for i in list_edge_depths:
    
    depth = float(i)
    # Number of pixels that corresponds to each edge depth
    fine_scale = depth/res
    # Corridor width is considered as twice the edge depth
    corridor_width_pix = fine_scale * 2
    
    # Rounding to an integer number of pixels
    # If the number is even, we sum 1 to have an odd number of pixel to the moving window
    if corridor_width_pix %2 == 0:
      corridor_width_pix = int(corridor_width_pix)
      corridor_width_pix = corridor_width_pix + 1
      list_edge_depths_meters.append(int(depth)) # append the edge depth to the list
      list_corridor_width_pixels.append(corridor_width_pix) # append the corridor width to the list
      
    # If the number is already odd, it is ok
    else:
      corridor_width_pix = int(round(corridor_width_pix, ndigits=0))
      list_edge_depths_meters.append(int(depth)) # append the edge depth to the list
      list_corridor_width_pixels.append(corridor_width_pix) # append the corridor width to the list
      
  # Return both lists
  return list_edge_depths_meters, list_corridor_width_pixels


#------------------------------- 
# Function get_size_pixels
def get_size_pixels(input_map, scale_in_meters):
  '''
  Function get_size_pixels
  
  This function uses the scale difined by the user and the pixel size to 
  return the number of pixels that correspond to the scale
  (to define the size of the moving window)
  
  Input:
  input_map: string; name of the input map, from which the resolution/pixel size will be taken.
  scale_in_meters: float or integer; size of the moving window in meters.
  
  Output:
  The number of pixels which correspond to the size of the moving window, to be used in a GRASS GIS
  function such as r.neighbors. Remind that this size must be always odd, and the function already does that.
  '''
  
  # Assess the resolution of the input map
  map_info = grass.parse_command('g.region', rast = input_map, flags = 'm')      
  res = float(map_info['ewres'])
  #######################################
  #scale_in_pixels = (float(scale_in_meters)*2)/res # should we really multiply it by 2????
  scale_in_pixels = (float(scale_in_meters))/res # should we really multiply it by 2????
  
  # Checking if number of pixels of moving window is integer and even
  # and correcting it if necessary
  if int(scale_in_pixels)%2 == 0: # If the number of pixels is even, add 1
    scale_in_pixels = int(scale_in_pixels)
    scale_in_pixels = scale_in_pixels + 1 
  else: # If the number of pixels is odd, it is ok
    scale_in_pixels = int(scale_in_pixels)
  
  # Returns the scale in number of pixels
  return scale_in_pixels

#----------------------------------------------------------------------------------
# Functions of Landscape Metrics

#-------------------------------
# Function create_binary
def create_binary(list_maps, list_habitat_classes, zero = True,
                  prepare_biodim = False, calc_statistics = False, 
                  prefix = '', add_counter_name = False, export = False, dirout = ''):
  """
  Function create_binary
  
  This function reclassify a (series of) input map(s) into a (series of) binary map(s), with values
  1/0 or 1/null. This is done by considering a list of values which represent a given type of habitat 
  or environment, which will be reclassified as 1 in the output; all the other values in the map 
  will be set to zero/null value.
  
  Input:
  list_maps: list with strings; a python list with maps loaded in the GRASS GIS location.
  list_habitat_classes: list with strings or integers; a python list of values that correspond to habitat in the input raster maps, and will be considered as 1.
  zero: (True/False) logical; if True, non-habitat values are set to zero; otherwise, they are set as null values.
  prepare_biodim: (True/False) logical; if True, maps and input text files for running BioDIM package are prepared.
  calc_statistics: (True/False) logical; if True, statistics are calculated and saved as an output text file.
  prefix: string; a prefix to be appended in the beginning of the output map names.
  add_counter_name: (True/False) logical; if True, a number is attached to the beginning of each outputmap name, in the order of the input, following 0001, 0002, 0003 ...
  export: (True/False) logical; if True, the maps are exported from GRASS.
  dirout: string; folder where the output maps will be saved when exported from GRASS. If '', the output maps are generated but are not exported from GRASS.
  
  Output:
  A binary map where all the map pixels in 'list_habitat_classes' are set to 1 and all the other pixels are
  set to zero (if zero == True, or null if zero == False).
  The function returns a python list with the names of the binary class maps created.
  If prepare_biodim == True, a file with binary maps to run BioDIM is generated.
  If calc_statistics == True, a file with the area/proportion of each class (habitat/non-habitat) is generated.
  """
  
  # If we ask to export something but we do not provide an output folder, it shows a warning
  if (export or prepare_biodim or calc_statistics) and dirout == '':
    warnings.warn("You are trying to export files from GRASS but we did not set an output folder.")
  
  # A list of map names is initialized, to be returned
  list_maps_habmat = []
   
  # Initialize counter, in case the user wants to add a number to the map name
  cont = 1
  
  # For each map in the list of input maps
  for i_in in list_maps:
    
    # Putting (or not) a prefix in the beginning of the output map name
    if not add_counter_name:
      pre_numb = ''
    else: # adding numbers in case of multiple maps
      pre_numb = '00000'+`cont`+'_'
      pre_numb = pre_numb[-5:]
    
    # Check if the list of classes is greater than zero
    if len(list_habitat_classes) > 0:
      
      conditional = ''
      cc = 0
      # Creates a condition for all habitat classes being considered as 1
      for j in list_habitat_classes:
        if cc > 0:
          conditional = conditional+' || '
        conditional = conditional+i_in+' == '+str(j)
        cc += 1
      
      # Prefix of the output
      i = prefix+pre_numb+i_in
      
      if zero == True:
      # Calculating binary map with 1/0
        expression = i+'_HABMAT = if('+conditional+', 1, 0)'
      else:
        # Calculating binary map with 1/0
        expression = i+'_HABMAT = if('+conditional+', 1, null())'        

      # Define region and run reclassification using r.mapcalc
      grass.run_command('g.region', rast=i_in)
      grass.mapcalc(expression, overwrite = True, quiet = True)
    
    else: # If the list of habitat values is not > 0, it gives an error.
      raise Exception('You did not type which class is habitat! Map not generated.\n')
    
    # The list of map names is updated
    list_maps_habmat.append(i+'_HABMAT')
    
    # If export == True and dirout == '', the map is not exported; in other cases, the map is exported in this folder
    if export == True and dirout != '':
      os.chdir(dirout)
      grass.run_command('g.region', rast=i+'_HABMAT')
      grass.run_command('r.out.gdal', input=i+'_HABMAT', out=i+'_HABMAT.tif', overwrite = True)
  
    # If calc_statistics == True, the stats of this metric are calculated and exported
    if calc_statistics and dirout != '':
      createtxt(i+'_HABMAT', dirout, i+'_HABMAT')
    
    # Update counter of the map number
    cont += 1
      
  # If prepare_biodim == True, use the list of output map names to create a text file and export it
  if prepare_biodim:
    create_TXTinputBIODIM(list_maps_habmat, dirout, "simulados_HABMAT")
    
  return list_maps_habmat

   
#-------------------------------
# Function patch_size
def patch_size(input_maps, 
               zero = False, diagonal = False,
               prepare_biodim = False, calc_statistics = False, remove_trash = True,
               prefix = '', add_counter_name = False, export = False, export_pid = False, dirout = ''):
  """
  Function patch_size
  
  This function calculates patch area, considering all pixels that are continuous as a single patch.
  Areas are calculated in hectares, assuming that input map projection is in meters.
  
  Input:
  input_maps: list with strings; a python list with maps loaded in the GRASS GIS location. Must be binary class maps (e.g. maps of habitat-non habitat).
  zero: (True/False) logical; if True, non-habitat values are set to zero; otherwise, they are set as null values.
  diagonal: (True/False) logical; if True, cells are clumped also in the diagonal for estimating patch size.
  prepare_biodim: (True/False) logical; if True, maps and input text files for running BioDIM package are prepared.
  calc_statistics: (True/False) logical; if True, statistics are calculated and saved as an output text file.
  remove_trash: (True/False) logical; if True, maps generated in the middle of the calculation are deleted; otherwise they are kept within GRASS.
  prefix: string; a prefix to be appended in the beginning of the output map names.
  add_counter_name: (True/False) logical; if True, a number is attached to the beginning of each outputmap name, in the order of the input, following 0001, 0002, 0003 ...
  export: (True/False) logical; if True, the maps are exported from GRASS.
  export_pid: (True/False) logical; if True, the patch ID (pid) maps are exported from GRASS.
  dirout: string; folder where the output maps will be saved when exported from GRASS. If '', the output maps are generated but are not exported from GRASS.
  
  Output:
  Maps with Patch ID and Area of each patch (considering non-habitat as 0 if zero == True or null if zero == False).
  If prepare_biodim == True, a file with patch size maps to run BioDIM is generated.
  If calc_statistics == True, a file with area per patch in hectares is generated.
  """
  
  # If we ask to export something but we do not provide an output folder, it shows a warning
  if (export or prepare_biodim or calc_statistics) and dirout == '':
    warnings.warn("You are trying to export files from GRASS but we did not set an output folder.")  
  
  # The lists of map names of Patch ID and area are initialized
  lista_maps_pid = []
  lista_maps_area = []  

  # Initialize counter, in case the user wants to add a number to the map name
  cont = 1
  
  # For each map in the list of input maps
  for i_in in input_maps:
    
    # Putting (or not) a prefix in the beginning of the output map name
    if not add_counter_name:
      pre_numb = ''
    else: # adding numbers in case of multiple maps
      pre_numb = '00000'+`cont`+'_'
      pre_numb = pre_numb[-5:]
      
    # Prefix of the output
    i = prefix+pre_numb+i_in

    # Define the region
    grass.run_command('g.region', rast = i_in)
    
    # Clump pixels that are contiguous in the same patch ID
    if diagonal: # whether or not to clump pixels considering diagonals
      grass.run_command('r.clump', input=i_in, output=i+'_patch_clump', overwrite = True, flags = 'd')
    else:
      grass.run_command('r.clump', input=i_in, output=i+'_patch_clump', overwrite = True)
      
    # Takes only what is habitat
    expression1 = i+"_patch_clump_hab = "+i+"_patch_clump * "+i_in
    grass.mapcalc(expression1, overwrite = True, quiet = True)
    # Transforms non-habitat cells into null cells - this is the Patch ID map
    expression2 = i+"_pid = if("+i+"_patch_clump_hab > 0, "+i+"_patch_clump_hab, null())"
    grass.mapcalc(expression2, overwrite = True, quiet = True)
    
    # Reclass pixel id values by calculating the area in hectares
    
    if dirout != '':
      os.chdir(dirout) # folder to save temp reclass file
    # If zero == False (non-habitat cells are considered null)
    if zero == False:
      nametxtreclass = rulesreclass(input_map = i+"_pid", outputfolder = '.')
      grass.run_command('r.reclass', input = i+"_pid", output = i+"_patch_AreaHA", rules=nametxtreclass, overwrite = True)
      os.remove(nametxtreclass)
      # We could also use r.area
      # area - number of pixels
      #grass.run_command("r.area", input = i+"_pid", output = i+"_numpix", overwrite = True)
      # area in hectares
      # Code for taking the area of a pixel in hectares - pixel_size
      #ex = i+"_AreaHA = "+i+"_pid * pixel_size"
      #grass.mapcalc(ex, overwrite = True)
    else: # If zero == True (non-habitat cells are considered as zeros)
      nametxtreclass = rulesreclass(input_map = i+"_pid", outputfolder = '.')
      grass.run_command('r.reclass', input = i+"_pid", output = i+"_patch_AreaHA_aux", rules=nametxtreclass, overwrite = True)
      os.remove(nametxtreclass)      

      # Transforms what is 1 in the binary map into the patch size
      expression3 = i+'_patch_AreaHA = if('+i_in+' == 0, 0, '+i+'_patch_AreaHA_aux)'
      grass.mapcalc(expression3, overwrite = True)    
    
    # The list of map names is updated
    lista_maps_pid.append(i+"_pid")
    lista_maps_area.append(i+"_patch_AreaHA")
     
    # If export == True and dirout == '', the map is not exported; in other cases, the map is exported in this folder
    if export == True and dirout != '':
      os.chdir(dirout)
      grass.run_command('g.region', rast = i+"_patch_AreaHA")
      grass.run_command('r.out.gdal', input = i+"_patch_AreaHA", out = i+"_patch_AreaHA.tif", overwrite = True)
    # If export_pid == True, the patch ID map is exported in this folder
    if export_pid == True and dirout != '':
      os.chdir(dirout)
      grass.run_command('g.region', rast = i+"_pid")
      grass.run_command('r.out.gdal', input = i+"_pid", out = i+"_pid.tif", overwrite = True)
          
    # If calc_statistics == True, the stats of this metric are calculated and exported
    if calc_statistics:
      createtxt(i+"_pid", dirout, i+"_patch_AreaHA")
    
    # If remove_trash == True, the intermediate maps created in the calculation of patch size are removed
    if remove_trash:
      # Define list of maps
      if zero:
        txts = [i+"_patch_clump", i+"_patch_clump_hab", i+"_patch_AreaHA_aux"]
      else:
        txts = [i+"_patch_clump", i+"_patch_clump_hab"]
      # Remove maps from GRASS GIS location
      for txt in txts:
        grass.run_command('g.remove', type="raster", name=txt, flags='f')
    
    # Update counter of the map number    
    cont += 1
        
  # If prepare_biodim == True, use the list of output map names to create a text file and export it
  if prepare_biodim:
    create_TXTinputBIODIM(lista_maps_pid, dirout, "simulados_HABMAT_grassclump_PID")
    create_TXTinputBIODIM(lista_maps_area, dirout, "simulados_HABMAT_grassclump_AREApix")  # Review these names later on!!
    
  # Return a list of maps of Patch ID and Patch area
  return lista_maps_pid, lista_maps_area


#-------------------------------
# Function fragment_area
def fragment_area(input_maps, list_edge_depths,
                  zero = False, diagonal = False,
                  struct_connec = False, patch_size_map_names = [],
                  prepare_biodim = False, calc_statistics = False, remove_trash = True,
                  prefix = '', add_counter_name = False, export = False, export_fid = False, dirout = ''):
  # check that - other parameters used list_meco, check_func_edge,
  """
  Function fragment_area
  
  This function fragments habitat patches (FRAG), excluding corridors and edges,
  given input habitat maps and scales that correspond to edge depths. The habitatcorridors 
  that are excluded from habitat patch to habitat fragment maps have a width corresponding to 
  two the edge depth passed as input.
  
  Input:
  input_maps: list with strings; a python list with maps loaded in the GRASS GIS location. Must be binary class maps (e.g. maps of habitat-non habitat).
  list_edge_depths: list with numbers; each value correpond to a edge depth; the function excludes corridors with width = 2*(edge depth) to calculate fragment size.
  zero: (True/False) logical; if True, non-habitat values are set to zero; otherwise, they are set as null values.
  diagonal: (True/False) logical; if True, cells are clumped also in the diagonal for estimating patch size.
  struct_connec: (True/False) logical; if True, a structural connectivity map is also calculated. In this case, a (list of) map(s) of pactch size must be also provided.
  patch_size_map_names: list with strings; a python list with the names of the patch size maps created using the function patch_size, corresponding to the patch size maps to be used to calculate structural connectivity maps.
  prepare_biodim: (True/False) logical; if True, maps and input text files for running BioDIM package are prepared.
  calc_statistics: (True/False) logical; if True, statistics are calculated and saved as an output text file.
  remove_trash: (True/False) logical; if True, maps generated in the middle of the calculation are deleted; otherwise they are kept within GRASS.
  prefix: string; a prefix to be appended in the beginning of the output map names.
  add_counter_name: (True/False) logical; if True, a number is attached to the beginning of each outputmap name, in the order of the input, following 0001, 0002, 0003 ...
  export: (True/False) logical; if True, the maps are exported from GRASS.
  export_fid: (True/False) logical; if True, the fragment ID (fid) maps are exported from GRASS.
  dirout: string; folder where the output maps will be saved when exported from GRASS. If '', the output maps are generated but are not exported from GRASS.
  
  Output:
  Maps with Fragment ID and Area in hectares of each fragment (considering non-habitat as 0 if zero == True or null if zero == False).
  Fragments are equal to habitat patches but exclude corridors and branches with width equals 2*(edge depth).
  If prepare_biodim == True, a file with fragment size maps to run BioDIM is generated.
  If calc_statistics == True, a file with area per fragment in hectares is generated.
  """

  # If we ask to export something but we do not provide an output folder, it shows a warning
  if (export or prepare_biodim or calc_statistics) and dirout == '':
    warnings.warn("You are trying to export files from GRASS but we did not set an output folder.")
    
  if (struct_connec and (len(patch_size_map_names) == 0 or len(patch_size_map_names) != len(input_maps))):
    raise Warning('A list of names of patch size maps must be provided, and its length must be equal to number of input maps.')

  # If prepare_biodim == True, lists of map names of Fragment ID and area are initialized
  # Theses lists here are matrices with input maps in rows and edge depths in columns
  if prepare_biodim:
    lista_maps_fid = np.empty((len(input_maps), len(list_edge_depths)), dtype=np.dtype('a200'))
    lista_maps_farea = np.empty((len(input_maps), len(list_edge_depths)), dtype=np.dtype('a200'))
  
  # Initialize counter of map name for lists of map names
  z = 0 
  
  # Initialize counter, in case the user wants to add a number to the map name
  cont = 1
  list_ssbc_maps=[] ###################
  
  # For each map in the list of input maps
  for i_in in input_maps:
    
    # Putting (or not) a prefix in the beginning of the output map name
    if not add_counter_name:
      pre_numb = ''
    else: # adding numbers in case of multiple maps
      pre_numb = '00000'+`cont`+'_'
      pre_numb = pre_numb[-5:]
      
    # Prefix of the output
    i = prefix+pre_numb+i_in
    
    # Define the region      
    grass.run_command('g.region', rast=i_in)
    
    # Calculate edge depths and corridor widths to be subtracted from connections between patches
    edge_depths, list_corridor_width_pixels = frag_scales(i_in, list_edge_depths)
    
    # Initialize counter of edge depth value for lists of map names
    x = 0
    
    lista_maps_CSSB=[] ################

    # For each value in the list of corridor widths
    for a in list_corridor_width_pixels:
      meters = int(edge_depths[x]) # should we use the input list_edge_depths instead? only list_edge_depths[x]
      
      # Prefix for map names regarding scale
      format_escale_name = '0000'+`meters`
      format_escale_name = format_escale_name[-4:]
      
      # Uses a moving window to erodes habitat patches, by considering the minimum value within a window
      grass.run_command('r.neighbors', input = i_in, output = i+"_ero_"+format_escale_name+'m', method = 'minimum', size = a, overwrite = True)#, flags = 'c')
      
      # This is followed by dilatating the patches again (but not the corridors), by considering the maximum value within a moving window
      grass.run_command('r.neighbors', input=i+"_ero_"+format_escale_name+'m', output = i+"_dila_"+format_escale_name+'m', method = 'maximum', size = a, overwrite = True)#, flags = 'c')
      
      # Taking only positive values
      expression1 = i+"_FRAG_"+format_escale_name+"m_pos = if("+i+"_dila_"+format_escale_name+'m'+" > 0, "+i+"_dila_"+format_escale_name+'m'+", null())"
      grass.mapcalc(expression1, overwrite = True, quiet = True)
      expression2 = i+"_FRAG_"+format_escale_name+"m_pos_habitat = if("+i_in+" >= 0, "+i+"_FRAG_"+format_escale_name+"m_pos, null())"
      grass.mapcalc(expression2, overwrite = True, quiet = True)
      
      # Clump pixels that are contiguous in the same fragment ID
      if diagonal: # whether or not to clump pixels considering diagonals
        grass.run_command('r.clump', input = i+"_FRAG_"+format_escale_name+"m_pos_habitat", output = i+"_"+format_escale_name+"m_fid", overwrite = True, flags = 'd')
      else:
        grass.run_command('r.clump', input = i+"_FRAG_"+format_escale_name+"m_pos_habitat", output = i+"_"+format_escale_name+"m_fid", overwrite = True)      
      
      # Reclass pixel id values by calculating the area in hectares
        
      if dirout != '':
        os.chdir(dirout) # folder to save temp reclass file
      # Define region
      grass.run_command('g.region', rast = i+"_"+format_escale_name+"m_fid")
      
      # If zero == False (non-habitat cells are considered null)
      if zero == False:      
        nametxtreclass = rulesreclass(i+"_"+format_escale_name+"m_fid", outputfolder = '.')
        grass.run_command('r.reclass', input = i+"_"+format_escale_name+"m_fid", output = i+"_"+format_escale_name+"m_fragment_AreaHA", rules=nametxtreclass, overwrite = True)   
        os.remove(nametxtreclass)
      else: # If zero == True (non-habitat cells are considered as zeros)
        nametxtreclass = rulesreclass(i+"_"+format_escale_name+"m_fid", outputfolder = '.')
        grass.run_command('r.reclass', input = i+"_"+format_escale_name+"m_fid", output = i+"_"+format_escale_name+"m_fragment_AreaHA_aux", rules=nametxtreclass, overwrite = True)   
        os.remove(nametxtreclass)
        
        # Transforms what is 1 in the binary map into the patch size
        expression3 = i+'_'+format_escale_name+'m_fragment_AreaHA = if('+i_in+' == 0, 0, '+i+'_'+format_escale_name+'m_fragment_AreaHA_aux)'
        grass.mapcalc(expression3, overwrite = True)          
      
      ## identificando branch tampulins e corredores
      #expression3='temp_BSSC=if(isnull('+i+"_FRAG"+format_escale_name+"m_mata_clump_AreaHA"+'),'+i_in+')'
      #grass.mapcalc(expression3, overwrite = True, quiet = True)    
      
      #expression1="MapaBinario=temp_BSSC"
      #grass.mapcalc(expression1, overwrite = True, quiet = True)    
      #grass.run_command('g.region',rast="MapaBinario")
      #expression2="A=MapaBinario"
      #grass.mapcalc(expression2, overwrite = True, quiet = True)
      #grass.run_command('g.region',rast="MapaBinario")
      #expression3="MapaBinario_A=if(A[0,0]==0 && A[0,-1]==1 && A[1,-1]==0 && A[1,0]==1,1,A)"
      #grass.mapcalc(expression3, overwrite = True, quiet = True)
      #expression4="A=MapaBinario_A"
      #grass.mapcalc(expression4, overwrite = True, quiet = True)
      #expression5="MapaBinario_AB=if(A[0,0]==0 && A[-1,0]==1 && A[-1,1]==0 && A[0,1]==1,1,A)"
      #grass.mapcalc(expression5, overwrite = True, quiet = True) 
      #expression6="A=MapaBinario_AB"
      #grass.mapcalc(expression6, overwrite = True, quiet = True)
      #expression7="MapaBinario_ABC=if(A[0,0]==0 && A[0,1]==1 && A[1,1]==0 && A[1,0]==1,1,A)"
      #grass.mapcalc(expression7, overwrite = True, quiet = True)
      #expression8="A=MapaBinario_ABC"
      #grass.mapcalc(expression8, overwrite = True, quiet = True)
      #expression9="MapaBinario_ABCD=if(A[0,0]==0 && A[1,0]==1 && A[1,1]==0 && A[0,1]==1,1,A)"
      #grass.mapcalc(expression9, overwrite = True, quiet = True)
      
      #expression4='MapaBinario_ABCD1=if(MapaBinario_ABCD==0,null(),1)'
      #grass.mapcalc(expression4, overwrite = True, quiet = True)    
      #grass.run_command('r.clump', input='MapaBinario_ABCD1', output="MapaBinario_ABCD1_pid", overwrite = True)
      
      #grass.run_command('r.neighbors', input='MapaBinario_ABCD1_pid', output='MapaBinario_ABCD1_pid_mode', method='mode', size=3, overwrite = True)
      #grass.run_command('r.cross', input=i+"_FRAG"+format_escale_name+'m_mata_clump_pid,MapaBinario_ABCD1_pid_mode',out=i+"_FRAG"+format_escale_name+'m_mata_clump_pid_cross_corredor',overwrite = True)
      #cross_TB = grass.read_command('r.stats', input=i+"_FRAG"+format_escale_name+'m_mata_clump_pid_cross_corredor', flags='l')  # pegando a resolucao
      #print cross_TB 
      #txt=open("table_cross.txt",'w')
      #txt.write(cross_TB)
      #txt.close()
      
      #reclass_frag_cor('MapaBinario_ABCD1_pid', dirout) 
      #expression10='MapaBinario_ABCD1_pid_reclass_sttepings=if(isnull(MapaBinario_ABCD1_pid_reclass)&&temp_BSSC==1,3,MapaBinario_ABCD1_pid_reclass)'
      #grass.mapcalc(expression10, overwrite = True, quiet = True)  
      
      #outputmapSCB=i_in+'_SSCB_deph_'+format_escale_name
      #expression11=outputmapSCB+'=if(temp_BSSC==1,MapaBinario_ABCD1_pid_reclass_sttepings,null())'
      #grass.mapcalc(expression11, overwrite = True, quiet = True) 
      #list_ssbc_maps.append(outputmapSCB)
      
      # If prepare_biodim == True, the list of map names is updated
      if prepare_biodim:
        lista_maps_fid[z,x] = i+"_"+format_escale_name+"m_fid"
        lista_maps_farea[z,x] = i+'_'+format_escale_name+'m_fragment_AreaHA'

      # If export == True and dirout == '', the map is not exported; in other cases, the map is exported in this folder
      if export == True and dirout != '':
        os.chdir(dirout)
        grass.run_command('g.region', rast = i+'_'+format_escale_name+'m_fragment_AreaHA')
        grass.run_command('r.out.gdal', input = i+'_'+format_escale_name+'m_fragment_AreaHA', out = i+'_'+format_escale_name+'m_fragment_AreaHA.tif', overwrite = True)
      # If export_fid == True, the fragment ID map is exported in this folder
      if export_fid == True and dirout != '':
        os.chdir(dirout)
        grass.run_command('g.region', rast = i+"_"+format_escale_name+"m_fid")
        grass.run_command('r.out.gdal', input = i+"_"+format_escale_name+"m_fid", out = i+"_"+format_escale_name+'m_fid.tif', overwrite = True)
      
      # If calc_statistics == True, the stats of this metric are calculated and exported
      if calc_statistics:      
        createtxt(i+"_"+format_escale_name+"m_fid", dirout, i+'_'+format_escale_name+'m_fragment_AreaHA')      
      
      # If remove_trash == True, the intermediate maps created in the calculation of patch size are removed
      if remove_trash:
        # Define list of maps
        if zero:
          txts = [i+"_ero_"+format_escale_name+'m', i+"_dila_"+format_escale_name+'m', i+"_FRAG_"+format_escale_name+"m_pos", i+"_FRAG_"+format_escale_name+"m_pos_habitat", i+'_'+format_escale_name+'m_fragment_AreaHA_aux', 'MapaBinario_ABCD1_pid','MapaBinario_ABCD1_pid_reclass','MapaBinario_ABCD1_pid_reclass_sttepings2', 'temp_BSSC','MapaBinario','A','MapaBinario_A','MapaBinario_AB','MapaBinario_ABC','MapaBinario_ABCD','MapaBinario_ABCD1','MapaBinario_ABCD1_pid','MapaBinario_ABCD1_pid_mode', i+'_FRAG'+`meters`+'m_mata_clump_pid_cross_corredor','MapaBinario_ABCD1_pid_reclass_sttepings']
        else:        
          txts = [i+"_ero_"+format_escale_name+'m', i+"_dila_"+format_escale_name+'m', i+"_FRAG_"+format_escale_name+"m_pos", i+"_FRAG_"+format_escale_name+"m_pos_habitat", 'MapaBinario_ABCD1_pid','MapaBinario_ABCD1_pid_reclass','MapaBinario_ABCD1_pid_reclass_sttepings2', 'temp_BSSC','MapaBinario','A','MapaBinario_A','MapaBinario_AB','MapaBinario_ABC','MapaBinario_ABCD','MapaBinario_ABCD1','MapaBinario_ABCD1_pid','MapaBinario_ABCD1_pid_mode',i+"_FRAG"+`meters`+'m_mata_clump_pid_cross_corredor','MapaBinario_ABCD1_pid_reclass_sttepings']
        # Remove maps from GRASS GIS location        
        for txt in txts:
          grass.run_command('g.remove', type="raster", name=txt, flags='f')
          
      # Update counter columns (edge depths)
      x = x + 1
    
    # Update counter rows (map names)
    z = z + 1
    
    # Update counter for map names
    cont += 1
 
  #if check_func_edge:
    #cont=0
    #for i in list_ssbc_maps:
      
      #meters=int(listmeters[cont])  # lista de escalas em metros
      #format_escale_name='0000'+`meters`
      #format_escale_name=format_escale_name[-4:]   
      #nameaux=i[0:len(input_maps)]
      #outputname=nameaux+'_SSCCB_deph_'+format_escale_name
      #inpmaps=i+','+list_meco[cont]
      
      
      #grass.run_command('r.patch',input=inpmaps,out=outputname,overwrite = True)
      #cont+=1
      
  # If prepare_biodim == True, use the list of output map names to create a text file and export it, for each scale
  if prepare_biodim:
    # For each value in the list of edge depths
    for i in range(len(list_edge_depths)):
      # Create a text file as BioDIM input
      mm = int(list_edge_depths[i])
      create_TXTinputBIODIM(lista_maps_fid[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_FRAC_"+`mm`+"m_PID")
      create_TXTinputBIODIM(lista_maps_farea[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_FRAC_"+`mm`+"m_AREApix")              


#-------------------------------
# Function percentage
def percentage(input_maps, scale_list, method = 'average', append_name = '',
               remove_trash = True, export = False, dirout = ''):
  '''
  Function percentage
  
  This function calculates the percentage of a certain variable using a neighborhood analysis.
  Given a list of window sizes, a moving window is applied to the binary input maps and the percentage
  of the variable around the focal pixel is calculated.
  
  Input:
  input_maps: list with strings; each input map corresponds to a binary map (1/0 and NOT 1/null!!) that represents a certain variable.
  scale_list: list with numbers (float or integer); each value correponds to a size for the moving window, in meters, in which the percentage will be calculated.
  method: string; the method calculation performed inside the moving window. For percentages in general the method 'average' is used (stardard), but ir may be set to other values depending on the kind of input variable.
  append_name: name to be appended in the output map name. It may be used to distinguish between edge, core, and habitat percentage, for example.
  remove_trash: (True/False) logical; if True, maps generated in the middle of the calculation are deleted; otherwise they are kept within GRASS.
  export: (True/False) logical; if True, the maps are exported from GRASS.
  dirout: string; folder where the output maps will be saved when exported from GRASS. If '', the output maps are generated but are not exported from GRASS.
               
  Output:
  A map in which each pixel is the percentage of the input variable in a window around it. The size of the window
  is given by the scale provided as input.
  '''
  
  #calc_statistics = False for landscape level?, 
  
  # If we ask to export something but we do not provide an output folder, it shows a warning
  if export and dirout == '':
    warnings.warn("You are trying to export files from GRASS but we did not set an output folder.")  
  
  # For each map in the input list
  for in_map in input_maps: 
    
    # For each scale in the scale list
    for i in scale_list:
    
      # Transform the scale into an integer
      scale = int(i)
      
      # Defines the output name
      # The variable append_name is used to define different percentages, such as habitat, edge, or core percentage
      outputname = in_map+append_name+"_pct_"+str(scale)+"m"
      
      # Define the window size in pixels
      windowsize = get_size_pixels(input_map = in_map, scale_in_meters = scale)
      
      # Define the region
      grass.run_command('g.region', rast = in_map)
      
      # Calculate average value based on the average value (or other method of r.neighbors) of moving window
      grass.run_command('r.neighbors', input = in_map, output = "temp_PCT", method = method, size = windowsize, overwrite = True)
      
      # Multiplying by 100 to get a value between 0 and 100%
      expression1 = outputname+' = temp_PCT * 100'
      grass.mapcalc(expression1, overwrite = True, quiet = True)
      
      # If export == True, export the rsulting map
      if export == True and dirout != '':
        os.chdir(dirout)      
        grass.run_command('r.out.gdal', input = outputname, out = outputname+'.tif', overwrite = True)
        
      # If remove_trash == True, remove the maps generated in the process
      if remove_trash:
        grass.run_command('g.remove', type = "raster", name = 'temp_PCT', flags='f')


#-------------------------------
# Function functional_connectivity
def functional_connectivity(input_maps, list_gap_crossing,
                            zero = False, diagonal = False,
                            functional_connec = False,
                            functional_area_complete = False,
                            prepare_biodim = False, calc_statistics = False, remove_trash = True,
                            prefix = '', add_counter_name = False, export = False, export_pid = False, dirout = ''):  
  """
  Function functional_connectivity
  
  This function used input maps and values of gaps an organism can cross to calculate maps of functional
  connected area, complete functional connected area (if functional_area_complete == True), 
  and functional connectivity (if functional_connec == True). All values are in hectares,
  given the projection uses meters. The default is to calculate only functionally connected area maps.
  - Funtional connected area: each habitat pixel presents a value equals to the sum of all area of all patches
  functionally connected to it.
  - Complete funtional connected area: each habitat pixel presents a value equals to the sum of all area of all patches
  functionally connected to it, plus the surrounding distance in the matrix, defined by the gap crossing distance.
  - Functional connecitivity: each habitat pixel presents a value equals to the sum of all area of all patches
  functionally connected to it, minus the size of the habitat patch it is part of.
  It is the same as the map of functional area minus the map of patch size.
  
  Input:
  input_maps: list with strings; a python list with maps loaded in the GRASS GIS location. Must be binary class maps (e.g. maps of habitat-non habitat).
  list_gap_crossing: list with numbers; each value correpond to a distance an organism can cross in the matrix; all habitat patches whose distance is <= this gap crossing distance are considered functionally connected.
  zero: (True/False) logical; if True, non-habitat values are set to zero; otherwise, they are set as null values.
  diagonal: (not used yet) (True/False) logical; if True, cells are clumped also in the diagonal for estimating patch size.
  functional_connec: (True/False) logical; if True, the functional connectivity map is calculated. If gap crossing == 0 is not present in the list of gap crossings, it is added to generate these functional connectivity maps
  functional_area_complete: (True/False) logical; if True, maps of complete functional connectivity area are also generated.
  prepare_biodim: (True/False) logical; if True, maps and input text files for running BioDIM package are prepared.
  calc_statistics: (True/False) logical; if True, statistics are calculated and saved as an output text file.
  remove_trash: (True/False) logical; if True, maps generated in the middle of the calculation are deleted; otherwise they are kept within GRASS.
  prefix: string; a prefix to be appended in the beginning of the output map names.
  add_counter_name: (True/False) logical; if True, a number is attached to the beginning of each outputmap name, in the order of the input, following 0001, 0002, 0003 ...
  export: (True/False) logical; if True, the maps are exported from GRASS.
  export_pid: (True/False) logical; if True, the fragment ID (fid) maps are exported from GRASS.
  dirout: string; folder where the output maps will be saved when exported from GRASS. If '', the output maps are generated but are not exported from GRASS.

  Output:
  For default, only functionally connected area maps are calculated. If functional_connec == True, functional connectivity
  maps are also calculated. If functional_area_complete, maps of complete functionally connected area are also calculated.
  If prepare_biodim == True, a file with fragment size maps to run BioDIM is generated.
  If calc_statistics == True, a file with area per fragment in hectares is generated.
  """  
  
  # If we ask to export something but we do not provide an output folder, it shows a warning
  if (export or prepare_biodim or calc_statistics) and dirout == '':
    warnings.warn("You are trying to export files from GRASS but we did not set an output folder.")
  
  # If we want to calculate functional connectivity, we need a map for gap crossing = 0
  # Check if 0 is in the the list; if not or if it is but not in the beginning, add it to the beginning
  list_gap_cross = [float(i) for i in list_gap_crossing] # making sure values are float
  if functional_connec:
    if 0 in list_gap_cross and list_gap_cross[0] != 0:
      list_gap_cross.remove(0)
      list_gap_cross.insert(0, 0)
    elif not (0 in list_gap_cross):
      list_gap_cross.insert(0, 0)
  
  # If prepare_biodim == True, lists of map names of Fragment ID and area are initialized
  # Theses lists here are matrices with input maps in rows and edge depths in columns  
  if prepare_biodim:
    # Functional connected area (clean) maps are always saved
    lista_maps_pid_clean = np.empty((len(input_maps), len(list_gap_cross)), dtype=np.dtype('a200'))
    lista_maps_area_clean = np.empty((len(input_maps), len(list_gap_cross)), dtype=np.dtype('a200'))
    
    # If functional_area_complete == True, these maps are also saved as BioDIM input
    if functional_area_complete:
      lista_maps_pid_comp = np.empty((len(input_maps), len(list_gap_cross)), dtype=np.dtype('a200'))
      lista_maps_area_comp = np.empty((len(input_maps), len(list_gap_cross)), dtype=np.dtype('a200'))      
  
  # Initialize counter of map name for lists of map names
  z = 0
  
  # Initialize counter, in case the user wants to add a number to the map name
  cont = 1
  
  # For each map in the list of input maps
  for i_in in input_maps:
    
    # Putting (or not) a prefix in the beginning of the output map name
    if not add_counter_name:
      pre_numb = ''
    else: # adding numbers in case of multiple maps
      pre_numb = '00000'+`cont`+'_'
      pre_numb = pre_numb[-5:]
      
    # Prefix of the output
    i = prefix+pre_numb+i_in
    
    # Define the region
    grass.run_command('g.region', rast = i_in)
    
    # Calculate gap crossing distances in number of pixels, based on input values in meters
    list_dilatate_meters, list_dilatate_pixels = connectivity_scales(input_map = i_in, list_gap_crossing = list_gap_cross)
    
    # Initialize counter of gap crossing value for lists of map names
    x = 0
    
    # For each value in the list of gap crossing distances
    for a in list_dilatate_pixels:
      
      meters = int(2*list_dilatate_meters[x])  # should we use the input list_gap_cross instead? only list_gap_cross[x]  
      
      # Prefix for map names regarding scale
      format_escale_name = '0000'+`meters`
      format_escale_name = format_escale_name[-4:]
        
      # Uses a moving window to dilatate/enlarge habitat patches, by considering the maximum value within a window
      grass.run_command('r.neighbors', input = i_in, output = i+"_dila_"+format_escale_name+'m_orig', method = 'maximum', size = a, overwrite = True)
      
      # Set zero values as null
      expression1 = i+"_dila_"+format_escale_name+'m_orig_temp = if('+i+"_dila_"+format_escale_name+'m_orig == 0, null(), '+i+"_dila_"+format_escale_name+'m_orig)'
      grass.mapcalc(expression1, overwrite = True, quiet = True)
      
      # Clump pixels that are contiguous in the same functionally connected patch ID - the complete PID with matrix pixels
      grass.run_command('r.clump', input = i+"_dila_"+format_escale_name+'m_orig_temp', output = i+"_"+format_escale_name+'m_func_connect_complete_pid', overwrite = True)
      
      # Take only values within the original habitat
      expression2 = i+"_"+format_escale_name+'m_func_connect_complete_pid_habitat = '+i_in+'*'+i+"_"+format_escale_name+'m_func_connect_complete_pid'
      grass.mapcalc(expression2, overwrite = True, quiet = True)
      
      # Transform no habitat values in null() - this is the clean patch ID for functionally connected patches
      expression3 = i+"_"+format_escale_name+'m_func_connect_pid = if('+i+"_"+format_escale_name+'m_func_connect_complete_pid_habitat > 0, '+i+"_"+format_escale_name+'m_func_connect_complete_pid_habitat, null())'
      grass.mapcalc(expression3, overwrite = True, quiet = True)
      
      # Reclass pixel id values by calculating the area in hectares
      if dirout != '':
        os.chdir(dirout) # folder to save temp reclass file
      # Define region
      grass.run_command('g.region', rast = i+"_"+format_escale_name+'m_func_connect_pid')      
      
      # If zero == False (non-habitat cells are considered null)
      if zero == False:        
        nametxtreclass = rulesreclass(i+"_"+format_escale_name+'m_func_connect_pid', outputfolder = '.')
        grass.run_command('r.reclass', input = i+"_"+format_escale_name+'m_func_connect_pid', output = i+"_"+format_escale_name+'m_func_connect_AreaHA', rules = nametxtreclass, overwrite = True)
        os.remove(nametxtreclass)
      else: # If zero == True (non-habitat cells are considered as zeros)
        nametxtreclass = rulesreclass(i+"_"+format_escale_name+'m_func_connect_pid', outputfolder = '.')
        grass.run_command('r.reclass', input = i+"_"+format_escale_name+'m_func_connect_pid', output = i+"_"+format_escale_name+'m_func_connect_AreaHA_aux', rules = nametxtreclass, overwrite = True)
        os.remove(nametxtreclass)
        
        # Transforms what is 1 in the binary map into the patch size
        expression4 = i+"_"+format_escale_name+'m_func_connect_AreaHA = if('+i_in+' == 0, 0, '+i+'_'+format_escale_name+'m_fragment_AreaHA_aux)'
        grass.mapcalc(expression4, overwrite = True)
      
      # Save the name of the functional area map in case the gap crossing == 0:
      if list_gap_cross[x] == 0:
        name_map_gap_crossing_0 = i+"_"+format_escale_name+'m_func_connect_AreaHA'
        
      # If functional_area_complete == True, the area of complete maps (dilatated maps, considering the matrix pixels) is also calculated
      if functional_area_complete and list_gap_cross[x] != 0:
        
        # If zero == False (non-habitat cells are considered null)
        if zero == False:          
          nametxtreclass = rulesreclass(i+"_"+format_escale_name+'m_func_connect_complete_pid', '.')
          grass.run_command('r.reclass', input = i+"_"+format_escale_name+'m_func_connect_complete_pid', output=i+"_"+format_escale_name+'m_func_connect_complete_AreaHA', rules=nametxtreclass, overwrite = True)
          os.remove(nametxtreclass)
        else: # If zero == True (non-habitat cells are considered as zeros)
          nametxtreclass = rulesreclass(i+"_"+format_escale_name+'m_func_connect_complete_pid', '.')
          grass.run_command('r.reclass', input = i+"_"+format_escale_name+'m_func_connect_complete_pid', output=i+"_"+format_escale_name+'m_func_connect_complete_AreaHA_aux', rules=nametxtreclass, overwrite = True)
          os.remove(nametxtreclass)
      
          # Transforms what is 1 in the binary map into the patch size
          expression5 = i+"_"+format_escale_name+'m_func_connect_complete_AreaHA = if('+i_in+' == 0, 0, '+i+"_"+format_escale_name+'m_func_connect_complete_AreaHA_aux)'
          grass.mapcalc(expression5, overwrite = True)      
      
      # If functional_connect == True, calculate map of functional connectivity
      # This map equals functional_area - funcional_area(gap_crossing == 0)
      if functional_connec and list_gap_cross[x] != 0:
        
        # Should we check here or somewhere if the map for gap crossing == 0 was really generated?
        expression6 = i+'_'+format_escale_name+'m_functional_connectivity = '+i+'_'+format_escale_name+'m_func_connect_AreaHA - '+name_map_gap_crossing_0
        grass.mapcalc(expression6, overwrite = True)         
      
      # If prepare_biodim == True, the list of map names is updated
      if prepare_biodim:
        lista_maps_pid_clean[z,x] = i+"_"+format_escale_name+'m_func_connect_pid'
        lista_maps_area_clean[z,x] = i+"_"+format_escale_name+'m_func_connect_AreaHA'        
        
        # If functional_area_complete == True, these maps are also saved as BioDIM input
        if functional_area_complete:
            lista_maps_pid_comp[z,x] = i+"_"+format_escale_name+'m_func_connect_complete_pid'
            lista_maps_area_comp[z,x] = i+"_"+format_escale_name+'m_func_connect_complete_AreaHA'            
  
      # If export == True and dirout == '', the map is not exported; in other cases, the map is exported in this folder
      # For gap crossing == 0, maps are not exported
      if export == True and dirout != '' and list_gap_cross[x] != 0:
        os.chdir(dirout) 
        grass.run_command('g.region', rast = i+"_"+format_escale_name+'m_func_connect_AreaHA')
        grass.run_command('r.out.gdal', input = i+"_"+format_escale_name+'m_func_connect_AreaHA', output = i+"_"+format_escale_name+'m_func_connect_AreaHA.tif', overwrite = True)
        
        # If functional_area_complete == True, these maps are also exported
        if functional_area_complete:        
          grass.run_command('r.out.gdal', input = i+"_"+format_escale_name+'m_func_connect_complete_AreaHA', output = i+"_"+format_escale_name+'m_func_connect_complete_AreaHA.tif', overwrite = True)
          
        # If functional_connec == True, the functional connectivity maps are also exported
        if functional_connec:
          grass.run_command('r.out.gdal', input = i+'_'+format_escale_name+'m_functional_connectivity', output = i+'_'+format_escale_name+'m_functional_connectivity.tif', overwrite = True)
      
      # If export_fid == True, the fragment ID map is exported in this folder
      if export_pid == True and dirout != '':
        os.chdir(dirout)
        grass.run_command('g.region', rast = i+"_"+format_escale_name+'m_func_connect_pid')
        grass.run_command('r.out.gdal', input = i+"_"+format_escale_name+'m_func_connect_pid', output = i+"_"+format_escale_name+'m_func_connect_pid.tif', overwrite = True)
        
        # If functional_area_complete == True, these maps are also exported
        if functional_area_complete and list_gap_cross[x] != 0:        
          grass.run_command('r.out.gdal', input = i+"_"+format_escale_name+'m_func_connect_complete_pid', output = i+"_"+format_escale_name+'m_func_connect_complete_pid.tif', overwrite = True)
            
      # If calc_statistics == True, the stats of this metric are calculated and exported
      if calc_statistics:
        createtxt(i+"_"+format_escale_name+'m_func_connect_pid', outputfolder = dirout, filename = i+"_"+format_escale_name+'m_func_connect_AreaHA')
        # If functional_area_complete == True, these statistics are also calculated
        if functional_area_complete:          
          createtxt(i+"_"+format_escale_name+'m_func_connect_complete_pid', outputfolder = dirout, filename = i+"_"+format_escale_name+'m_func_connect_complete_AreaHA')
      
      # If remove_trash == True, the intermediate maps created in the calculation of patch size are removed
      if remove_trash:
        # Define list of maps
        if functional_area_complete and list_gap_cross[x] != 0:
          txts = [i+"_dila_"+format_escale_name+'m_orig', i+"_dila_"+format_escale_name+'m_orig_temp', i+"_"+format_escale_name+'m_func_connect_complete_pid_habitat']
        else:
          txts = [i+"_dila_"+format_escale_name+'m_orig', i+"_dila_"+format_escale_name+'m_orig_temp', i+"_"+format_escale_name+'m_func_connect_complete_pid', i+"_"+format_escale_name+'m_func_connect_complete_pid_habitat'] #, i+"_"+format_escale_name+'m_func_connect_pid']
        if zero == True:
          txts.append(i+"_"+format_escale_name+'m_func_connect_AreaHA_aux')
          if functional_area_complete and list_gap_cross[x] != 0:
            txts.append(i+"_"+format_escale_name+'m_func_connect_complete_AreaHA_aux')
        # Remove maps from GRASS GIS location     
        for txt in txts:
          grass.run_command('g.remove', type='raster', name=txt, flags='f')
      
      # Update counter columns (gap crossing values)    
      x = x + 1
    
    # Update counter rows (map names)  
    z = z + 1
    
    # Update counter for map names
    cont += 1
    
  # If prepare_biodim == True, use the list of output map names to create a text file and export it, for each scale
  if prepare_biodim:
    # For each value in the list of gap crossing
    for i in range(len(list_gap_cross)):
      # Create a text file as BioDIM input
      mm = int(list_gap_cross[i])
      if mm != 0: # Do not export for gap crossing == 0
        create_TXTinputBIODIM(lista_maps_pid_clean[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_grassclump_dila_"+`mm`+"m_clean_PID")
        create_TXTinputBIODIM(lista_maps_area_clean[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_grassclump_dila_"+`mm`+"m_clean_AREApix")
        # If functional_area_complete == True, these statistics are also calculated
        if functional_area_complete:
          create_TXTinputBIODIM(lista_maps_pid_comp[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_grassclump_dila_"+`mm`+"m_complete_PID")
          create_TXTinputBIODIM(lista_maps_area_comp[:,i].tolist(), outputfolder = dirout, filename = "simulados_HABMAT_grassclump_dila_"+`mm`+"m_complete_AREApix")                      
      
      
#----------------------------------------------------------------------------------
# Metrics for edge area (EDGE)

def mapcalcED(expression):
  """
  
  """
  grass.mapcalc(expression, overwrite = True, quiet = True)        

   
    
def create_EDGE(ListmapsED, escale_ed, dirs, prefix,calc_statistics,remove_trash,escale_pct,checkCalc_PCTedge):
  os.chdir(dirs)
  """
  Function for a series of maps
  This function separates habitat area into edge and interior/core regions, given a scale/distance defined as edge, and:
  - generates and exports maps with each region
  - generatics statistics - Area per region (matrix/edge/core) (if calc_statistics == True)
  """
  
  cont = 1
  list_meco=[] # essa lista sera usada na funcao area frag

  for i_in in ListmapsED:
    
    if prefix == '':
      pre_numb = ''
    else:
      if cont <= 9:
        pre_numb = "000"+`cont`+'_'
      elif cont <= 99:
        pre_numb = "00"+`cont`+'_'
      elif cont <= 999:        
        pre_numb = "0"+`cont`+'_'
      else: 
        pre_numb = `cont`+'_'
    
    i = prefix+pre_numb+i_in
    
    grass.run_command('g.region', rast=i_in)
    listsize, listmeters = escala_frag(i_in, escale_ed)
    
    cont_escale=0
    for size in listsize:
      apoioname = int(listmeters[cont_escale])  
      formatnumber='0000'+`apoioname`
      formatnumber=formatnumber[-4:]
      outputname_meco=i+'_MECO_'+formatnumber+'m' # nome de saida do mapa edge-core-matriz
      outputname_core=i+'_CORE_'+formatnumber+'m' # nome de saida do mapa Core
      outputname_edge=i+'_EDGE_'+formatnumber+'m' # nome de saida do mapa edge
      list_meco.append(outputname_meco)
      
      grass.run_command('r.neighbors', input=i_in, output=i+"_eroED_"+`apoioname`+'m', method='minimum', size=size, overwrite = True)
      inputs=i+"_eroED_"+`apoioname`+'m,'+i_in
      out=i+'_EDGE'+`apoioname`+'m_temp1'
      grass.run_command('r.series', input=inputs, out=out, method='sum', overwrite = True)
      espressaoEd=i+'_EDGE'+`apoioname`+'m_temp2 = int('+i+'_EDGE'+`apoioname`+'m_temp1)' # criando uma mapa inteiro
      mapcalcED(espressaoEd)
           
      
      espressaoclip=i+'_EDGE'+`apoioname`+'m_temp3= if('+i_in+' >= 0, '+i+'_EDGE'+`apoioname`+'m_temp2, null())'
      mapcalcED(espressaoclip)  
      
      espressaoEd=outputname_meco+'=if('+i+'_EDGE'+`apoioname`+'m_temp3==0,0)|if('+i+'_EDGE'+`apoioname`+'m_temp3==1,4)|if('+i+'_EDGE'+`apoioname`+'m_temp3==2,5)'
      mapcalcED(espressaoEd)       
      
      espressaocore=outputname_core+'= if('+i+'_EDGE'+`apoioname`+'m_temp3==2,1,0)'
      grass.mapcalc(espressaocore, overwrite = True, quiet = True)     
      
      espressaoedge=outputname_edge+'= if('+i+'_EDGE'+`apoioname`+'m_temp3==1,1,0)'
      grass.mapcalc(espressaoedge, overwrite = True, quiet = True)  
      
      
       
      grass.run_command('r.out.gdal', input=outputname_meco, out=outputname_meco+'.tif', overwrite = True) 
      grass.run_command('r.out.gdal', input=outputname_edge, out=outputname_edge+'.tif', overwrite = True)
      grass.run_command('r.out.gdal', input=outputname_core, out=outputname_core+'.tif', overwrite = True)
      if len(escale_pct)>0 and checkCalc_PCTedge==True:
        for pct in escale_pct:
          pctint=int(pct)
      
          formatnumber='0000'+`pctint`
          formatnumber=formatnumber[-4:]        
          outputname_edge_pct=outputname_edge+'_PCT_esc_'+formatnumber
          
          size=getsizepx(outputname_edge, pctint)
          grass.run_command('r.neighbors', input=outputname_edge, output="temp_pct", method='average', size=size, overwrite = True)
          espressaoedge=outputname_edge_pct+'=temp_pct*100'
          grass.mapcalc(espressaoedge, overwrite = True, quiet = True)    
          grass.run_command('r.out.gdal', input=outputname_edge_pct, out=outputname_edge_pct+'.tif', overwrite = True)
          grass.run_command('g.remove', type="raster", name='temp_pct', flags='f')     
            
      if calc_statistics:
        createtxt(outputname_meco, i+'_EDGE'+`apoioname`+'m_temp1')
      
      if remove_trash:
        grass.run_command('g.remove', type="raster", name=i+"_eroED_"+`apoioname`+'m,'+i+'_EDGE'+`apoioname`+'m_temp1,'+i+'_EDGE'+`apoioname`+'m_temp2,'+i+'_EDGE'+`apoioname`+'m_temp3', flags="f")
      
      cont_escale +=1
      
    cont += 1
  print list_meco
  return list_meco


#


#----------------------------------------------------------------------------------
# Metrics for distance to edges
    


def dist_edge(Listmapsdist_in, prefix,prepare_biodim, dirout,remove_trash):
  """
  Function for a series of maps
  This function calculates the distance of each pixel to habitat edges, considering
  negative values (inside patches) and positive values (into the matrix). Also:
  - generates and exports maps of distance to edge (DIST)
  """

  if prepare_biodim:
    lista_maps_dist=[]    
  
  cont = 1
  for i_in in Listmapsdist:
    
    if prefix == '':
      pre_numb = ''
    else:
      if cont <= 9:
        pre_numb = "000"+`cont`+'_'
      elif cont <= 99:
        pre_numb = "00"+`cont`+'_'
      elif cont <= 999:        
        pre_numb = "0"+`cont`+'_'
      else: 
        pre_numb = `cont`+'_'

    i = prefix+pre_numb+i_in

    grass.run_command('g.region', rast=i_in)
    expression1=i+'_invert = if('+i_in+' == 0, 1, null())'
    grass.mapcalc(expression1, overwrite = True, quiet = True)
    grass.run_command('r.grow.distance', input=i+'_invert', distance=i+'_invert_forest_neg_eucldist',overwrite = True)
    expression2=i+'_invert_matrix = if('+i_in+' == 0, null(), 1)'
    grass.mapcalc(expression2, overwrite = True, quiet = True)
    grass.run_command('r.grow.distance', input=i+'_invert_matrix', distance=i+'_invert_matrix_pos_eucldist',overwrite = True)
    expression3=i+'_dist = '+i+'_invert_matrix_pos_eucldist-'+i+'_invert_forest_neg_eucldist'
    grass.mapcalc(expression3, overwrite = True, quiet = True)
    
    if prepare_biodim:
      lista_maps_dist.append(i+'_dist')
    else:
      grass.run_command('r.out.gdal', input=i+'_dist', out=i+'_DIST.tif', overwrite = True)
      
    if remove_trash:
      txts = [i+'_invert', i+'_invert_forest_neg_eucldist', i+'_invert_matrix', i+'_invert_matrix_pos_eucldist']
      for txt in txts:
        grass.run_command('g.remove', type="raster", name=txt, flags='f')
    
    cont += 1
    
  if prepare_biodim:
    create_TXTinputBIODIM(lista_maps_dist, dirout, "simulados_HABMAT_DIST")
    
#----------------------------------------------------------------------------------


#----------------------------------------------------------------------------------
#def para diversidade de shannon

def createUiqueList(tab_fid00_arry_subset_list,dim):
    tab_fid00_arry_subset_list_apoio=[]
    for i in xrange(dim):
        temp1=tab_fid00_arry_subset_list[i][:]
        for j in temp1:
            if j != -9999 :
                tab_fid00_arry_subset_list_apoio.append(j)
    return tab_fid00_arry_subset_list_apoio
      
      


def Shannon(st):
    st = st
    stList = list(st)
    alphabet = list(Set(st)) # list of symbols in the string
    
    # calculate the frequency of each symbol in the string
    freqList = []
    for symbol in alphabet:
        ctr = 0
        for sym in stList:
            if sym == symbol:
                ctr += 1
        freqList.append(float(ctr) / len(stList))
    
    # Shannon entropy
    ent = 0.0
    for freq in freqList:
        ent = ent + freq * math.log(freq, 2)
    ent = -ent
    
    #print int(math.ceil(ent))
    return ent


    
def removeBlancsapce(ls):
    ls2=[]
    for i in ls:
        if i != "":
            ls2.append(i)
            
    return ls2

def setNodata(arry,nrow,ncol,nodata):
    for i in xrange(nrow):
        for j in xrange(ncol):
            arry[i][j]=nodata
    return arry

#----------------------------------------------------------------------------------
def shannon_diversity(landuse_map,dirout,Raio_Analise):
  for raio in Raio_Analise:
    raio_int=int(raio)
    os.chdir(dirout) #
    grass.run_command('g.region',rast=landuse_map)
    grass.run_command('r.out.ascii',input=landuse_map,output='landuse_map.asc',null_value=-9999,flags='h')
    landusemap_arry=np.loadtxt('landuse_map.asc')
    NRows,Ncols=landusemap_arry.shape
    region_info = grass.parse_command('g.region', rast=landuse_map, flags='m')  # pegando a resolucao    
    cell_size = float(region_info['ewres'])    
    north=float(region_info['n'])
    south=float(region_info['s'])
    east=float(region_info['e'])
    west=float(region_info['w'])
    rows=int(region_info['rows'])
    cols=int(region_info['cols'])
    
    Nodata=-9999
    
    JanelaLinha=(raio_int/cell_size)
    
    new_array = np.zeros(shape=(NRows,Ncols))
    new_array=setNodata(new_array,NRows,Ncols,Nodata)  
    
    JanelaLinha= int(JanelaLinha)
    #
    for i in xrange(JanelaLinha,NRows-JanelaLinha):
      for j in xrange(JanelaLinha,Ncols-JanelaLinha):
        landusemap_arry_subset=landusemap_arry[i-JanelaLinha:i+JanelaLinha,j-JanelaLinha:j+JanelaLinha]    
        landusemap_arry_subset_list=landusemap_arry_subset.tolist()
        landusemap_arry_subset_list=createUiqueList(landusemap_arry_subset_list,len(landusemap_arry_subset_list))
        landusemap_arry_subset_list=map(str,landusemap_arry_subset_list)
        new_array[i][j]=round(Shannon(landusemap_arry_subset_list),6)   

    txt=open("landuse_map_shannon.asc",'w')
    
    L_parameters_Info_asc=['north: ',`north`+'\nsouth: ',`south`+'\neast: ',`east`+'\nwest: ',`west`+'\nrows: ',`rows`+'\ncols: '+`cols`+'\n']
    
    check_ultm=1 # variavel que vai saber se e o ultimo
    for i in L_parameters_Info_asc:
        if check_ultm==len(L_parameters_Info_asc):
            txt.write(i)    
        else:
            txt.write(i+' ')  
        check_ultm=check_ultm+1 
        
    for i in range(NRows):
        for j in range(Ncols):
            txt.write(str(new_array[i][j])+' ')
        
        txt.write('\n')
    
    txt.close()  
    grass.run_command('r.in.ascii',input="landuse_map_shannon.asc",output=landuse_map+"_Shanno_Div_Esc_"+`raio_int`,overwrite=True,null_value=-9999)
    grass.run_command('r.colors',map=landuse_map+"_Shanno_Div_Esc_"+`raio_int`,color='differences')
    os.remove('landuse_map_shannon.asc')
    os.remove('landuse_map.asc')
    


#----------------------------------------------------------------------------------
def lsmetrics_run(input_maps,
                  outputdir = '', output_prefix = '', add_counter_name = False,
                  zero_bin = True, zero_metrics = False, use_calculated_bin = False,
                  calcstats = False, prepare_biodim = False, remove_trash = True, 
                  binary = False, list_habitat_classes = [], export_binary = False,
                  calc_patch_size = False, diagonal = False, export_patch_size = False, export_patch_id = False,
                  calc_frag_size = False, list_edge_depth_frag = [], export_frag_size = False, export_frag_id = False,
                  struct_connec = False, export_struct_connec = False,
                  percentage_habitat = False, list_window_size_habitat = [], method_percentage = 'average', export_percentage_habitat = False,
                  functional_connected_area = False, list_gap_crossing = [], export_func_con_area = False, export_func_con_pid = False,
                  functional_area_complete = False, functional_connectivity_map = False,
                  classify_edge = False,
                  edge_dist = False):
  
  # Transform maps into binary class maps
  if binary:
                
    bin_map_list = create_binary(input_maps, list_habitat_classes, zero = zero_bin, 
                                 prepare_biodim = prepare_biodim, calc_statistics = calcstats, 
                                 prefix = output_prefix, add_counter_name = add_counter_name,
                                 export = export_binary, dirout = outputdir)

  # If binary maps were created and the user wants these maps to be used to calculate metric,
  # then the list is considered as these binary maps; otherwise, the input list of maps is considered
  if binary and use_calculated_bin:
    list_maps_metrics = bin_map_list
    output_prefix = '' # If using this maps, do not repeat the output prefix
    add_counter_name = False # If using this maps, do not add new numbers
  else:
    list_maps_metrics = input_maps
  
  # Metrics of structural connectivity
    
  # Patch size
  if calc_patch_size:
    
    list_patch_size_pid, list_patch_size_area = patch_size(input_maps = list_maps_metrics,
                                                           zero = zero_metrics, diagonal = diagonal, 
                                                           prepare_biodim = prepare_biodim, calc_statistics = calcstats, remove_trash = remove_trash,
                                                           prefix = output_prefix, add_counter_name = add_counter_name,
                                                           export = export_patch_size, export_pid = export_patch_id, dirout = outputdir)
  
  # Fragment size
  if calc_frag_size:
    
    # Checking whether patch size was calculated
    if calc_patch_size == False and struc_connec:
      raise Exeption('To calculate structural connectivity, you need to also calculate patch size.')
    
    fragment_area(input_maps = list_maps_metrics, list_edge_depths = list_edge_depth_frag,
                  zero = zero_metrics, diagonal = diagonal,
                  struct_connec = struct_connec, patch_size_map_names = list_patch_size_area,
                  prepare_biodim = prepare_biodim, calc_statistics = calcstats, remove_trash = remove_trash,
                  prefix = output_prefix, add_counter_name = add_counter_name, 
                  export = export_frag_size, export_fid = export_frag_id, dirout = outputdir)
  
  # Percentage of habitat
  if percentage_habitat:
    
    if zero_bin == False:
      raise Warning('You set the binary map to value 1-null and asked for a percentage of habitat map; this may cause problems in the output!')
    
    percentage(input_maps = list_maps_metrics, scale_list = list_window_size_habitat, method = method_percentage, append_name = '_habitat',
               remove_trash = remove_trash, export = export_percentage_habitat, dirout = outputdir)
    
  # Metrics of functional connectivity
  
  # Functional connected area, functional complete connected area, and functional connectivity
  if functional_connected_area or functional_connectivity_map:
    
    functional_connectivity(input_maps = list_maps_metrics, list_gap_crossing = list_gap_crossing,
                            zero = zero_metrics, diagonal = diagonal,
                            functional_connec = functional_connectivity_map,
                            functional_area_complete = functional_area_complete,
                            prepare_biodim = prepare_biodim, calc_statistics = calcstats, remove_trash = remove_trash,
                            prefix = output_prefix, add_counter_name = add_counter_name, 
                            export = export_func_con_area, export_pid = export_func_con_pid, dirout = outputdir)  
  
  
    ## Calculates core-edge        
    #if classify_edge:
              
      #create_EDGE_single(input_map, output_prefix2, outputdir, escala_ED, 
                         #calcstats, remove_trash, list_esc_pct)
    
    ## Calculates edge distance         
    #if edge_dist:
      
      #dist_edge_Single(self.input_map,self.output_prefix2, self.prepare_biodim, self.dirout, self.remove_trash)
              
    #if self.checPCT==True:
      
      #PCTs_single(self.input_map, self.list_esc_pct)
    
    #if self.check_diversity==True:

      #shannon_diversity(self.input_map, self.dirout, self.analise_rayos)





#----------------------------------------------------------------------------------
# LSMetrics is the main class, in which the software is initialized and runs

class LSMetrics(wx.Panel):
    def __init__(self, parent, id):
        
        # Initializing GUI
        wx.Panel.__init__(self, parent, id)
        
        # Takes the current mapset and looks for maps only inside it
        self.current_mapset = grass.read_command('g.mapset', flags = 'p').replace('\n','').replace('\r','')        
        
        # Parameters
        
        # Maps to be processed
        self.input_maps = [] # List of input maps
        
        # For output names
        self.outputdir = '' # path to the folder where output maps
        self.output_prefix = '' # prefix to be appended to output map names
        self.add_counter_name = False # whether or not to include a counter in the output map names
        
        # Options for outputs and processing
        # remove_trash: If True, maps generated in the middle of the processes for creating final maps are removed from GRASS location
        self.remove_trash = True
        # prepare_biodim: If True, the package is run to prepare input maps and files to run BioDIM individual-based model package
        self.prepare_biodim = False
        # calc_statistics: If True, statistics files of the maps are saved while creating them
        self.calc_statistics = True
        # calc_multiple: True in case of running metrics for multiple maps, and False if running for only one map
        self.calc_multiple = False        
        
        # Metrics to be calculated
        self.binary = False # Option: Transform input maps into binary class maps
        self.calc_patch_size = False # Option: Patch area maps
        self.calc_frag_size = False # Option: Fragment area maps (removing corridors and branches)
        self.struct_connec = False # Option: Structural connectivity maps
        self.percentage_habitat = False # Option: Proportion of habitat
        self.functional_connected_area = False # Option: Functionally connected area maps
        self.functional_area_complete = False # Option: Complete functionally connected area maps
        self.functional_connectivity_map = False # Option: Functional connectivity maps
        
        #self.Dist = True # Option: Distance from edge maps
        #self.PCT = True # Option: Generate percentage (of habitat, of edges) maps
        
        # Options for each metric
        
        # For multiple
        self.zero_bin = True # whether the binary generated will be 1/0 (True) or 1/null (False)
        self.zero_metrics = False # whether the metrics generated will have non habitat values as 0 (True) or null (False)
        self.use_calculated_bin = False # whether binary maps generated will use be used for calculating the other metrics
        self.diagonal = False # whether or not to clump pixels using diagonal pixels (used for many functions)
        # For binary maps
        self.list_habitat_classes = [] # list of values that correspond to habitat
        self.export_binary = False # whether or not to export generated binary maps
        # For patch size
        self.export_patch_size = False # whether or not to export generated patch size maps
        self.export_patch_id = False # whether or not to export generated patch ID maps
        # For fragment size
        self.list_edge_depth_frag = [] # list of values of edge depth to be considered for fragmentation process
        self.export_frag_size = False # whether or not to export generated fragment size maps
        self.export_frag_id = False # whether or not to export generated fragment ID maps
        # For structural connectivity
        self.export_struct_connec = False # whether or not to export generated structural connectivity maps
        # For percentage of habitat 
        self.list_window_size_habitat = [] # list of window sizes to be considered for proportion of habitat
        self.method_percentage = 'average' # method used in r.neighbors to calculate the proportion of habitat
        self.export_percentage_habitat = False # whether or not to export generated maps of proportion of habitat
        # Functional connectivity
        self.list_gap_crossing = [] # list of gap crossing distances to be considered for functional connectivity
        self.export_func_con_area = False # whether or not to export generated functional connectivity area maps
        self.export_func_con_pid = False # whether or not to export generated functional connectivity patch ID maps
        # For edges
        
        # For diversity
        
        # GUI options
        
        # List of maps to be chosen inside a mapset, in GUI
        self.map_list = []
        # Chosen map to be shown in the list, within the GUI
        self.chosen_map = ''
        # Expression for looking at multiple input maps
        self.pattern_name = ''  
        
        ############ REMOVE?
        self.chebin = ''
        self.checEDGE = ''
        self.checkCalc_PCTedge = ''
        self.checPCT = ''
        self.check_diversity = ''
        self.analise_rayos = ''
        self.list_meco = ''
        
        #------------------------------------------------------#
        #---------------INITIALIZING GUI-----------------------#
        #------------------------------------------------------#
        
        ########### Find out the best way to set the pixel size in Windows and Linux
        # Adjusting width of GUI elements depending on the Operational System
        if CURRENT_OS == "Windows":
          self.add_width = 0
        elif CURRENT_OS == "Linux":
          self.add_width = 50
        # MAC?
        else:
          self.add_width = 0
        
        # Listing maps within the mapset, to be displayed and select as input maps
        
        # If preparing maps for running BioDIM, the maps must be inside a mapset named 'userbase'
        if self.prepare_biodim: 
          self.map_list=grass.list_grouped ('rast') ['userbase']
        else:
          self.map_list=grass.list_grouped ('rast') [self.current_mapset]
          
        #################### colocar isso de novo no final de uma rodada e atualizar o combobox - talvez o mapa
        ### gerado aparececa la!! testar!        
        
        #---------------------------------------------#
        #------------ MAIN GUI ELEMENTS --------------#
        #---------------------------------------------#
        
        # Title
        #self.quote = wx.StaticText(self, id=-1, label = "LandScape Metrics", pos = wx.Point(20, 20))        
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #self.quote.SetForegroundColour("blue")
        #self.quote.SetFont(font)

        self.imageFile0 = 'lsmetrics_logo.png'
        im0 = Image.open(self.imageFile0)
        jpg0 = wx.Image(self.imageFile0, wx.BITMAP_TYPE_ANY).Scale(200, 82).ConvertToBitmap()
        wx.StaticBitmap(self, -1, jpg0, (100, 15), (jpg0.GetWidth(), jpg0.GetHeight()), style=wx.SUNKEN_BORDER)                  
        
        # LEEC lab logo
        imageFile = 'logo_lab.png'
        im1 = Image.open(imageFile)
        jpg1 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        wx.StaticBitmap(self, -1, jpg1, (20, 470), (jpg1.GetWidth(), jpg1.GetHeight()), style=wx.SUNKEN_BORDER)
        
        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self, 5, '', wx.Point(200, 470), wx.Size(290 + self.add_width, 150), wx.TE_MULTILINE | wx.TE_READONLY)        
        
        #---------------------------------------------#
        #-------------- RADIO BOXES ------------------#
        #---------------------------------------------#   
      
        # RadioBox - event 92 (single/multiple)
        # Calculate metrics for a single or multiple maps?
        self.single_multiple_maps = ['Single', 'Multiple']
        rb1 = wx.RadioBox(self, 92, "Single or multiple maps?", wx.Point(20, 117), wx.DefaultSize,
                          self.single_multiple_maps, 2, wx.RA_SPECIFY_ROWS)
        wx.EVT_RADIOBOX(self, 92, self.EvtRadioBox)
      
        # RadioBox - event 91 (prepare maps for BioDIM)
        # Prepare files and maps for running BioDIM individual-based model?
        self.BioDimChoice = ['No', 'Yes']
        rb2 = wx.RadioBox(self, 91, "Prepare maps for BioDIM?", wx.Point(20, 195), wx.DefaultSize,
                          self.BioDimChoice, 2, wx.RA_SPECIFY_COLS)
        wx.EVT_RADIOBOX(self, 91, self.EvtRadioBox)                   
        
        #---------------------------------------------#
        #-------------- MAP SELECTION ----------------#
        #---------------------------------------------#          
        
        # Static text
        self.SelectMap = wx.StaticText(self, -1, "Select input map:", wx.Point(250, 112))
        
        # ComboBox - event 93 (select an input map from a combo box)
        
        # Maps shown when selecting a single map to calculate metrics
        try: # Try to select the first map of the list of maps loaded in the GRASS GIS location
          self.chosen_map = self.map_list[0]
        except: # If there are no maps loaded
          self.chosen_map = ''
        
        # ComboBox
        self.editmap_list = wx.ComboBox(self, 93, self.chosen_map, wx.Point(165 + self.add_width, 130), wx.Size(260, -1),
                                        self.map_list, wx.CB_DROPDOWN)
        wx.EVT_COMBOBOX(self, 93, self.EvtComboBox)
        ############### do we need that here???
        wx.EVT_TEXT(self, 93, self.EvtText)              
        
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1, "Pattern:", wx.Point(165 + self.add_width, 165))
        
        # Text Control - event 190
        # Regular expression (pattern) for selecting multiple maps
        self.editname1 = wx.TextCtrl(self, 190, '', wx.Point(230 + self.add_width, 160), wx.Size(195,-1))
        self.editname1.Disable()
        wx.EVT_TEXT(self, 190, self.EvtText)
        
        #---------------------------------------------#
        #-------------- BINARY MAPS ------------------#
        #---------------------------------------------#        
        
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1, "Create binary map:", wx.Point(20, 250)) # Or habitat map?
        
        # Check box - event 100 (creating binary class maps)
        self.insure1 = wx.CheckBox(self, 100, "", wx.Point(135 + self.add_width, 248))
        wx.EVT_CHECKBOX(self, 100,   self.EvtCheckBox)       

        # Static text
        self.SelectMetrics1 = wx.StaticText(self, -1, "Codes for habitat:", wx.Point(165 + self.add_width, 250))
        
        # Text Control - event 191
        # List of codes that represent habitat, for generating binary class maps
        self.editname2 = wx.TextCtrl(self, 191, '', wx.Point(300 + self.add_width, 248), wx.Size(120,-1)) 
        wx.EVT_TEXT(self, 191, self.EvtText)
        self.editname2.Disable()
        
        # Static text
        self.export_text1 = wx.StaticText(self, -1, "Export?", wx.Point(450 + self.add_width, 215))
        
        # Check Box - event 51 (export binary maps)
        self.insure2 = wx.CheckBox(self, 51, "", wx.Point(465 + self.add_width, 248))
        wx.EVT_CHECKBOX(self, 51, self.EvtCheckBox)
        self.insure2.Disable()
        
        # Check Box - event 71 (use binary maps calculated to calculate other landscape metrics)
        self.insure3 = wx.CheckBox(self, 71, 'Use binary maps to calculate other metrics?', wx.Point(20, 280))
        wx.EVT_CHECKBOX(self, 71, self.EvtCheckBox)
        self.insure3.Disable()
        
        #---------------------------------------------#
        #-------- STRUCTURAL CONNECTIVITY ------------#
        #---------------------------------------------#         
      
        # Static text
        self.SelectMetrics2 = wx.StaticText(self, -1, "Metrics of structural connectivity:", wx.Point(20, 310))
        
        #------------
        # Patch size
        
        # Static text
        self.SelectMetrics3 = wx.StaticText(self, -1, "Patch size map:", wx.Point(20, 340))
        
        # Check box - event 101 (check calculate patch size)
        self.insure4 = wx.CheckBox(self, 101, '', wx.Point(135 + self.add_width, 338))
        wx.EVT_CHECKBOX(self, 101, self.EvtCheckBox)
                
        # Check Box - event 52 (export patch size maps)
        self.insure5 = wx.CheckBox(self, 52, "", wx.Point(465 + self.add_width, 338))
        wx.EVT_CHECKBOX(self, 52, self.EvtCheckBox)
        self.insure5.Disable()
        
        #------------
        # Fragment size        
        
        # Static text
        self.SelectMetrics4 = wx.StaticText(self, -1, "Fragment size map:", wx.Point(20, 370))
                
        # Check box - event 102 (check calculate fragment size)
        self.insure6 = wx.CheckBox(self, 102, '', wx.Point(135 + self.add_width, 368))
        wx.EVT_CHECKBOX(self, 102, self.EvtCheckBox)         
        
        # Static text
        self.SelectMetrics5 = wx.StaticText(self, -1, "Edge depths (m):", wx.Point(165 + self.add_width, 370))
                
        # Text Control - event 192
        # List of edge depths for calculation fragment size maps
        self.editname3 = wx.TextCtrl(self, 192, '', wx.Point(300 + self.add_width, 368), wx.Size(120,-1)) 
        wx.EVT_TEXT(self, 192, self.EvtText)
        self.editname3.Disable()        
        
        # Check Box - event 53 (export fragment size maps)
        self.insure7 = wx.CheckBox(self, 53, "", wx.Point(465 + self.add_width, 368))
        wx.EVT_CHECKBOX(self, 53, self.EvtCheckBox)
        self.insure7.Disable()
        
        #------------
        # Structural connectivity
        
        # Static text
        self.SelectMetrics6 = wx.StaticText(self, -1, "Structural connectivity:", wx.Point(20, 400))
                        
        # Check box - event 103 (check calculate structural connectivity)
        self.insure8 = wx.CheckBox(self, 103, '', wx.Point(135 + self.add_width, 398))
        wx.EVT_CHECKBOX(self, 103, self.EvtCheckBox)
        self.insure8.Disable()
        
        # Check Box - event 54 (export structural connectivity maps)
        self.insure9 = wx.CheckBox(self, 54, "", wx.Point(465 + self.add_width, 398))
        wx.EVT_CHECKBOX(self, 54, self.EvtCheckBox)
        self.insure9.Disable()        
        
        #------------
        # Proportion of habitat
        
        # Static text
        self.SelectMetrics7 = wx.StaticText(self, -1, "Proportion of habitat:", wx.Point(20, 430))
                        
        # Check box - event 104 (check calculate proportion of habitat)
        self.insure10 = wx.CheckBox(self, 104, '', wx.Point(135 + self.add_width, 428))
        wx.EVT_CHECKBOX(self, 104, self.EvtCheckBox)         
                
        # Static text
        self.SelectMetrics8 = wx.StaticText(self, -1, "Window size (m):", wx.Point(165 + self.add_width, 430))
                        
        # Text Control - event 193
        # List of moving window sizes for calculating proportion of habitat
        self.editname4 = wx.TextCtrl(self, 193, '', wx.Point(300 + self.add_width, 428), wx.Size(120,-1)) 
        wx.EVT_TEXT(self, 193, self.EvtText)
        self.editname4.Disable()        
                
        # Check Box - event 55 (export proportion of habitat)
        self.insure11 = wx.CheckBox(self, 55, "", wx.Point(465 + self.add_width, 428))
        wx.EVT_CHECKBOX(self, 55, self.EvtCheckBox)
        self.insure11.Disable()
        
        
        
        
        
        
        self.SelectMetrics = wx.StaticText(self, -1,"Connectivity map:", wx.Point(20, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"Gap crossing list (m):", wx.Point(140, 500))
        
        # Static text      
        self.SelectMetrics = wx.StaticText(self, -1,"Core/Edge map:", wx.Point(20, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"Edge depth list (m):", wx.Point(140, 500))
      
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1,"Percentage:", wx.Point(20, 550))
        self.SelectMetrics = wx.StaticText(self, -1,"Habitat", wx.Point(90, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"Edge/Core", wx.Point(156, 500))
      
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1,"Extents:", wx.Point(236, 500)) # para as pct

        # Static text
        self.SelectMetrics = wx.StaticText(self, -1,"Calculate Statistics:", wx.Point(20, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"Distance from edge map:", wx.Point(20, 500))
        
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1,"Landscape diversity map:", wx.Point(20, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"Extents (m):", wx.Point(170, 500)) # para  diversidade de shannon
        
        # Static text
        self.SelectMetrics = wx.StaticText(self, -1,"Export: Hab/Edge/Matrix", wx.Point(20, 500))
        self.SelectMetrics = wx.StaticText(self, -1,"| Corridor/Branch/SS", wx.Point(170, 500))
        
        #---------------------------------------------#
        #-------------- COMBO BOXES ------------------#
        #---------------------------------------------#        
      
          
        
        
        #---------------------------------------------#
        #-------------- CHECK BOXES ------------------#
        #---------------------------------------------#          
      
        #self.insure = wx.CheckBox(self, 96, "AH Patch.", wx.Point(70,150))
        #wx.EVT_CHECKBOX(self, 96,   self.EvtCheckBox)     
      
        #self.insure = wx.CheckBox(self, 95, "AH Frag.", wx.Point(143,150))
        #wx.EVT_CHECKBOX(self, 95,   self.EvtCheckBox)
        
                  
      
        self.insure = wx.CheckBox(self, 97, "", wx.Point(120, 500)) # area con connectivity
        wx.EVT_CHECKBOX(self, 97,   self.EvtCheckBox)  
      
        self.insure = wx.CheckBox(self, 150, "", wx.Point(120, 500)) #EDGE/Core
        wx.EVT_CHECKBOX(self, 150,   self.EvtCheckBox)  
        #"""
        #essa funcao a baixo eh o botao para saber se vai ou nao calcular o mapa de distancia euclidiana
          #"""        
        self.insure = wx.CheckBox(self, 151, "", wx.Point(135, 500)) # pct habitat
        wx.EVT_CHECKBOX(self, 151,   self.EvtCheckBox)            
      
        #"""
        #essa funcao a baixo eh o botao para saber se vai ou nao calcular o mapa de distancia euclidiana
        #"""
        self.insure = wx.CheckBox(self, 99, "", wx.Point(150, 500)) # self.Distedge botaozainho da distancia em relacao a borda
        wx.EVT_CHECKBOX(self, 99,   self.EvtCheckBox)  
      
      
        
      
        """
              essa funcao a baixo eh o botao para saber se vai ou nao calcular o mapa de diveridade de shannon
              """
        self.insure = wx.CheckBox(self, 1111, "", wx.Point(150, 500)) # Criando mapa de diversidade de shannon
        wx.EVT_CHECKBOX(self, 1111,   self.EvtCheckBox)   
      
      
        self.insure = wx.CheckBox(self, 152, "", wx.Point(215, 500)) # pct edge edge/core preciso implementar
        wx.EVT_CHECKBOX(self, 152,   self.EvtCheckBox)   
      
      
        """
              essa funcao a baixo eh o botao para saber se vai ou nao calcular a statistica para os mapas
              """
        self.insure = wx.CheckBox(self, 98, "", wx.Point(150, 500)) # self.calc_statistics botaozainho da statisica
        wx.EVT_CHECKBOX(self, 98,   self.EvtCheckBox)      
      
        self.insure = wx.CheckBox(self, 153, "", wx.Point(150, 500)) # export hab/edge/matrix
        wx.EVT_CHECKBOX(self, 153,   self.EvtCheckBox)       
      
        self.insure = wx.CheckBox(self, 154, "", wx.Point(275, 500)) # export corridor branch ss
        wx.EVT_CHECKBOX(self, 154,   self.EvtCheckBox)     

        #---------------------------------------------#
        #-------------- TEXT CONTROLS ----------------#
        #---------------------------------------------# 
        
        # Include fast description
        

               
        

        # List of extents for percentage maps
        self.editname7 = wx.TextCtrl(self, 194, '', wx.Point(300 + self.add_width, 500), wx.Size(120,-1))
        # List of radii on influence for calculating landscape diversity/heterogeneity
        self.editname8 = wx.TextCtrl(self, 195, '', wx.Point(300 + self.add_width, 500), wx.Size(120,-1))
        
        #---------------------------------------------#
        #-------------- TEXT EVENTS ------------------#
        #---------------------------------------------#       
        
        
        
        
        wx.EVT_TEXT(self, 194, self.EvtText)
        wx.EVT_TEXT(self, 195, self.EvtText)
        
        #---------------------------------------------#
        #-------------- BUTTONS ----------------------#
        #---------------------------------------------#        
        
        self.button = wx.Button(self, 10, "START CALCULATIONS", wx.Point(20, 630))
        wx.EVT_BUTTON(self, 10, self.OnClick)
        
        self.button = wx.Button(self, 8, "EXIT", wx.Point(270, 630))
        wx.EVT_BUTTON(self, 8, self.OnExit)        

    #______________________________________________________________________________________________________    
    # Radio Boxes        
    def EvtRadioBox(self, event):
      
      # RadioBox - event 91 (prepare maps for BioDIM)
      if event.GetId() == 91:
        self.text_biodim = event.GetString()
        if self.text_biodim == 'No':
          self.prepare_biodim = False
        elif self.text_biodim == 'Yes':
          self.prepare_biodim = True
        else:
          raise "Error: Preparation of BioDIM maps must be either Yes or No!\n"
          
        # Refresh the list of possible input maps
        if self.prepare_biodim:        
          self.map_list = grass.list_grouped ('rast') ['userbase']
        else:
          self.map_list = grass.list_grouped ('rast') ['PERMANENT']      
      
      # RadioBox - event 92 (single/multiple maps)
      if event.GetId() == 92: 
        self.text_multiple = event.GetString()
        
        if self.text_multiple == 'Single':
          self.calc_multiple = False
          self.editmap_list.Enable()
          self.editname1.Disable()
        elif self.text_multiple == 'Multiple':
          self.calc_multiple = True
          self.editmap_list.Disable()
          self.editname1.Enable()
        else:
          raise "Error: Calculations must be done for either single or multiple maps!\n"
     
    #______________________________________________________________________________________________________
    # Combo Boxes
    def EvtComboBox(self, event):
      
        # Combo Box - event 93 (take the name of single or multiple maps and transform it into a list)
        if event.GetId() == 93:
            self.input_maps = [event.GetString()]
            self.logger.AppendText('Map: %s\n' % event.GetString())
        else:
            self.logger.AppendText('EvtComboBox: NEEDS TO BE SPECIFIED')
            
            


        
    #______________________________________________________________________________________________________   
    def OnClick(self,event):
        #self.logger.AppendText(" Click on object with Id %d\n" %event.GetId())
        
        #______________________________________________________________________________________________________________ 
        if event.GetId()==10:   #10==START

          # Before running and calculating the metrics, the user must define the output folder
          # where output maps and files will be saved
          self.dirout=selectdirectory()
          
          
          if self.calc_multiple=="Single":
            
            if self.prepare_biodim:
              self.output_prefix2 = 'lndscp_0001_'            
            
            if self.Habmat: ############ adicionei isso aqui: talvez temos que aplicar as outras funcoes ja nesse mapa?
              ###### as outras funcoes precisam de um mapa binario de entrada? ou pode ser so um mapa habitat/null?
              
              create_habmat_single(self.input_map, self.output_prefix2, self.list_habitat_classes, prepare_biodim=self.prepare_biodim, 
                                   calc_statistics=self.calc_statistics, dirout=self.dirout)
            if self.patch_size==True:   
              
              patchSingle(self.input_map, self.output_prefix2, self.dirout, self.prepare_biodim,self.calc_statistics,self.remove_trash)
              
            if self.Frag==True:
              
              areaFragSingle(self.input_map, self.output_prefix2, self.escala_frag_con, self.dirout, self.prepare_biodim,self.calc_statistics,self.remove_trash)
            if self.Con==True:
              areaconSingle(self.input_map, self.output_prefix2, self.escala_frag_con, self.dirout, self.prepare_biodim, self.calc_statistics, self.remove_trash)
            if self.checEDGE==True:
              
              create_EDGE_single(self.input_map, self.escala_ED, self.dirout, self.output_prefix2, self.calc_statistics, self.remove_trash,self.list_esc_pct)
             
            if self.Dist==True:
              dist_edge_Single(self.input_map,self.output_prefix2, self.prepare_biodim, self.dirout, self.remove_trash)
              
            if self.checPCT==True:
              PCTs_single(self.input_map, self.list_esc_pct)
            if self.check_diversity==True:
              shannon_diversity(self.input_map, self.dirout, self.analise_rayos)
            
          else: # caso seja pra mais de um arquivos
                      
            if self.prepare_biodim:
              self.input_maps=grass.list_grouped ('rast', pattern=self.pattern_name) ['userbase']
              self.output_prefix2 = 'lndscp_'              
            else:
              self.input_maps=grass.list_grouped ('rast', pattern=self.pattern_name) ['PERMANENT']   
              
            if self.Habmat: ############ adicionei isso aqui: talvez temos que aplicar as outras funcoes ja nesse mapa?
              ###### as outras funcoes precisam de um mapa binario de entrada? ou pode ser so um mapa habitat/null?
              create_habmat(self.input_maps, list_habitat_classes=self.list_habitat_classes, 
                            prepare_biodim=self.prepare_biodim, calc_statistics=self.calc_statistics, prefix = self.output_prefix2)            
            
             
            
            if self.checEDGE==True:
              self.list_meco=create_EDGE(self.input_maps, self.escala_ED, self.dirout, self.output_prefix2, self.calc_statistics, self.remove_trash,self.list_esc_pct,self.checkCalc_PCTedge)     
              areaFrag(self.input_maps, self.output_prefix2,self.escala_ED, self.dirout, self.prepare_biodim,self.calc_statistics,self.remove_trash,self.list_meco,self.checEDGE)
              
            
            if self.Frag==True:
              self.list_meco=[]
              self.checEDGE=False
              
              areaFrag(self.input_maps, self.output_prefix2, self.escala_frag_con, self.dirout, self.prepare_biodim,self.calc_statistics,self.remove_trash,self.list_meco,self.checEDGE)
              
            if self.Con==True:
              self.ListmapsPatch=patch_size(self.input_maps, self.output_prefix2, self.dirout, self.prepare_biodim,self.calc_statistics,self.remove_trash)
              areacon(self.input_maps,self.output_prefix2, self.escala_frag_con, self.dirout, self.prepare_biodim, self.calc_statistics, self.remove_trash) 
              
            
            if self.Dist==True:
              dist_edge(self.input_maps,self.output_prefix2, self.prepare_biodim, self.dirout, self.remove_trash)
            
            if self.checPCT==True:
              PCTs(self.input_maps, self.list_esc_pct)
               
        #______________________________________________________________________________________________________________ 
        if event.GetId()==11:   
          if self.chebin==True:
            if  self.calc_multiple=="Single":
              createBinarios_single(self.input_map)
            else:
              
              if self.prepare_biodim:
                self.input_maps=grass.list_grouped ('rast', pattern=self.pattern_name) ['userbase']
              else:
                self.input_maps=grass.list_grouped ('rast', pattern=self.pattern_name) ['PERMANENT']                
              
              createBinarios(self.input_maps)
          
          
        
        
        # 
        d= wx.MessageDialog( self, " Calculations finished! \n"
                            " ","Thanks", wx.OK)
                            # Create a message dialog box
        d.ShowModal() # Shows it
        d.Destroy()
        
    
    #______________________________________________________________________________________________________________                
    # Text Events
    def EvtText(self, event):
         
        # Text Event - event 190 (define the pattern for searching for input maps)
        if event.GetId() == 190:
          self.pattern_name = event.GetString()
          
                  
        if event.GetId() == 198:
          edge_depth_frag_aux = event.GetString()
          try:
            self.edge_depth_frag = [float(i) for i in edge_depth_frag_aux.split(',')]
          except:
            raise Exception('Edge depth values must be numerical.')
          
          
        if event.GetId() == 199:
          self.escala_ED=event.GetString()    
          
        # Text Control - event 191
        # List of codes that represent habitat, for generating binary class maps
        if event.GetId() == 191:
          list_habitat = event.GetString()
          try: # Transform values in a list of integers
            self.list_habitat_classes = [int(i) for i in list_habitat.split(',')]
          except:
            self.list_habitat_classes = [-1]
            print 'Codes for binary class reclassification of maps must be numerical.'
            
        # Text Control - event 192
        # List of edge depths for calculation fragment size maps
        if event.GetId() == 192:
          list_edge_frag = event.GetString()
          try: # Transform values in a list of float numbers
            self.list_edge_depth_frag = [float(i) for i in list_edge_frag.split(',')]
          except:
            self.list_edge_depth_frag = [-1]
            print 'Edge depth must be a positive numerical values, given in meters.'
            
        # Text Control - event 193
        # List of moving window sizes for calculating proportion of habitat
        if event.GetId() == 193:
          list_window_size = event.GetString()
          try: # Transform values in a list of float numbers
            self.list_window_size_habitat = [float(i) for i in list_window_size.split(',')]
          except:
            self.list_window_size_habitat = [-1]
            print 'Window size must be a positive numerical values, given in meters.'        
        
        if event.GetId()==194:
          # funcao para pegar a lista de escalas de porcentagem
          list_esc_percent=event.GetString()
          self.list_esc_pct=list_esc_percent.split(',')
        if event.GetId()==195:
          # funcao para pegar a lista de escalas de porcentagem
          list_esc_raios_DV=event.GetString()
          self.analise_rayos=list_esc_raios_DV.split(',')        
          
        

    #______________________________________________________________________________________________________
    # Check Boxes
    def EvtCheckBox(self, event):
        #self.logger.AppendText('EvtCheckBox: %d\n' % event.Checked())
        if event.GetId()==95:
            if event.Checked()==1:
                self.Frag=True
                self.logger.AppendText('EvtCheckBox:\nMetric Selected: Frag \n')
            else:
                self.Frag=False
                self.logger.AppendText('EvtCheckBox: \nMetric Not Selected: Frag \n')
                
                
        if event.GetId()==96:
          if event.Checked()==1:
            self.patch_size=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Patch size \n')
          else:
            self.patch_size=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Patch size\n')
                   
            
        if event.GetId()==97:
          if event.Checked()==1:
            self.Con=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Connectivity \n')
          else:
            self.Con=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Connectivity \n')
                         
        
        if event.GetId()==98: #criando txtx de statitiscas
          if int(event.Checked())==1: 
            self.calc_statistics=True           
            self.logger.AppendText('EvtCheckBox:\nCalculate connectivity statistics: '+`self.calc_statistics`+' \n')
            
            
            
        if event.GetId()==99: #criando mapa de distancia 
          if int(event.Checked())==1:
            self.Dist=True
            self.logger.AppendText('EvtCheckBox:\n Create Distance map: '+`self.Dist`+' \n')
         
        # Check Box - event 100 (calculate binary class map)   
        if event.GetId() == 100:
          if int(event.Checked()) == 1:
            self.binary = True
            self.logger.AppendText('Create binary map: On\n')
            self.editname2.Enable() # Enable list of habitat values
            self.insure2.Enable() # Enable possibility to export binary maps
            self.insure3.Enable() # Enable possibility to use generated binary maps for other metrics
          else:
            self.binary = False
            self.logger.AppendText('Create binary map: Off\n')
            self.editname2.Disable() # Disable list of habitat values
            self.insure2.Disable() # Disable possibility to export binary maps
            self.insure3.Disable() # Disable possibility to use generated binary maps for other metrics
            
        # Check Box - event 71 (use calculated binary class maps to calculate other metrics)
        if event.GetId() == 71:
          if int(event.Checked()) == 1:
            self.use_calculated_bin = True
            self.logger.AppendText('Use binary maps for calculating other landscape metrics: On\n')
          else:
            self.use_calculated_bin = False
            self.logger.AppendText('Use binary maps for calculating other landscape metrics: Off\n')
            
        # Check Box - event 101 (check calculate patch size)
        if event.GetId() == 101:
          if int(event.Checked()) == 1:
            self.calc_patch_size = True
            self.logger.AppendText('Calculate patch size: On\n')
            self.insure5.Enable() # Enable possibility to export patch size maps
            #self.insure3.Enable() # Enable possibility to use generated binary maps for other metrics
          else:
            self.calc_patch_size = False
            self.logger.AppendText('Calculate patch size: Off\n')
            self.insure5.Disable() # Disable possibility to export patch size maps
            
          # If both patch size and frag size are checked, we may calculate structural connectivity
          if self.calc_frag_size and self.calc_patch_size:
            self.insure8.Enable() # Enable possibility to calculate structural connectivity maps
            self.insure9.Enable() # Enable possibility to export structural connectivity maps
          else:
            self.insure8.Disable() # Disable possibility to calculate structural connectivity maps
            self.insure9.Disable() # Disable possibility to export structural connectivity maps          
        
        
        # Check Box - event 102 (check calculate fragment size)
        if event.GetId() == 102:
          if int(event.Checked()) == 1:
            self.calc_frag_size = True
            self.logger.AppendText('Calculate fragment size: On\n')
            self.insure7.Enable() # Enable possibility to export fragment size maps
            self.editname3.Enable() # Enable list of edge depths
          else:
            self.calc_frag_size = False
            self.logger.AppendText('Calculate fragment size: Off\n')
            self.insure7.Disable() # Disable possibility to export fragment size maps
            self.editname3.Disable() # Disable list of habitat values
            
          # If both patch size and frag size are checked, we may calculate structural connectivity
          if self.calc_frag_size and self.calc_patch_size:
            self.insure8.Enable() # Enable possibility to calculate structural connectivity maps
            self.insure9.Enable() # Enable possibility to export structural connectivity maps
          else:
            self.insure8.Disable() # Disable possibility to calculate structural connectivity maps
            self.insure9.Disable() # Disable possibility to export structural connectivity maps
            
        
        # Check Box - event 103 (check calculate structural connectivity)
        if event.GetId() == 103:
          if int(event.Checked()) == 1:
            self.struct_connec = True
            self.logger.AppendText('Calculate structural connectivity: On\n')
            self.insure9.Enable() # Enable possibility to export structural connectivity maps
          else:
            self.struct_connec = False
            self.logger.AppendText('Calculate structural connectivity: Off\n')
            self.insure9.Disable() # Disable possibility to export structural connectivity maps
            
            
        # Check Box - event 104 (check calculate proportion of habitat)
        if event.GetId() == 104:
          if int(event.Checked()) == 1:
            self.percentage_habitat = True
            self.logger.AppendText('Calculate proportion of habitat: On\n')
            self.editname4.Enable() # Enable list of window sizes
            self.insure11.Enable() # Enable possibility to export maps of proportion of habitat
          else:
            self.percentage_habitat = False
            self.logger.AppendText('Calculate proportion of habitat: Off\n')
            self.editname4.Disable() # Disable list of window sizes
            self.insure11.Disable() # Disable possibility to export maps of proportion of habitat
        
        #
        if event.GetId()==1111: #check EDGE
          if int(event.Checked())==1:
            self.check_diversity=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Diversity shannon map \n')
          else:
            self.check_diversity=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Diversity shannon map \n')         
        
        if event.GetId()==150: #check EDGE
          if int(event.Checked())==1:
            self.checEDGE=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Edge \n')
          else:
            self.checEDGE=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Edge \n')
          
         
         
        if event.GetId()==151: #check EDGE
          if int(event.Checked())==1:
            self.checPCT=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Percentage habitat \n')
          else:
            self.checPCT=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Percentage habitat \n')           
        
        # CRIAR UM BOTAO E UM EVENTO DESSES AQUI, PARA O MAPA DE DIST (mesmo que ele so seja usado para o biodim)
        if event.GetId()==152: #check EDGE
          if int(event.Checked())==1:
            self.checkCalc_PCTedge=True
            self.logger.AppendText('EvtCheckBox:\nMetric Selected: Percentage from edge/core \n')
          else:
            self.checkCalc_PCTedge=False
            self.logger.AppendText('EvtCheckBox:\nMetric Not Selected: Percentage from edge/core \n')             
        
        # Check boxes for exporting maps
        
        # Check Box - event 51 (export binary maps)
        if event.GetId() == 51:
          if int(event.Checked()) == 1:
            self.export_binary = True
            self.logger.AppendText('Export binary map: On\n')
          else:
            self.export_binary = False
            self.logger.AppendText('Export binary map: Off\n')
            
        # Check Box - event 52 (export patch size maps)
        if event.GetId() == 52:
          if int(event.Checked()) == 1:
            self.export_patch_size = True
            self.logger.AppendText('Export patch size map: On\n')
          else:
            self.export_patch_size = False
            self.logger.AppendText('Export patch size map: Off\n')
            
        # Check Box - event 53 (export fragment size maps)
        if event.GetId() == 53:
          if int(event.Checked()) == 1:
            self.export_frag_size = True
            self.logger.AppendText('Export fragment size map: On\n')
          else:
            self.export_frag_size = False
            self.logger.AppendText('Export fragment size map: Off\n')
            
        # Check Box - event 54 (export structural connectivity maps)
        if event.GetId() == 54:
          if int(event.Checked()) == 1:
            self.export_struct_connec = True
            self.logger.AppendText('Export structural connectivity map: On\n')
          else:
            self.export_struct_connec = False
            self.logger.AppendText('Export tructural connectivity map: Off\n')
            
        # Check Box - event 55 (export proportion of habitat)
        if event.GetId() == 55:
          if int(event.Checked()) == 1:
            self.export_percentage_habitat = True
            self.logger.AppendText('Export map of proportion of habitat: On\n')
          else:
            self.export_percentage_habitat = False
            self.logger.AppendText('Export map of proportion of habitat: Off\n')        
            
    #______________________________________________________________________________________________________
    def OnExit(self, event):
        d= wx.MessageDialog( self, " Thanks for using LSMetrics "+VERSION+"!\n"
                            "","Good bye", wx.OK)
                            # Create a message dialog box
        d.ShowModal() # Shows it
        d.Destroy() # finally destroy it when finished.
        frame.Close(True)  # Close the frame. 

#----------------------------------------------------------------------
#......................................................................
#----------------------------------------------------------------------
if __name__ == "__main__":
    
    # Size of the window
    ########### ver como conversar tamanho de pixel em windows e linux
    # Adjusting width of GUI depending on the Operational System
    if CURRENT_OS == "Windows":
      size = (520, 700)
    elif CURRENT_OS == "Linux":
      size = (520 + 50, 680)
    # MAC?    
    
    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, "LSMetrics "+VERSION, pos=(0,0), size = size)
    LSMetrics(frame,-1)
    frame.Show(1)
    
    app.MainLoop()
