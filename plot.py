import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

## SETTING #########################################################
# This code visualizes a designated FPGA composition with the given
# tile information extracted from Vivado.
# - case 0: if mainTiles is not empty, the code draws map for only mainTiles,
# - case 1: if mainTiles is empty and isConcise is True, the code draws concise version of map,
# - case 2: if mainTiles is empty and isConcise is False, the code draws detailed version.

mainTiles = []
# mainTiles = ["BRAM", "CLB", "CLK", "DSP", "INT", "IO", "PS"]
isConcise = True
csvFileName = "zedboard.csv"  # tile information
pd.set_option('display.max_columns', None)  # print all cols
####################################################################


# In concise version, INT_R and INT_L are considered INT,
# CLBLL_L, CLBLL_R are considered CLBLL,
# CLBLM_L, CLBLM_R are considered CLBLM.
# It cuts "Types" from the first "_"
def genConcise(tile_df, deviceMat, rowIDs, colIDs):
    tile_df['Type_concise'] = tile_df['Type'].\
        apply(lambda r: r.split('_')[0] if len(r.split('_')) > 1 else r)
    # assign unique id to each tile type
    tile_df['id_concise'] = tile_df["Type_concise"].astype('category').cat.codes

    null_df = tile_df[tile_df['Type'] == "empty"]
    deviceMat[rowIDs, colIDs] = tile_df['id_concise']
    numIDs = len(tile_df['id_concise'].unique())
    types = []
    for id_i in range(numIDs):
        id_df = tile_df[tile_df['id_concise'] == id_i]
        # peek 1st row's val, list all types in concise ver.
        type_concise = id_df['Type_concise'].iloc[0]
        types.append(type_concise)
    nullID = null_df['id_concise'].iloc[0]  # peek 1st row's val, finds what's id for "empty"
    return (deviceMat, numIDs, types, nullID)


# In verbose version, the code draws a map for all tile types.
def genVerbose(tile_df, deviceMat, rowIDs, colIDs):
    null_df = tile_df[tile_df['Type'] == "empty"]
    deviceMat[rowIDs, colIDs] = tile_df['id']
    numIDs = len(tile_df['id'].unique())
    types = []
    for id_i in range(numIDs):
        id_df = tile_df[tile_df['id'] == id_i]
        # peek 1st row's val, list all types in verbose ver.
        type_verbose = id_df['Type'].iloc[0]
        types.append(type_verbose)
    nullID = null_df['id'].iloc[0]  # peek 1st row's val, finds what's id for "empty"
    return (deviceMat, numIDs, types, nullID)


# In mainTypes version, it draws map only for tiles in mailTypes list.
# e.g. if CLB is in mainTiles, CLBLL_L, CLBLL_R, CLBLM_L, CLBLM_R are all considered CLB.
# if CLB is NOT in mainTiles, they are considered "empty"
def genMainTypes(tile_df, mainTiles, deviceMat, rowIDs, colIDs):
    tile_df['isMainTile'] = "no"  # initialized
    tile_df['Main Type'] = tile_df["Type"]  # initialized
    # print(tile_df)
    for elem in mainTiles:
        tile_df.loc[tile_df['Type'].str.startswith(elem), "isMainTile"] = "yes"
        tile_df.loc[tile_df['Type'].str.startswith(elem), "Main Type"] = elem

    tile_df.loc[tile_df['isMainTile'] == "no", "Main Type"] = "empty"  # if not main type, empty
    tile_df['id_main_type'] = tile_df["Main Type"].astype('category').cat.codes
    # print(tile_df)
    null_df = tile_df[tile_df['Main Type'] == "empty"]
    deviceMat[rowIDs, colIDs] = tile_df['id_main_type']
    numIDs = len(tile_df['id_main_type'].unique())
    types = []
    for id_i in range(numIDs):
        id_df = tile_df[tile_df['id_main_type'] == id_i]
        # peek 1st row's val, list all types in main types ver.
        type_concise = id_df['Main Type'].iloc[0]
        types.append(type_concise)
    nullID = null_df['id_main_type'].iloc[0]  # peek 1st row's val, finds what's id for "empty"
    return (deviceMat, numIDs, types, nullID)


# Draws 2D grid, "empty" tiles are grey
def matShow(data, numIDs, nullID, types):
    cmap = plt.get_cmap('jet', numIDs)
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmaplist[nullID] = (.5, .5, .5, 1.0)  # force "empty" tile to be grey
    # create the new map
    cmap = LinearSegmentedColormap.from_list('Custom cmap', cmaplist, cmap.N)

    # set limits .5 outside true range
    mat = plt.matshow(data, cmap=cmap, vmin=np.min(data) - .5, vmax=np.max(data) + .5)
    # plt.colorbar(mat, ticks=types)
    cbar = plt.colorbar(mat, ticks=np.arange(np.min(data), np.max(data) + 1))
    # cbar.set_ticks([])
    cbar.ax.set_yticklabels(types)  # labels
    plt.axis('off')


def main():
    tile_df = pd.read_csv(csvFileName)
    rowMax = tile_df['Row'].max()
    colMax = tile_df['Col'].max()
    tile_df = tile_df.drop('Sites', 1)
    tile_df = tile_df.drop('Cells', 1)
    # print(rowMax)
    # print(colMax)

    # fill NULL as "empty"
    tile_df['Type'] = tile_df['Type'].fillna('empty')
    # assign unique id to each tile type
    tile_df['id'] = tile_df["Type"].astype('category').cat.codes

    rowIDs = tile_df['Row']
    colIDs = tile_df['Col']
    # Creates 2d array for plot.
    # deviceMat[row][col] value is id for the tile in (row,col) location.
    # Each tile in 2d array is colored with different color,
    # and the "empty" tile type is colored grey
    deviceMat = np.zeros((rowIDs.max() + 1, colIDs.max() + 1))

    if(len(mainTiles) == 0):
        if(isConcise):
            (deviceMat, numIDs, types, nullID) = genConcise(tile_df, deviceMat, rowIDs, colIDs)
        else:
            (deviceMat, numIDs, types, nullID) = genVerbose(tile_df, deviceMat, rowIDs, colIDs)
    else:
        (deviceMat, numIDs, types, nullID) = genMainTypes(tile_df, mainTiles, deviceMat, rowIDs, colIDs)

    matShow(deviceMat, numIDs, nullID, types)
    plt.show()


if __name__ == '__main__':
    main()
