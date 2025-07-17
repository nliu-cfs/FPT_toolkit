# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 14:23:14 2024

@author: nliu
"""

import geopandas as gpd
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
from tqdm import tqdm
import postbp
import numpy as np
import os

# =====================
# Citation Reminder
# =====================
def citation_warning():
    print("""
    =====================================================
    |  NOTICE: If you use this code, please cite our article. |
    =====================================================
    """)

# =====================
# Data Loading Functions
# =====================
def load_hexagons(shp_path):
    return gpd.read_file(shp_path, driver='ESRI Shapefile')

def load_csv_data(csv_path, column_names):
    df = pd.read_csv(csv_path, names=column_names, skiprows=1, header=None)
    df.rename(columns={0:'column', 1:'row'}, inplace=True)
    df.set_index(['column', 'row'], inplace=True)
    df.dropna(how='all', inplace=True)
    df.reset_index(inplace=True)
    return df

def get_column_count(csv_path):
    with open(csv_path, 'r') as temp_f:
        col_count = max([len(l.split(",")) for l in temp_f.readlines()])
    return col_count

def melt_data(df, value_name):
    return df.melt(id_vars=['column','row'], var_name='round', value_name=value_name).dropna(how='any')

# =====================
# Grid and Geometry Functions
# =====================
def create_grid(ncols, nrows, xllcorner, yllcorner, cellsize, crs):
    cols = np.arange(1, ncols+1)
    rows = np.arange(1, nrows+1)
    outlist = [(i, j) for i in cols for j in rows]
    grids = pd.DataFrame(outlist, columns=['column', 'row'])
    grids['y_coord'] = yllcorner + (grids['row']-1)*cellsize
    grids['x_coord'] = xllcorner + (grids['column']-1)*cellsize
    gridPts = gpd.points_from_xy(x=grids['x_coord'], y=grids['y_coord'], crs=crs)
    return gpd.GeoDataFrame(grids, geometry=gridPts)

def spatial_join_grid(gridPts, hexagons):
    gridHexChart = gridPts.sjoin(hexagons, how='left', predicate='within')
    gridHexChart.dropna(how='any', inplace=True)
    gridHexChart = gridHexChart[['column', 'row', 'geometry', 'Node_ID']]
    return gridHexChart.reset_index(drop=True)

# =====================
# Ignition Data Functions
# =====================
def load_ignition_points(stats_path, crs, hexagons):
    igndata = pd.read_csv(stats_path, header=0)
    ignPts = gpd.points_from_xy(x=igndata['x_coord'], y=igndata['y_coord'], crs=crs)
    ignPts = gpd.GeoDataFrame(igndata, geometry=ignPts)
    ignPts = ignPts[['iteration', 'geometry']]
    ignHexChart = ignPts.sjoin(hexagons, how='left', predicate='within')
    ignHexChart.drop(labels=['index_right','geometry'], axis=1, inplace=True)
    return ignHexChart

# =====================
# Distance Calculation
# =====================
def calc_dist(ptID, ignID, nodes):
    pt1 = nodes.loc[nodes['Node_ID']==ptID]
    pt1.reset_index(drop=True, inplace=True)
    ignPt = nodes.loc[nodes['Node_ID']==ignID]
    ignPt.reset_index(drop=True, inplace=True)
    dist = pt1.distance(ignPt.geometry)
    return dist.values[0]

# =====================
# Main Analysis Functions
# =====================
def process_burndata(hexagons, arcs, nodes, bi_path, ros_path, fi_path, stats_path, grid_params, output_dir):
    SRID = hexagons.crs
    col_count = get_column_count(bi_path)
    column_names = [i for i in range(col_count)]
    fireBI = load_csv_data(bi_path, column_names)
    fireROS = load_csv_data(ros_path, column_names)
    fireFI = load_csv_data(fi_path, column_names)
    reshapeBI = melt_data(fireBI, 'iterationID')
    reshapeROS = melt_data(fireROS, 'ROS')
    reshapeFI = melt_data(fireFI, 'FI')
    burndata = reshapeBI.merge(reshapeROS, on=['column','row','round'], how='left')
    burndata = burndata.merge(reshapeFI, on=['column','row','round'], how='left')
    burndata0 = burndata.copy()
    gridPts = create_grid(*grid_params, crs=SRID)
    gridHexChart = spatial_join_grid(gridPts, hexagons)
    ignHexChart = load_ignition_points(stats_path, SRID, hexagons)
    burndataHex = gridHexChart.merge(burndata, on=['column','row'], how='right')
    burndataHex.dropna(subset='Node_ID', inplace=True)
    return burndataHex, ignHexChart, arcs, nodes

def build_graphs(burndataHex, ignHexChart, arcs, nodes, output_dir):
    burnDF = burndataHex.groupby(['iterationID','Node_ID'])[['ROS']].mean()
    burnDF.reset_index(inplace=True)
    burnDF = burnDF.merge(ignHexChart, left_on='iterationID', right_on='iteration', how='left')
    burnDF.rename(columns={'Node_ID_x':'Node_ID', 'Node_ID_y':'ignitionHex'}, inplace=True)
    burnDF = burnDF[['iterationID', 'ignitionHex', 'Node_ID']]
    burnDF.dropna(how='any', inplace=True)
    burnDF = burnDF[burnDF['Node_ID'] != burnDF['ignitionHex']]
    burnDF['Node_ID'] = burnDF['Node_ID'].astype(int)
    burnDF['ignitionHex'] = burnDF['ignitionHex'].astype(int)
    burnDF['iterationID'] = burnDF['iterationID'].astype(int)
    grandDF = pd.DataFrame()
    for it in tqdm(np.unique(burnDF['iterationID'])):
        burnDF1 = burnDF.loc[burnDF['iterationID']==it]
        nodes1 = burnDF1['Node_ID']
        nodes1 = pd.concat([nodes1, pd.Series(np.unique(burnDF1['ignitionHex'].values))])
        nodes1.reset_index(drop=True, inplace=True)
        edges = arcs.copy().drop(labels='geometry', axis=1)
        edges = edges.loc[edges['Node_1'].isin(nodes1.values)]
        edges = edges.loc[edges['Node_2'].isin(nodes1.values)]
        ipt = burnDF1['ignitionHex'].values[0]
        dff = pd.DataFrame()
        for n, row in edges.iterrows():
            dist_j = calc_dist(row['Node_2'], ipt, nodes)
            dist_i = calc_dist(row['Node_1'], ipt, nodes)
            if dist_j > dist_i:
                row = pd.DataFrame(row).T
                dff = pd.concat([dff, row])
        dff.insert(loc=0,column='iterationID', value=it)
        dff.insert(loc=0,column='origin', value=ipt)
        dff.rename(columns={'Node_1':'arcStart', 'Node_2':'arcEnd'}, inplace=True)
        grandDF = pd.concat([grandDF, dff])
    grandDF.reset_index(drop=True, inplace=True)
    grandDF = grandDF.apply(pd.to_numeric)
    grandDF['arcStart'] = grandDF['arcStart'].astype(int)
    grandDF['arcEnd'] = grandDF['arcEnd'].astype(int)
    # Union by iteration ID
    grandDF0 = grandDF.copy()
    df_itall = pd.DataFrame()
    for it in tqdm(np.unique(grandDF0['iterationID'])):
        df_it = grandDF0.loc[grandDF0['iterationID']==it]
        df_it.drop_duplicates(subset=['arcStart','arcEnd'], keep='first', inplace=True)
        df_itall = pd.concat([df_itall, df_it])
    df_itall.reset_index(drop=True, inplace=True)
    df_itall['iterationID'] = df_itall['iterationID'].astype(int)
    df_itall['V'] = 1
    df_itall['arcStart'] = df_itall['arcStart'].astype(int)
    df_itall['arcEnd'] = df_itall['arcEnd'].astype(int)
    df_itall[['iterationID', 'arcStart', 'arcEnd', 'V']].to_csv(os.path.join(output_dir, 'Fire_spread_graphs.txt'), index=False, header=False, sep='\t')
    df_itall_it = df_itall.copy()
    df_itall_it = df_itall_it[['iterationID', 'origin', 'V']]
    df_itall_it.drop_duplicates(subset=['iterationID', 'origin'], inplace=True)
    df_itall_it.drop_duplicates(subset=['iterationID'], inplace=True)
    df_itall_it[['iterationID', 'origin', 'V']].to_csv(os.path.join(output_dir, 'Fire_f_ign_node_i.txt'), index=False, header=False, sep='\t')
    iterID = df_itall.copy()
    iterID = iterID[['iterationID']]
    iterID.drop_duplicates(subset=['iterationID'], inplace=True)
    iterID['iterID'] = iterID['iterationID']
    iterID.to_csv(os.path.join(output_dir, 'f_ID.txt'), index=False, header=False, sep='\t')
    iterElem1 = df_itall.copy()
    iterElem2 = df_itall.copy()
    iterElem1 = iterElem1[['iterationID','origin']]
    iterElem2 = iterElem2[['iterationID','arcEnd']]
    iterElem1.drop_duplicates(subset=['iterationID','origin'], inplace=True)
    iterElem1.columns = ['iterationID','arcEnd']
    iterElem = pd.concat([iterElem1,iterElem2])
    iterElem.sort_values(by='iterationID', ignore_index=True, inplace=True)
    iterElem.drop_duplicates(subset=['iterationID','arcEnd'], inplace=True)
    iterElem['V'] = 1
    iterElem.to_csv(os.path.join(output_dir, 'Fire_f_node_i.txt'), index=False, header=False, sep='\t')
    # Fireplain scenarios
    grandDF1 = grandDF.copy()
    df_ignAll = pd.DataFrame()
    for ign in tqdm(np.unique(grandDF1['origin'])):
        df_ign = grandDF1.loc[grandDF1['origin']==ign]
        df_ign.drop_duplicates(subset=['iterationID','arcStart','arcEnd'], keep='first', inplace=True)
        df_ignGr = df_ign.groupby(['arcStart', 'arcEnd'])[['iterationID']].count()
        df_ignGr.reset_index(inplace=True)
        df_ignGr['ignitionID'] = ign
        df_ignAll = pd.concat([df_ignAll, df_ignGr])
    df_ignAll.reset_index(drop=True, inplace=True)
    df_ignAll['iterationID'] = df_ignAll['iterationID'].astype(int)
    df_ignAll['ignitionID'] = df_ignAll['ignitionID'].astype(int)
    df_ignAll['arcStart'] = df_ignAll['arcStart'].astype(int)
    df_ignAll['arcEnd'] = df_ignAll['arcEnd'].astype(int)
    df_ignAll[['ignitionID', 'arcStart', 'arcEnd', 'iterationID']].to_csv(os.path.join(output_dir, 'Fireplain_trees.txt'), index=False, header=False, sep='\t')
    ignID = df_ignAll.copy()
    ignID = ignID[['ignitionID']]
    ignID.drop_duplicates(subset=['ignitionID'], inplace=True)
    ignID['ignID'] = ignID['ignitionID']
    ignID['V'] = 1
    ignID.to_csv(os.path.join(output_dir, 'Fplain_ign_node_i.txt'), index=False, header=False, sep='\t')
    ignElem1 = df_ignAll.copy()
    ignElem2 = df_ignAll.copy()
    ignElem1 = ignElem1[['ignitionID','arcStart']]
    ignElem2 = ignElem2[['ignitionID','arcEnd']]
    ignElem1.drop_duplicates(subset=['ignitionID','arcStart'], inplace=True)
    ignElem1.columns = ['ignitionID','arcEnd']
    ignElem = pd.concat([ignElem1,ignElem2])
    ignElem.sort_values(by='ignitionID', ignore_index=True, inplace=True)
    ignElem.drop_duplicates(subset=['ignitionID','arcEnd'], inplace=True)
    ignElem['V'] = 1
    ignElem['arcEnd'] = ignElem['arcEnd'].astype(int)
    ignElem.to_csv(os.path.join(output_dir, 'Fplain_node_i.txt'), index=False, header=False, sep='\t')

# =====================
# Main Entrypoint
# =====================
def main():
    citation_warning()
    # File paths and parameters
    input_dir = 'rawData'
    output_dir = 'output'
    hex_shp = os.path.join(input_dir, 'hexagon400ha_cropped.shp')
    bi_path = os.path.join(input_dir, '_BI.csv')
    ros_path = os.path.join(input_dir, '_ROSRaw.csv')
    fi_path = os.path.join(input_dir, '_FIRaw.csv')
    stats_path = os.path.join(input_dir, 'stats_.csv')
    grid_params = (1015, 822, 294086.60254, 5977635.57756, 100)
    hexagons = load_hexagons(hex_shp)
    nodes = postbp.nodes_from_hexagons(hexagons)
    arcs = postbp.create_arcs(hexagons, Node_ID='Node_ID')
    burndataHex, ignHexChart, arcs, nodes = process_burndata(hexagons, arcs, nodes, bi_path, ros_path, fi_path, stats_path, grid_params, output_dir)
    build_graphs(burndataHex, ignHexChart, arcs, nodes, output_dir)

if __name__ == '__main__':
    main()



