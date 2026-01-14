#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      MANCUSI
#
# Created:     27/12/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import configparser
import platform

import os
import numpy as np
import math
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.dates import DayLocator, HourLocator,MonthLocator, WeekdayLocator, DateFormatter
import matplotlib.dates as mdates
from pylab import figure, show
from pylab import *

from sklearn.model_selection import TimeSeriesSplit

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

def Graph(ListaY,ListaLabels,Variabile,txt_param=None,Eff=None,RMSE_model=None,MAE_model=None,chk_vol=None,FileOut=None,EffVer=None,period_valid_verify=None,mask=None):

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

    ax.plot(X,Y1,'k-o', linewidth=2.5, label=Variabile[0])

    if len(ListaY)>1:
        X1 = np.arange(len(Y2))+1
        ax.plot(X1,Y2,'r--', linewidth=2.0, label=Variabile[1])
    if len(ListaY)>2:
        X2 = np.arange(len(Y3))+1
        ax.plot(X2,Y3,'--', linewidth=2.0, label=Variabile[2])

    ax.set_title(ListaLabels[0], fontsize=25)
    ax.set_xlabel(ListaLabels[1], fontsize=15)
    ax.set_ylabel(ListaLabels[2], fontsize=15)

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
    else:
        top=top+0.06

    if Eff!=None:
        top=top-0.06
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Nash–Sutcliffe efficency= %.3f' % (Eff)
        if EffVer!=None:
            label2+=' - Verify= %.3f' % (EffVer)
            if period_valid_verify!=None:
                label2+=' - from %s to %s' % (period_valid_verify[0],period_valid_verify[1])
            if mask!=None:
                try:
                    x_v=X[mask]
                    y_v=Y2[mask]
                    ax.scatter(x_v, y_v, 60, color='blue', label='Verify')
                except:
                    pass


        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    if RMSE_model!=None:
        top=top-0.06
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Root Mean Square Error= %.2f' % (RMSE_model)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)


    if MAE_model!=None:
        top=top-0.06
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Mean Absolute Error = %.2f' % (MAE_model)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)


    if chk_vol!=None:
        top=top-0.06
        bbox_props = dict(boxstyle="square", fc="cyan", ec="b", lw=2, alpha=0.6)
        label2='Estim. Vol. / Obs. Vol. = %.3f' % (chk_vol)
        ax.text(left, top, label2,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax.transAxes,
                size=textsize,
                bbox=bbox_props)

    ax.legend(loc='upper right')

    plt.show()


def Graph_Historical(cur,description):

    # Modified values
    fig = figure(figsize=[18.0, 7.8])

    # Create the graph
    ax = fig.add_subplot(111)

    title1='Historical streamflow : %s' % description
    title(title1, fontsize=18)


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

    DirFigureInput=configuration.get('globalOptions','DirFigureInput')
    DirFigureInput = os.path.realpath(DirFigureInput)


    # input LagTime
    SupFlowMaxLagTime = int(configuration.get('Input_par','SupFlowMaxLagTime'))
    BaseFlowMaxLagTime = int(configuration.get('Input_par','BaseFlowMaxLagTime'))

    DirFigureInput=configuration.get('globalOptions','DirFigureInput')
    DirFigureInput = os.path.realpath(DirFigureInput)

    if not os.path.exists(DirFigureInput):
        os.mkdir(DirFigureInput)

    save_fig_input= int(configuration.get('Input_par','save_fig_input'))

    # list projects
    Lista = os.listdir(ProjectPath)
    ProjectsID=[]
    for file in Lista:
        if file.endswith('.sqlite'):
            pp=file[:-7].split('_')
            ProjectsID.append(file)


    for mydb in ProjectsID:

        pp=mydb.split('.')
        ProgName=pp[0]

        mydb_path= ProjectPath + os.sep +mydb
        mydb_path=os.path.realpath(mydb_path)

         # open database
        # --------------
        conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        # select name river basin
        sql='SELECT description FROM RIVERBASIN;'
        cur.execute(sql)
        record=cur.fetchone()

        description=record[0]

        txt='river station: %s' % record[0]
        print(txt)


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
        List_date=cur.fetchall()

        date_ini_TimeSeries = List_date[0][0]

        MaxLag=max(SupFlowMaxLagTime,BaseFlowMaxLagTime)
        date_ini_TimeSeries=date_ini_TimeSeries+relativedelta(months=MaxLag)

        QobsArray,dic_periodi_continui,Periodi_array,periodo_max = Select_continuos_periods(cur,date_ini_TimeSeries)

        # load observed discharge
        # QtotObs m3/s
        TSTYPE=20
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % date_ini_TimeSeries
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        records=cur.fetchall()

        List_date_obs=[]
        List_Q_obs=[]
        Lista_mese=[]
        months_map = {}
        i=-1
        for rec in records:
            i+=1
            months_map[i]="{:04d}-{:02d}".format(rec[0].year,rec[0].month)
            List_date_obs.append(rec[0])
            Lista_mese.append(rec[0].month)
            List_Q_obs.append(rec[1])


        date_ini_TimeSeries_obs = List_date_obs[0]
        date_end_TimeSeries_obs = List_date_obs[-1]

        Date_array = np.array(List_date_obs)
        Q_obs_array = np.array(List_Q_obs)
        obs_data_mask = Q_obs_array > 0

        nn=len(Q_obs_array)
        seq=np.arange(nn)

        req_array = np.zeros(seq.shape)

        seq_mask = seq[obs_data_mask]

        months = np.array([months_map[ii] for ii in seq_mask])


        nn=len(Q_obs_array)
        num_data= obs_data_mask.sum()

        txt='num months observation period = %d\nnum data = %d\nnum_nodata = %d' % (nn,num_data,nn-num_data)
        print (txt)

        # DROP TABLE splitperiods
        Tableslipt='splitperiods'
        sql='DROP TABLE IF EXISTS %s' % Tableslipt
        cur.execute(sql)
        conn.commit()

        # CREATE TABLE
        sql='CREATE TABLE %s (PKUID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT' % Tableslipt
        sql+=', SplitID INTEGER'
        sql+=', TrainDateIni date'
        sql+=', TrainDateEnd date'
        sql+=', TestDateIni date'
        sql+=', TestDateEnd date'
        sql+=');'
        cur.execute(sql)
        conn.commit()

        # Create template insert
        _template='INSERT INTO %s (' % Tableslipt
        _template+='SplitID,TrainDateIni,TrainDateEnd'
        _template+=',TestDateIni,TestDateEnd'
        _template+=') VALUES ('
        num_field=5
        newholder=''
        for i in range(num_field):
            newholder+='?,'
        newholder=newholder[:-1]
        _template+='%s)' % newholder
        _template+=';'


        X=seq_mask
        tscv = TimeSeriesSplit(n_splits=2)
        sp=0
        for train, test in tscv.split(X):

            record_insert=[]

            sp+=1

            # save SplitID
            record_insert.append(sp)

            # Modified values
            fig = figure(figsize=[18.0, 7.8])

            # Create plot
            ax = fig.add_subplot(111)

            Titolo1='Historical streamflow : %s - split %d' % (description,sp)
            title(Titolo1, fontsize=18)

            color = 'black'
            label_txt_1='Q obs'
            ii=0
            for key in dic_periodi_continui:
                mask=Periodi_array==key
                Y1=QobsArray[mask]
                ii+=1
                if ii==1:
                    ax.plot(dic_periodi_continui[key],Y1,'.-',label=label_txt_1, linewidth=0.5, color=color)
                else:
                    ax.plot(dic_periodi_continui[key],Y1,'.-', linewidth=0.5, color=color)

            # Train
            # --------------------------
            color = 'tab:red'
            label_txt_1='Q Train'
            ax.plot(Date_array[X[train]], Q_obs_array[X[train]],'o',label=label_txt_1, linewidth=1.5, color=color)

            # Save Train Ini - End date
            record_insert.append(Date_array[X[train]][0])
            record_insert.append(Date_array[X[train]][-1])


            # Test
            # --------------------------
            color = 'blue'
            label_txt_1='Q Test'
            ax.plot(Date_array[X[test]], Q_obs_array[X[test]],'*',label=label_txt_1, linewidth=1.5, color=color)

            # Save Test Ini - End date
            record_insert.append(Date_array[X[test]][0])
            record_insert.append(Date_array[X[test]][-1])

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

            if save_fig_input>0:
                NameFig='$s_%d.png' % (ProgName,sp)
                fig_file=DirFigureInput+os.sep+NameFig
                fig.savefig(fig_file, dpi=150, format='png')
            else:
                show()


            # Save date in db
            cur.execute(_template,record_insert)
            conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)