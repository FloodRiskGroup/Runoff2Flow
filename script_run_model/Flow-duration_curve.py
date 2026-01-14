#-------------------------------------------------------------------------------
# Name:        Flow-Duration_curve
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys
import sqlite3
import numpy as np
import datetime
from datetime import timedelta, date
import math
import configparser

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.dates import DayLocator, HourLocator,MonthLocator, WeekdayLocator, DateFormatter
import matplotlib.dates as mdates
from pylab import figure, show
from pylab import *

from dateutil.parser import parse
##def convert_to_date(input_str, parserinfo=None):
##    return parse(input_str, parserinfo=parserinfo).date()
# to register a function for converting the Python object to int, long, float, str (UTF-8 encoded), unicode or buffer
def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())

sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_adapter(datetime, adapt_datetime_epoch)

# to register a function for converting text to the Python object.
# The input is always text because internally, sqlite stores everything as text.
def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return date.fromisoformat(val.decode())

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.fromtimestamp(int(val))

sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)

def Load_TimeSerieDateClima(cur,field,DataPrimaDate,DataUltimaDate):
    """
    extract the time series based on dates
    """
    testoSQL='SELECT TSDate,%s from TimeSeriesClima' %(field)
    testoSQL=testoSQL + " WHERE TSDate>='%s'" % DataPrimaDate
    testoSQL=testoSQL + " AND TSDate<='%s'" % DataUltimaDate
    testoSQL=testoSQL + " ORDER BY TSDate;"
    cur.execute(testoSQL)
    records = cur.fetchall()

    Date=[]
    Val=[]

    if records!=None:
        for rec in records:
            Date.append(rec[0])
##            Date.append(convert_to_date(rec[0]))
            Val.append(rec[1])

    return Date,Val


def Load_TimeSerieDate(cur,TSTypeID,DataPrimaDate,DataUltimaDate):
    """
    extract the time series based on dates
    """
    testoSQL='SELECT TSDate,value from TimeSeries WHERE TSTYPE=%s' %(TSTypeID)
    testoSQL=testoSQL + " AND TSDate>='%s'" % DataPrimaDate
    testoSQL=testoSQL + " AND TSDate<='%s'" % DataUltimaDate
    testoSQL=testoSQL + " ORDER BY TSDate;"
    cur.execute(testoSQL)
    records = cur.fetchall()

    Date=[]
    Val=[]

    if records!=None:
        for rec in records:
##            tsdatetime=rec[0]
##            date0 = datetime.datetime(int(tsdatetime[0:4]), int(int(tsdatetime[5:7])), int(int(tsdatetime[8:10])),int(tsdatetime[11:13]) )
            Date.append(rec[0])
##            Date.append(convert_to_date(rec[0]))
            Val.append(rec[1])

    return Date,Val

def Load_TimeSerieDate_ricostruite(cur,TSTypeID_obs,DataPrimaDate,DataUltimaDate,ListDate_cal,TSTypeID_calc):
    """
    extract the time series based on dates
    replaces the reconstructed values in case of missing observed data
    """

    Nodata=-999.0

    num_date_cal=len(ListDate_cal)

    testoSQL='SELECT TSDate,value from TimeSeries WHERE TSTYPE=%s' %(TSTypeID_obs)
    testoSQL+=" AND TSDate>='%s'" % DataPrimaDate
    testoSQL+=" AND TSDate<='%s'" % DataUltimaDate
    testoSQL+=" ORDER BY TSDate;"
    cur.execute(testoSQL)
    records = cur.fetchall()

    Date=[]
    Val=[]

    kk=0

    if len(records)>0:

        # case of no data observed on previous dates
        if records[0][0]>ListDate_cal[0][0]:

            ii=0
            date_cur=ListDate_cal[ii]

            while date_cur<records[0][0]:
                Date.append(date_cur)
                Val.append(Nodata)
                ii+=1
                date_cur=ListDate_cal[ii]

        # loading observed data
        for rec in records:
            Date.append(rec[0])
            Val.append(rec[1])

        # case of no data observed for subsequent dates
        if Date[-1]<ListDate_cal[-1][0]:

            ii=0
            date_cur=ListDate_cal[ii][0]
            while date_cur<=Date[-1]:
                ii+=1
                date_cur=ListDate_cal[ii][0]

            # insert no data for subsequent dates
            for jj in range(ii,num_date_cal):
                Date.append(ListDate_cal[jj][0])
                Val.append(Nodata)

        # case of data observed for dates subsequent to those calculated
        if  Date[-1]>ListDate_cal[-1][0]:
            ii=0
            date_cur=Date[ii]
            while date_cur<=ListDate_cal[-1][0]:
                ii+=1
                date_cur=Date[ii]
            kk=0
            while date_cur<Date[-1]:
                ii+=1
                kk+=1
                date_cur=Date[ii]

    else:

        testoSQL='SELECT TSDate,value from TimeSeries WHERE TSTYPE=%s' %(TSTypeID_calc)
        testoSQL+=" AND TSDate>='%s'" % DataPrimaDate
        testoSQL+=" AND TSDate<='%s'" % DataUltimaDate
        testoSQL+=" ORDER BY TSDate;"
        cur.execute(testoSQL)
        records = cur.fetchall()

        for rec in records:
            Date.append(rec[0])
            Val.append(rec[1])


    Val_array=np.array(Val)
    Date_array=np.array(Date)
    shape_Date=Date_array.shape

    nodata_mask= Val_array<0.0

    num=nodata_mask.sum()

    Date_array_nodata=Date_array[nodata_mask]
    shape_nodata=Date_array_nodata.shape

    Val_array_filled=np.copy(Val_array)


    if nodata_mask.sum()>0:

        testoSQL='SELECT TSDate,value from TimeSeries WHERE TSTYPE=%s' %(TSTypeID_calc)
        testoSQL+=" AND TSDate>='%s'" % DataPrimaDate
        testoSQL+=" AND TSDate<='%s'" % DataUltimaDate
        testoSQL+=" ORDER BY TSDate;"
        cur.execute(testoSQL)
        records = cur.fetchall()

        num_cal=len(records)
        num_array=len(Date)

        diff= num_array-num_cal-kk
##
##        delta=records[0][0]-DataPrimaDate
##        delta_mesi = int(delta.days/30)

        Date_cal=[]
        Val_cal=[]


        if records!=None:
            for i in range(diff):
                Date_cal.append(Date_array[i])
                Val_cal.append(Val_array[i])
            for rec in records:
                Date_cal.append(rec[0])
                Val_cal.append(rec[1])

        Val_array_cal=np.array(Val_cal)

        if Val_array_cal.shape[0] == Val_array.shape[0]:
            Val_array_filled[nodata_mask]=Val_array_cal[nodata_mask]

##    # convert to date
##    DateTime=[]
##    for dd in Date:
##        DateTime.append(convert_to_date(dd))
##
##
##    return DateTime,Val_array_filled,nodata_mask
    return Date,Val_array_filled,nodata_mask


def Cal_DurataMensile(serie):

    array=np.array(serie)
    shape=array.shape
    delta=int(shape[0] /12)
    resto = shape[0] % 12

    # array in descending order
    array_copy = np.sort(array)[::-1]

    num_dati=shape[0]
    curva=[]
    kk=0
    while kk<num_dati:
        curva.append(array_copy[kk])
        kk+=delta

    return curva

def GraficoQ(label_txt,Date,Valori):

    title='flows %s' % 'TAVAGNASCO DORA BALTEA_monthly %s %s' % (Date[0].strftime("%Y/%m/%d"),Date[-1].strftime("%Y/%m/%d"))

    # ---------------
    # Modified values
    fig = figure(figsize=[18.0, 7.8])

    title(title, fontsize=18)

    # Create the graph
    ax = fig.add_subplot(111)


##    label_txt=dic_TSType_desc[TSTypeID]
    ax.plot(Date, Valori,'.-',label=label_txt, linewidth=0.5)

    ax.tick_params(axis='y', labelcolor='k')

    ax.set_ylabel('Y [m3/s]', fontsize=18)
    ax.set_xlabel('Date', fontsize=18)

    ax.autoscale_view()
    left, right = ax.get_xlim()

    ax.set_xlim(int(left), math.ceil(right))

    bottom, top = ax.get_ylim()
    majors=ax.yaxis.get_majorticklocs()
    deltay=majors[1]-majors[0]
    top_new=math.ceil(top/deltay)*deltay
    ax.set_ylim(0, top_new)

    ax.xaxis.grid(True, 'major',color='k', linestyle='-', linewidth=0.5)
    ax.xaxis.grid(True, 'minor')
    ax.grid(True)
    ax.legend(fontsize=12, loc=2)

    show()

def main():


    NotErr=bool('True')
    msg='OK'

    dir_script=os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_script)

    config_input='calibration_settings.ini'
    config_input_location=os.path.realpath(config_input)
    configuration = configparser.ConfigParser()
    configuration.read(config_input_location)

    ProjectPath=configuration.get('globalOptions','ProjectPath')
    ProjectPath = os.path.realpath(ProjectPath)

    # input Project nome
    ProjectName = configuration.get('Input_par','ProjectName')
    mydb='%s.sqlite' % ProjectName
    mydb_path=ProjectPath + os.sep +mydb
    mydb_path=os.path.realpath(mydb_path)

    if not os.path.exists(mydb_path):
        NotErr= bool()
        msg='file %s does not exists' % mydb_path
        return NotErr, msg

    MainDir = configuration.get('out_img','MainDir')
    MainDir = os.path.realpath(MainDir)

    dir_out_img_results = configuration.get('out_img','dir_out_img_results')
    DirRes=MainDir + os.sep+ dir_out_img_results
    if not os.path.exists(DirRes):
        os.mkdir(DirRes)

    num_periods = int(configuration.get('flow_duration','num_periods'))

    # =================================
    # connect sqlite database
    # =================================
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
##    conn = sqlite3.connect(mydb_path)
    # =================================

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()


    TabellaLegenda='TSTYPES'

    sql='SELECT TSTYPE,TSCODE FROM %s' % TabellaLegenda
    cur.execute(sql)
    ListTSType=cur.fetchall()

    dic_TSType_desc={}
    dic_desc_TSType={}
    for rec in ListTSType:
        dic_TSType_desc[rec[0]]=rec[1]
        dic_desc_TSType[rec[1]]=rec[0]

    search='QTot_calc'
    TSTypeID=0
    for key in dic_desc_TSType:
        if search in key:
            TSTypeID=dic_desc_TSType[key]
            break

    # =========================================
    # Extract values
    # =========================================


    TimeTable='TimeSeries'

    # search for initial time series dates
    # ---------------------------------
    # Qobs
    search='QtotObs'
    TSTypeID_obs=0
    for key in dic_desc_TSType:
        if search in key:
            TSTypeID_obs=dic_desc_TSType[key]
            break

    sql='SELECT TSDate FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTypeID_obs
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListQ_runoff=cur.fetchall()
    date_ini_TimeSeries_obs = ListQ_runoff[0][0]
    date_end_TimeSeries_obs = ListQ_runoff[-1][0]
##    date_ini_TimeSeries_obs = convert_to_date(ListQ_runoff[0][0])
##    date_end_TimeSeries_obs = convert_to_date(ListQ_runoff[-1][0])

    # QTot_calc
    search='QTot_calc'
    TSTypeID_calc=0
    for key in dic_desc_TSType:
        if search in key:
            TSTypeID_calc=dic_desc_TSType[key]
            break

    sql='SELECT TSDate FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTypeID_calc
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListDate_cal=cur.fetchall()
    date_ini_TimeSeries_cal = ListDate_cal[0][0]
    date_end_TimeSeries_cal = ListDate_cal[-1][0]
##    date_ini_TimeSeries_cal = convert_to_date(ListDate_cal[0][0])
##    date_end_TimeSeries_cal = convert_to_date(ListDate_cal[-1][0])


    date_ini_TimeSeries = min(date_ini_TimeSeries_cal,date_ini_TimeSeries_obs)
    date_end_TimeSeries = max(date_end_TimeSeries_cal,date_end_TimeSeries_obs)

    num_years= date_end_TimeSeries.year-date_ini_TimeSeries.year+1

    delta_year=int(num_years/num_periods)

    periods_list=[]
    periods_list.append([date_ini_TimeSeries.year,date_ini_TimeSeries.year+delta_year-1])
    periods_list.append([date_ini_TimeSeries.year+delta_year,date_ini_TimeSeries.year+2*delta_year-1])
    periods_list.append([date_ini_TimeSeries.year+2*delta_year,date_end_TimeSeries.year])


    dic_periodo_curve={}

    dic_periodo_media={}

    lista_labels=[]

    for periodo in periods_list:

        DataPrimaDate=date(periodo[0],1,1)
        DataUltimaDate=date(periodo[1],12,31)

        # Load date calc
        sql='SELECT TSDate FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTypeID_calc
        sql+=" AND TSDate>='%s'" % DataPrimaDate
        sql+=" AND TSDate<='%s'" % DataUltimaDate
        sql+=" ORDER BY TSDate"
        sql+=';'
        cur.execute(sql)
        ListDate_cal=cur.fetchall()

        Date,Valori,nodata_mask = Load_TimeSerieDate_ricostruite(cur,TSTypeID_obs,DataPrimaDate,DataUltimaDate,ListDate_cal,TSTypeID_calc)

        label_cur='Period %d - %d' % (Date[0].year,Date[-1].year)

        lista_labels.append(label_cur)

        curva=Cal_DurataMensile(Valori)

        dic_periodo_curve[label_cur]=curva
        dic_periodo_media[label_cur]=Valori.mean()

    # create the graph
    fig = figure(figsize=[15.0, 7.8])
    ax = fig.add_subplot(111)

    for label_cur in dic_periodo_curve:
        curva=dic_periodo_curve[label_cur]
        x=np.arange(len(curva))+1
        plt.plot(x, curva,'.-' ,label = label_cur)


    # evaluates the average flow rate for the first period: possible choice for a historic hydroelectric plant
    media_1=dic_periodo_media[lista_labels[0]]
    curva_array=np.array(dic_periodo_curve[lista_labels[0]])
    curva_array_flip=np.flip(curva_array)
    x_flip=np.flip(x)

    x_interp=np.interp(media_1,curva_array_flip,x_flip)

##    xx=[x[0],x[-1]]
    xx=[x[0],x_interp]
    yy=[media_1,media_1]
    xx_utilizzo=[x[0],x_interp]
    yy_utilizzo=[media_1,media_1]
    ii=-1
    for xp in x:
        ii+=1
        if xp>x_interp:
            xx_utilizzo.append(xp)
            yy_utilizzo.append(dic_periodo_curve[lista_labels[0]][ii])


    label_media='Q average - %s' % (lista_labels[0])
    plt.plot(xx, yy,'.--' ,linewidth=2.0,label = label_media)
    label_utilizzo='Area of ​​use of hydroelectric plant for\nQ average - %s' % (lista_labels[0])
    plt.fill_between(xx_utilizzo, yy_utilizzo, alpha=0.2,label = label_utilizzo)

    titolo='Flow duration curve for historical periods'
    plt.title(titolo, fontsize=18)
    ax.set_ylabel('Q (m3/s)', fontsize=18)
    ax.set_xlabel('Duration [months]', fontsize=18)

    plt.legend()
    plt.grid()
    plt.show()



    save=1
    if save>0:
        NameFig='flow_duration_curve.png'
        FileOut=DirRes+os.sep+NameFig
        fig.savefig(FileOut,dpi=100,format='png')


    cur=None
    conn.close()



    # cerca
if __name__ == '__main__':


    main()
