#-------------------------------------------------------------------------------
# Name:        GraphFromDB
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys
import numpy as np
import sqlite3
from calendar import monthrange
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


from Utils import Select_continuos_periods

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

def main():

    NotErr=bool('True')
    msg='OK'

    dir_script=os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_script)

    config_input='Input_Setup.ini'
    config_input_location=os.path.realpath(config_input)
    configuration = configparser.ConfigParser()
    configuration.read(config_input_location)

    ProjectPath=configuration.get('globalOptions','ProjectPath')
    ProjectPath = os.path.realpath(ProjectPath)

    ProjectName=configuration.get('Input_par','ProjectName')

    # =================================
    # sqlite database name
    # =================================
    mydb='%s.sqlite' % ProjectName
    mydb_path=ProjectPath + os.sep +mydb

    mydb_path=os.path.realpath(mydb_path)

    if not os.path.exists(mydb_path):
        NotErr= bool()
        msg='file %s does not exists' % mydb_path
        return NotErr, msg


    # connect to sqlite database
    # =================================
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
##    conn = sqlite3.connect(mydb_path)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()

    table='RIVERBASIN'
    sql='SELECT description FROM %s' % table
    cur.execute(sql)
    record=cur.fetchone()
    Station_name=record[0]

    TableLegend='TSTYPES'

    sql='SELECT TSTYPE,TSCODE,unit,description FROM %s' % TableLegend
    cur.execute(sql)
    ListTSType=cur.fetchall()

    dic_TSType_desc={}
    dic_desc_TSType={}
    dic_TSType_unit={}
    dic_TSType_CODE={}

    for rec in ListTSType:
        dic_TSType_desc[rec[0]]=rec[3]
        dic_desc_TSType[rec[3]]=rec[0]
        dic_TSType_unit[rec[0]]=rec[2]
        dic_TSType_CODE[rec[0]]=rec[1]

    # Read TSTYPE
    # -----------------------------------------------
    table='TimeSeries'

    sql='SELECT DISTINCT TSTYPE FROM %s' % table
    sql+=' ORDER BY TSTYPE'
    sql+=';'
    cur.execute(sql)
    records_TSTYPE=cur.fetchall()

    List_mm=[]
    for rec in records_TSTYPE:
        if 'mm' in dic_TSType_unit[rec[0]]:
            List_mm.append(rec[0])

    List_Q=[]
    for rec in records_TSTYPE:
        if 'm3/s' in dic_TSType_unit[rec[0]]:
            List_Q.append(rec[0])

    # Graph mm
    # ---------------
    fig = figure(figsize=[18.0, 7.8])

    # Create the graph
    ax = fig.add_subplot(111)

    for TSTYPE in List_mm:

        sql='SELECT TSDate,value FROM %s' % table
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        ListTSTime=cur.fetchall()

        Date=[]
        Valori=[]
        for rec in ListTSTime:
            Date.append(rec[0])
##            Date.append(convert_to_date(rec[0]))
            Valori.append(rec[1])

        label_txt=dic_TSType_desc[TSTYPE]
        ax.plot(Date, Valori,'.-',label=label_txt, linewidth=0.5)

    ax.tick_params(axis='y', labelcolor='k')

    ax.set_ylabel('Y [mm]', fontsize=18)
    ax.set_xlabel('Date', fontsize=18)

    ax.autoscale_view()
    left, right = ax.get_xlim()

    ax.set_xlim(int(left), math.ceil(right))

    bottom, top = ax.get_ylim()
    majors=ax.yaxis.get_majorticklocs()
    deltay=majors[1]-majors[0]
    top_new=math.ceil(top/deltay)*deltay
    ax.set_ylim(0, top_new)

    titolo='River station: %s' % (Station_name)
    plt.title(titolo, fontsize=14)

    ax.xaxis.grid(True, 'major',color='k', linestyle='-', linewidth=0.5)
    ax.xaxis.grid(True, 'minor')
    ax.grid(True)
    ax.legend(fontsize=12, loc=2)

    show()


    # Graph m3/s
    # ---------------
    fig = figure(figsize=[18.0, 7.8])

    # Create the graph
    ax = fig.add_subplot(111)

    Nodata=-9999

    for TSTYPE in List_Q:

        if 'Obs' in dic_TSType_CODE[TSTYPE]:

            width=2.0

            color = 'red'
            label_txt_1=dic_TSType_desc[TSTYPE]

            # Select continuous periods of discharge observation
            QobsArray,dic_continuous_periods,Periods_array,period_max = Select_continuos_periods(cur)
            ii=0
            for key in dic_continuous_periods:
                mask=Periods_array==key
                Y1=QobsArray[mask]
                ii+=1
                if ii==1:
                    ax.plot(dic_continuous_periods[key],Y1,'.-',label=label_txt_1, linewidth=width, color=color)
                else:
                    ax.plot(dic_continuous_periods[key],Y1,'.-', linewidth=width, color=color)

        else:
            width=0.5

            sql='SELECT TSDate,value FROM %s' % table
            sql+=' WHERE TSTYPE=%d' % TSTYPE
            sql+=' ORDER BY TSDate'
            sql+=';'
            cur.execute(sql)
            ListTSTime=cur.fetchall()

            Date=[]
            Valori=[]
            for rec in ListTSTime:
                val=rec[1]
                if val!=Nodata:
                    Date.append(rec[0])
##                    Date.append(convert_to_date(rec[0]))
                    Valori.append(rec[1])

            label_txt=dic_TSType_desc[TSTYPE]

            ax.plot(Date, Valori,'.-',label=label_txt, linewidth=width)

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


    titolo='River station: %s' % (Station_name)
    plt.title(titolo, fontsize=14)

    ax.xaxis.grid(True, 'major',color='k', linestyle='-', linewidth=0.5)
    ax.xaxis.grid(True, 'minor')
    ax.grid(True)
    ax.legend(fontsize=12, loc=2)

    show()

    # Close connection with the database
    cur.close()
    conn.close()

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)
