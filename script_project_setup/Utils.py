#-------------------------------------------------------------------------------
# Name:        Utils
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import configparser

from functools import reduce
from operator import add

import numpy as np
import math
import os, sys
import csv
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from dateutil.parser import parse

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

def Select_continuos_periods(cur):

    # Time Series Table
    TimeTable='TimeSeries'

    # Qtot Observed
    TSTYPE=20
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListaQobs=cur.fetchall()

    DataIniObs=ListaQobs[0][0]
    DataFinObs=ListaQobs[-1][0]
##    DataIniObs=convert_to_date(ListaQobs[0][0])
##    DataFinObs=convert_to_date(ListaQobs[-1][0])

    Qobs_series=[]
    dic_continuous_periods={}
    period=1
    start_period=bool()
    Periods_list=[]

    Nodata_date_list=[]

    for rec in ListaQobs:
        if rec[1]>0:
            Periods_list.append(period)
            if not start_period:
                start_period=bool('True')
                lista_date_period=[]
                lista_date_period.append(rec[0])
##                lista_date_period.append(convert_to_date(rec[0]))
            else:
                lista_date_period.append(rec[0])
##                lista_date_period.append(convert_to_date(rec[0]))
        else:
            Periods_list.append(-1)
            Nodata_date_list.append(rec[0])
##            Nodata_date_list.append(convert_to_date(rec[0]))
            if start_period:
                dic_continuous_periods[period]=lista_date_period
                period+=1
                start_period=bool()

        Qobs_series.append(rec[1])
    if start_period:
        dic_continuous_periods[period]=lista_date_period

    Periods_array=np.array(Periods_list)
    QobsArray=np.array(Qobs_series)

    mask_nodata=QobsArray<0

    Periodi_num_mesi={}
    num_max=0
    for key in dic_continuous_periods:
        nn=len(dic_continuous_periods[key])
        if nn>num_max:
            period_max=key
            num_max=nn*1
        Periodi_num_mesi[key]=nn

    return QobsArray,dic_continuous_periods,Periods_array,period_max

def main():

    pass

if __name__ == '__main__':
    main()
