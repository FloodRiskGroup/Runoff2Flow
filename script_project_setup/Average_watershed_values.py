#-------------------------------------------------------------------------------
# Name:        Average_watershed_values
# Purpose:
#
# Author:      MANCUSI
#
# Created:     04/04/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys
import osgeo
import matplotlib.pyplot as plt
import geopandas as gpd
try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
    from osgeo import ogr
except ImportError:
    import gdal
    import ogr
    from gdalconst import *

# Import spatial reference systems
try:
    from osgeo import osr
except ImportError:
    import osr

import configparser

import netCDF4 as nc
from netCDF4 import Dataset
import numpy as np

import time as timeclok


def CreaDataSourceMEM(array, Nodata, gt, prj, type=GDT_Float32):
    """
    Create in-memory GDAL raster dataset from numpy array.
    Used to avoid disk I/O during watershed extraction workflow.
    
    Parameters:
    - array: 2D numpy data matrix
    - Nodata: no-data value marker in array
    - gt: geotransformation [x_min, pixel_width, 0, y_max, 0, -pixel_height]
    - prj: WKT projection/coordinate reference system string
    - type: GDAL data type (default GDT_Float32 for climate data)
    """

    format = 'MEM'
##    type = GDT_Float32
    #type = GDT_Int16
    #type = GDT_Int32

    driver3 = gdal.GetDriverByName(format)
    driver3.Register()

    file_tmp='tmp.tif'

    # read the two dimensions of the data matrix
    rows,cols =array.shape

    ds = driver3.Create(file_tmp, cols, rows, 1, type)
    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        ds.SetGeoTransform(gt)

    # set the geographic reference system
    if prj is not None and len(prj) > 0:
        ds.SetProjection(prj)
##    else:
##        prj= inSpatialRef.ExportToWkt()
##        ds.SetProjection(prj)
    iBand=1
    outband = ds.GetRasterBand(iBand)
    outband.WriteArray(array, 0, 0)
    outband.FlushCache()
    outband.SetNoDataValue(Nodata)
    outband.GetStatistics(0,1)

    return ds

def Make_polygon_layer(poly_wkt,outSpatialRef):

    """
    Create a polygon layer in memory
    """

    driver=ogr.GetDriverByName('MEM')

    memds_poly=driver.CreateDataSource('memds_poly')
    lyr_poly=memds_poly.CreateLayer('polygon', geom_type=ogr.wkbPolygon, srs=outSpatialRef)
    idField_poly = ogr.FieldDefn("id", ogr.OFTInteger)
    lyr_poly.CreateField(idField_poly)
    feat_poly = ogr.Feature(lyr_poly.GetLayerDefn())
    feat_poly.SetField("id", 1)
    poly_area=ogr.CreateGeometryFromWkt(poly_wkt)
    feat_poly.SetGeometry(poly_area)
    lyr_poly.CreateFeature(feat_poly)

    AttrOption='ATTRIBUTE=id'

    return memds_poly,lyr_poly, AttrOption

def Make_raster_from_vect_layer(cols, rows, gt, prj, lyr, AttrOption, type=GDT_Int16):
    """
    Rasterize vector polygon layer to binary mask grid.
    Creates watershed mask for extraction/averaging of NetCDF climate data.
    """
    

    driver3 = gdal.GetDriverByName("MEM")
    driver3.Register()

    ds_tmp = driver3.Create('vector.tif', cols, rows, 1, type)

    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        ds_tmp.SetGeoTransform(gt)

    # sets the reference system
    if prj is not None and len(prj) > 0:
        ds_tmp.SetProjection(prj)

    # Rasterize
    iBand=1
    outband = ds_tmp.GetRasterBand(iBand)

    # Rasterize
    err = gdal.RasterizeLayer(ds_tmp, [1], lyr,
            burn_values=[0],
            options=[AttrOption])
    if err != 0:
        raise Exception("error rasterizing layer: %s" % err)

    raster_array = outband.ReadAsArray()
    outband.FlushCache()
    outband=None
    ds_tmp=None

    return raster_array

def Calc_MeanValues_from_NetCDF(nc_file,wkt_poligon,OriginEPSG):

    NotErr=bool('True')
    msg='OK'

    Mean_value_List=[]
    varname = 'unknown'

    # open NecCDF
    fh = Dataset(nc_file, mode='r')

    # retrieve dimensions,  atributes, variables, and missing value
    dimensions = fh.dimensions.copy()
    variables  =  fh.variables.copy()
    attributes = fh.__dict__.copy()

    varsInFile = fh.variables.keys()

    calendar_used = {}
    variableName = None

    #-set new values
    Var_dimensions_list=[]
    for key in list(dimensions.keys()):
        if 'lat' in key.lower() or 'y' == key:
            latVar= key
            Var_dimensions_list.append(key)
        elif 'lon' in key.lower() or 'x'==key:
            lonVar= key
            Var_dimensions_list.append(key)
        elif 'time' in key.lower():
            timeVar=key
            Var_dimensions_list.append(key)
        else:
            Var_dimensions_list.append(key)

    # extract lat/lon values (in degrees) to numpy arrays
    latitude, longitude = fh.variables[latVar], fh.variables[lonVar]
    latvals = latitude[:]; lonvals = longitude[:]

    latShape=latitude.shape
    lonShape=longitude.shape

    xcount=lonShape[0]
    ycount=latShape[0]

    pixelWidth=(lonvals.max()-lonvals.min())/(lonShape[0]-1)
    pixelHeight=(latvals.min()-latvals.max())/(latShape[0]-1)

    originX=lonvals[0]-pixelWidth/2.0
    originY=latvals[0]-pixelHeight/2.0

    gt=[]
    gt.append(originX)
    gt.append(pixelWidth)
    gt.append(0)
    gt.append(originY)
    gt.append(0)
    gt.append(pixelHeight)


    Variables_name=[]
    for key in list(varsInFile):
        if not key in Var_dimensions_list:
            Variables_name.append(key)

    # Variable value
    # .................................
    # assume to read the first variable
    # .................................
    varname=Variables_name[0]
    Var_vals_ref = variables[varname]


    # Time values
    # --------------
    time_var = fh.variables[timeVar]

    # get values
    nctime = fh.variables[timeVar]

    dates = nc.num2date(nctime, units = nctime.units, calendar=nctime.calendar,
                      only_use_cftime_datetimes=False,
                      only_use_python_datetimes=True)

    try:
        grid_mapping= Var_vals_ref.grid_mapping
        georef= variables[grid_mapping]
        spatial_ref_str=georef.spatial_ref
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromWkt(spatial_ref_str)
        # looking for the code of the reference system
        outSpatialRef.AutoIdentifyEPSG()
        TargetEPSG= outSpatialRef.GetAuthorityCode(None)
        prj = outSpatialRef.ExportToProj4()

    except:
        msg='Warning no spatialRef in %s' % nc_file
        msg+='\nmake sure the polygon in %s' % InputPolygonFile
        msg+='\nis in the same reference system'
        print( msg)
        TargetEPSG= None
        prj=None
        pass

    if TargetEPSG!=None and OriginEPSG!=None:

        inSpatialRef=osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(int(OriginEPSG))

        # compatibility with older versions of GDAL
        if int(osgeo.__version__[0]) >= 3:
            # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
            outSpatialRef.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
            inSpatialRef.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

        if TargetEPSG!=OriginEPSG:
            coordTrans = osr.CoordinateTransformation(inSpatialRef,outSpatialRef)
            To_transf=bool('True')
        else:
            To_transf=bool()
    else:
        To_transf=bool()

    # Create mask of polygon
    # ----------------------
    if To_transf:
        geom=ogr.CreateGeometryFromWkt(wkt_poligon)
        geom.Transform(coordTrans)
        wkt_geom = geom.ExportToWkt()
    else:
        wkt_geom=wkt_poligon

    memds_poly,lyr_poly, AttrOption = Make_polygon_layer(wkt_geom,outSpatialRef)

    grid_poly = Make_raster_from_vect_layer(xcount,ycount,gt,prj,lyr_poly,AttrOption)

    lyr_poly = None
    memds_poly = None

    mask_nodata_zona=grid_poly==0
    mask_data_zona=grid_poly>0

    num_pixel=mask_data_zona.sum()

    if num_pixel>0:

        ii=-1

        for date in dates:
            ii+=1
            # read raster
            vals=Var_vals_ref[ii,:,:]
            AverageValue= np.average(vals, weights=mask_data_zona)

            Mean_value_List.append([date.strftime("%Y-%m-%d"),AverageValue])

    return Mean_value_List,varname,msg

def SaveAverageResults(file_out,Mean_value_List,varname):

    NotErr=bool('True')
    errMsg='OK'

    fout=open(file_out,'w')

    sep=','
    txt='Date%s%s\n' % (sep,varname)
    fout.write(txt)

    for rec in Mean_value_List:
        txt='%s' % rec[0]
        txt+=sep
        txt+='%s' % rec[1]
        txt+='\n'
        fout.write(txt)
    fout.close()

    return NotErr,errMsg

def main():

    dic_type = {'POINT':1, 'LINESTRING':2, 'POLYGON':3, 'MULIPOINT':4, 'MULTILINESTRING':5, 'MULTIPOLYGON':6}

    start_time = timeclok.time()


    NotErr=bool('True')
    msg='OK'

    dir_script=os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_script)

    ogr.UseExceptions()

    config_input='Input_Setup.ini'
    config_input_location=os.path.realpath(config_input)
    configuration = configparser.ConfigParser()
    configuration.read(config_input_location)

    MainDirInput=configuration.get('globalOptions','MainDirInput')
    MainDirInput = os.path.realpath(MainDirInput)

    MainDirOutput=configuration.get('globalOptions','MainDirOutput')
    MainDirOutput = os.path.realpath(MainDirOutput)

    if not os.path.exists(MainDirOutput):
        os.mkdir(MainDirOutput)

    InputPolygonFile=configuration.get('input_data','InputPolygonFile')
    InputPolygonFile =MainDirInput + os.sep + InputPolygonFile

    if not os.path.exists(InputPolygonFile):
        NotErr= bool()
        msg='file %s does not exists' % InputPolygonFile
        return NotErr, msg

    surface_runoff=configuration.get('input_data','surface_runoff')
    surface_runoff = MainDirInput + os.sep +surface_runoff

    if not os.path.exists(surface_runoff):
        NotErr= bool()
        msg='file %s does not exists' % surface_runoff
        return NotErr, msg

    groundwater_recharge=configuration.get('input_data','groundwater_recharge')
    groundwater_recharge = MainDirInput + os.sep +groundwater_recharge

    if not os.path.exists(groundwater_recharge):
        NotErr= bool()
        msg='file %s does not exists' % groundwater_recharge
        return NotErr, msg

    # load output filename
    surface_runoff_csv=configuration.get('output','surface_runoff_csv')
    surface_runoff_csv = MainDirOutput + os.sep +surface_runoff_csv

    groundwater_recharge_csv=configuration.get('output','groundwater_recharge_csv')
    groundwater_recharge_csv = MainDirOutput + os.sep +groundwater_recharge_csv


    # open catchment file
    dataSource = ogr.Open(InputPolygonFile)
    layer = dataSource.GetLayer()
    LayerName=layer.GetName()
    inSpatialRef = layer.GetSpatialRef()
    # looking for the code of the reference system
    inSpatialRef.AutoIdentifyEPSG()
    OriginEPSG= inSpatialRef.GetAuthorityCode(None)

    num=layer.GetFeatureCount()
    f = layer.GetNextFeature()
    geom = f.GetGeometryRef()
    Type=geom.GetGeometryType()
    if Type==3:
        # case POLYGON
        geom.FlattenTo2D()
        wkt_poligon=geom.ExportToWkt()
        dataSource= None
    elif Type==6:
        # case MULTIPOLYGON
        geom.FlattenTo2D()
        # search for maximum area
        Area_max=0.0
        for i in range(0, geom.GetGeometryCount()):
            g = geom.GetGeometryRef(i)
            Area=g.GetArea()
            if Area> Area_max:
                wkt_poligon=g.ExportToWkt()
                Area_max= Area

        dataSource= None
    else:
        dataSource= None
        NotErr= bool()
        msg='no poligon in file %s ' % InputPolygonFile
        return NotErr, msg


    # plot
    fig, ax = plt.subplots()
    vector_map = gpd.GeoSeries.from_wkt([wkt_poligon])
    vector_map.plot(ax=ax, edgecolor="black", facecolor="None")
    titolo='Poligon layer: %s' % (LayerName)
    fig.suptitle(titolo, fontsize=14)

    plt.show()

    # Mean surface runoff
    # ----------------------------------
    nc_file=surface_runoff

    Mean_value_List,varname,msg = Calc_MeanValues_from_NetCDF(nc_file,wkt_poligon,OriginEPSG)

    file_out = surface_runoff_csv

    NotErr,msg =SaveAverageResults(file_out,Mean_value_List,varname)

    txt='Saved file: %s' % file_out
    print (txt)

    # Mean Recharge
    # ----------------------------------
    nc_file=groundwater_recharge

    Mean_value_List,varname,msg = Calc_MeanValues_from_NetCDF(nc_file,wkt_poligon,OriginEPSG)

    file_out = groundwater_recharge_csv

    NotErr,msg =SaveAverageResults(file_out,Mean_value_List,varname)

    txt='Saved file: %s' % file_out
    print (txt)

    return NotErr, msg


if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)
