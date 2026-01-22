#-------------------------------------------------------------------------------
# Name:        Model_IUH_NASH
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""
Istantaneus Unit Hydrograph of Nash
"""
import configparser

from Model_IUH_NASH_LinearRes import IUH_NASH_LinearRes
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.dates import DayLocator, HourLocator,MonthLocator, WeekdayLocator, DateFormatter
import matplotlib.dates as mdates
from pylab import figure, show
from pylab import *

import statsmodels.api as sm

from scipy.special import gamma
from functools import reduce
from operator import add

import numpy as np
import math
from sklearn.metrics import mean_absolute_error
import os, sys
import csv
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from dateutil.parser import parse
##def convert_to_date(input_str, parserinfo=None):
##    return parse(input_str, parserinfo=parserinfo).date()


# SQLite date/datetime adapters: Python object -> SQLite text
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

# SQLite date/datetime converters: SQLite text -> Python object
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

from Utils import Select_continuos_periods


def Trend_Line(YY):
    """
    Calculate the trend line of the YY vector
    """
    nn=len(YY)
    XX=np.arange(nn)
    vectuno=np.ones(nn)
    # Take a sequence of arrays and stack them vertically to make a single array
    A1=np.vstack([XX, vectuno])
    # Permute the dimensions of an array
    A = A1.T
    # Return the least-squares solution to a linear matrix equation
    m, c = np.linalg.lstsq(A, YY, rcond=None)[0]
    ydata= m*XX + c

    return ydata

def lowess_interp(y):

    lowess = sm.nonparametric.lowess
    x=np.arange(len(y))
    w = lowess(y, x, frac=1./3)
    wt=w.T

    return wt[1]

def Graph(ListaY,ListaLabels,Variabile,txt_param=None,Eff=None,RMSE_model=None,chk_vol=None,FileOut=None):


    fig = plt.figure(figsize=[15, 7.8])

    # Create a new subplot from a grid of 1x1
    ax = fig.add_subplot(111)

    Y1=np.array(ListaY[0])
    if len(ListaY)>1:
        Y2=np.array(ListaY[1])
    if len(ListaY)>2:
        Y3=np.array(ListaY[2])
    X = np.arange(len(Y1))+1
    # Setting limits
    if len(ListaY)==1:
        yy_min=Y1.min()
        yy_max=Y1.max()
    elif len(ListaY)==2:
        yy_min=min(Y1.min(),Y2.min())
        yy_max=max(Y1.max(),Y2.max())
    elif len(ListaY)==3:
        yy_min=min(Y1.min(),Y2.min(),Y3.min())
        yy_max=max(Y1.max(),Y2.max(),Y3.max())
    else:
        yy_min=Y1.min()
        yy_max=Y1.max()

    plt.ylim(yy_min * 0.9, yy_max.max() * 1.1)

    ax.plot(X,Y1,'k.-', linewidth=1.1, label=Variabile[0])

    if len(ListaY)>1:
        X1 = np.arange(len(Y2))+1
        ax.plot(X1,Y2,'r--', linewidth=1.0, label=Variabile[1])
    if len(ListaY)>2:
        X2 = np.arange(len(Y3))+1
        ax.plot(X2,Y3,'--', linewidth=1.0, label=Variabile[2])

    ax.set_title(ListaLabels[0], fontsize=25)
    ax.set_xlabel(ListaLabels[1], fontsize=15)
    ax.set_ylabel(ListaLabels[2], fontsize=15)

    ax.legend(loc='upper right')

    ax.grid(True)

    left=0.01
    top=0.98
    textsize=12

    if txt_param!=None:
        bbox_props = dict(boxstyle="square", fc="lime", ec="b", lw=2, alpha=0.6)
        ax.text(left, top, txt_param,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    top=top-0.06

    if Eff!=None:
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Nash–Sutcliffe efficency= %.3f' % (Eff)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    top=top-0.06

    if RMSE_model!=None:
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Root Mean Square Error= %.2f' % (RMSE_model)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    top=top-0.06

    if chk_vol!=None:
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Estim. Vol. / Obs. Vol. = %.3f' % (chk_vol)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    plt.show()

    if FileOut!=None:
        fig.savefig(FileOut,dpi=150,format='png')

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

    # open database
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()

    TableNameBasin='RIVERBASIN'
    sql='SELECT A_kmq,description FROM %s;' % TableNameBasin
    cur.execute(sql)
    ListArea=cur.fetchall()
    AreaSup=ListArea[0][0]
    description=ListArea[0][1]

    # ------------------------------------------------------------------------------------------------
    # coefficients for calculating volumes in Millions of cm
    # ------------------------------------------------------------------------------------------------
    #  mm*10^-3 (cm rain at mq nel in the month) * A_kmq*10^6 (area in mq) * 10^-6 (transformation into Millions cm)
    C_mm_Vol=AreaSup/1000.0
    # num_dys * 86400 (seconds in the month) * 10^-6 (transformation into Millions cm)
    C_Q_Vol=86400/1000000.0

    # input LagTime
    SupFlowMaxLagTime = int(configuration.get('Input_par','SupFlowMaxLagTime'))
    BaseFlowMaxLagTime = int(configuration.get('Input_par','BaseFlowMaxLagTime'))

    # Load target QtotObs m3/s - TSTYPE=20

    TimeTable='TimeSeries'

    # search for date_ini_TimeSeries
    # ------------------------------
    # Q_reach m3/s
    TSTYPE=12
    sql='SELECT TSDate FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    List_datef=cur.fetchall()
    date_ini_TimeSeries = List_datef[0][0]
    date_end_TimeSeries = List_datef[-1][0]

    MaxLag=max(SupFlowMaxLagTime,BaseFlowMaxLagTime)
    date_ini_TimeSeries=date_ini_TimeSeries+relativedelta(months=MaxLag)


    # Qtot Observed
    TSTYPE=20
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=" AND value>0.0"
    sql+=" AND TSDate>='%s'" % (date_ini_TimeSeries)
    sql+=" AND TSDate<='%s'" % (date_end_TimeSeries)
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListTargetQTOT=cur.fetchall()
    nn=len(ListTargetQTOT)/12

    # List of observed discharge and dates
    Qtot_obs=[]
    ListaDateObs=[]
    for rec in ListTargetQTOT:
        ListaDateObs.append(rec[0])
        Qtot_obs.append(rec[1])

    # Q_runoff m3/s
    TSTYPE=11
    # read including the 6 previous months
    data_ini_runoff=date_ini_TimeSeries+relativedelta(months=-SupFlowMaxLagTime)
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=" AND TSDate>='%s'" % (data_ini_runoff)
    sql+=" AND TSDate<='%s'" % (date_end_TimeSeries)
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListQ_runoff=cur.fetchall()
    num_dati=len(ListQ_runoff)


    nn1=len(ListQ_runoff)/12
    Q_runoff=[]
    for rec in ListQ_runoff:
        num_dys=monthrange(rec[0].year,rec[0].month)[1]
        Q_runoff.append(rec[1])
    Q_runoffArray=np.array(Q_runoff)

    # lista date
    ListaDateStorico=[]
    for ii in range(SupFlowMaxLagTime,num_dati):
        ListaDateStorico.append(ListQ_runoff[ii][0])

    # Q_reach m3/s
    TSTYPE=12
    # read with the 12 previous months
    data_ini_reac=date_ini_TimeSeries+relativedelta(months=-BaseFlowMaxLagTime)
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=" AND TSDate>='%s'" % (data_ini_reac)
    sql+=" AND TSDate<='%s'" % (date_end_TimeSeries)
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListQ_reach=cur.fetchall()
    nn2=len(ListQ_reach)/12
    Q_reach=[]
    for rec in ListQ_reach:
        Q_reach.append(rec[1])
    Q_reachArray=np.array(Q_reach)

    dic_param={}
    dic_param['AreaSup']=AreaSup
    dic_param['Q_runoff']=Q_runoffArray
    dic_param['Q_reach']=Q_reachArray

    dic_param['PreviousMonths']=BaseFlowMaxLagTime


    table='RIVERBASIN'

    sql='SELECT phi,k,n,phi_sup,k_sup FROM %s;' % table
    cur.execute(sql)
    ListValues=cur.fetchone()


    # ====================================
    # Initialize the parameter list
    # ====================================
    p=[]

    # -------------------------------
    # Nash model groundwater part
    # ------------------------------- 

    # phi: ratio between surface and groundwater basin area
    i_par=0
    p.append(ListValues[i_par])

    # k Coefficient : depletion constant of the Nash groundwater model
    i_par+=1
    p.append(ListValues[i_par])

    # N : Number of linear reservoirs in series of the Nash groundwater model
    i_par+=1
    p.append(ListValues[i_par])

    # -----------------------------------------
    # Linear Reservoir Model surface part
    # -----------------------------------------
    i_par+=1
    p.append(ListValues[i_par])

    # k_sup Coefficient: depletion constant of surface Nash model
    i_par+=1
    p.append(ListValues[i_par])

    Model=IUH_NASH_LinearRes(ProjectName,ProjectPath,dic_param,p)

    Model.Run()


    save=1
    if save>0:
        # save the calculated streamflow data
        # --------------------------------------
        TimeTable='TimeSeries'
        sql="PRAGMA table_info(%s);" % TimeTable
        cur.execute(sql)
        data = cur.fetchall()

        Campi_type={}
        Campi_notnull={}
        Campi_pk={}
        for rec in data:
            Campi_type[rec[1]]=rec[2]
            Campi_notnull[rec[1]]=rec[3]
            Campi_pk[rec[1]]=rec[5]

        Lista_campi_upload=[]
        for key in Campi_pk:
            Lista_campi_upload.append(key)


        # Build SQL INSERT template for uploading discharge time series
        # ---------------------------------------------------------------
        _template='INSERT INTO %s (' % TimeTable
        for field in Lista_campi_upload:
            _template+='%s, ' % field
        _template='%s) VALUES (' % _template[:-2]

        num_field=len(Lista_campi_upload)
        newholder=''
        for i in range(num_field):
            newholder+='?,'
        newholder=newholder[:-1]
        _template+='%s)' % newholder
        _template+=';'



        # QTot_calc m3/s
        TSTYPE=23
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % (ListaDateStorico[0])
        sql+=" AND TSDate<='%s'" % (ListaDateStorico[-1])
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        ListQTot_calc=cur.fetchall()


        if len(ListQTot_calc)>0:
            # update the data assuming they are continuous with dates
            ii=-1
            for rec in ListQTot_calc:
                ii+=1
                Qcal=Model.QtotCalc[ii]
                data_cur=rec[0]
                sql='UPDATE %s ' % TimeTable
                sql+=' SET value=%.2f' % Qcal
                sql+=' WHERE TSTYPE=%d' % TSTYPE
                sql+= " AND TSDate>='%s'" % (data_cur)
                sql+= " AND TSDate<='%s'" % (data_cur)
                sql+=''
                cur.execute(sql)
            conn.commit()
            print('Update', 'QTot_calc m3/s')
        else:
            # load new data (TSTYPE,TSDate,value)
            rows=[]
            for ii in range(len(ListaDateStorico)):
                record=[]
                record.append(TSTYPE)
                record.append(ListaDateStorico[ii])
                record.append(Model.QtotCalc[ii])
                rows.append(record)

            for row in rows:
                cur.execute(_template,row)
            conn.commit()
            print('Upload', 'QTot_calc m3/s')


    # Modified values
    fig = figure(figsize=[18.0, 7.8])

    # Create the graph
    ax = fig.add_subplot(111)

    title1='Historical streamflow : %s' % description
    title(title1, fontsize=18)

    # Historical discharge rates
    # --------------------------
    color = 'tab:blue'
    label_txt_1='Q calc'
    ax.plot(ListaDateStorico, Model.QtotCalc,'.-',label=label_txt_1, linewidth=0.5, color=color)

    # calculate trend line for historical data
    color = 'navy'
    ydata=Trend_Line(Model.QtotCalc)
    label_txt='Trend line %s' % label_txt_1
    ax.plot(ListaDateStorico, ydata,'-',label=label_txt, linewidth=3.0, color=color)

    # calculate lowess interpolation line
    color = 'green'
    wt=lowess_interp(Model.QtotCalc)
    label_txt='Locally weighted smoothing %s' % label_txt_1
    ax.plot(ListaDateStorico, wt,'--',label=label_txt, linewidth=3.0, color=color)


    color = 'red'
    label_txt_1='Q obs'
    QobsArray,dic_periodi_continui,Periodi_array,periodo_max = Select_continuos_periods(cur)
    ii=0
    for key in dic_periodi_continui:
        mask=Periodi_array==key
        Y1=QobsArray[mask]
        ii+=1
        if ii==1:
            ax.plot(dic_periodi_continui[key],Y1,'.-',label=label_txt_1, linewidth=0.5, color=color)
        else:
            ax.plot(dic_periodi_continui[key],Y1,'.-', linewidth=0.5, color=color)

    ax.tick_params(axis='y', labelcolor='k')

    ax.set_ylabel('Q (m3/s)', fontsize=18)
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

    save=1
    if save>0:
        NameFig='Graph_Discharge_periods.png'
        FileOut=DirRes+os.sep+NameFig
        fig.savefig(FileOut,dpi=100,format='png')

    # Close communication with the database
    cur.close()
    conn.close()


    return NotErr, msg

if __name__ == '__main__':
    NotErr, msg = main()
    print(msg)
