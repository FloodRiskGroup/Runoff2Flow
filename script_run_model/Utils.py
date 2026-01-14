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

def Select_continuos_periods(cur,DataStartObs=None):

    # Time Series Table
    TimeTable='TimeSeries'

    # Qtot Observed
    TSTYPE=20
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    if DataStartObs!=None:
        sql+=" AND TSDate>='%s'" % DataStartObs
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListaQobs=cur.fetchall()

    DataIniObs=ListaQobs[0][0]
    DataFinObs=ListaQobs[-1][0]

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
            else:
                lista_date_period.append(rec[0])
        else:
            Periods_list.append(-1)
            Nodata_date_list.append(rec[0])
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

def UpdateParameters(mydb_path, bestattempt=-2, Eff_theshold=0.7):
    """
    Update best calibration parameters to RIVERBASIN table.
    
    bestattempt: -2=auto-select best (default), -1=average all attempts, N=use attempt N
    Eff_theshold: Minimum Nash-Sutcliffe Efficiency for averaging strategy
    """

    ListParam = []
    bestattempt_val =-9
    BestSplit = -1

    # Database connenction
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()

    if bestattempt==-2:

        sql='SELECT attempt,Eff,Eff_verif FROM Attempt'
        sql+=';'
        cur.execute(sql)
        ListParam=cur.fetchall()
        if len(ListParam)>0:
            attempts=[]
            values=[]
            for rec in ListParam:
                attempts.append(rec[0])
                val=rec[1]*rec[2]
                values.append(val)
            values_array = np.array(values)
            ii = np.argmax(values_array)
            bestattempt_val = attempts[ii]

            # clean
            sql='UPDATE Attempt SET Best=0;'
            cur.execute(sql)
            conn.commit()

            # set best
            sql='UPDATE Attempt SET Best=1'
            sql+=' WHERE attempt=%d' % bestattempt_val
            sql+=';'
            cur.execute(sql)
            conn.commit()


            sql='SELECT phi,k,n,phi_sup,k_sup FROM Attempt'
            sql+=' WHERE attempt=%d' % bestattempt_val
            cur.execute(sql)
            ListParam=cur.fetchone()

            if ListParam!=None:

                table='RIVERBASIN'

                sql='UPDATE %s' % (table)
                sql+=' SET phi=%s, k=%s, n=%s, phi_sup=%s, k_sup=%s' % (ListParam)
                cur.execute(sql)
                conn.commit()

            sql='SELECT SplitID FROM Attempt'
            sql+=' WHERE attempt=%d' % bestattempt_val
            cur.execute(sql)
            BestSplit=cur.fetchone()[0]


        else:
            txt='Warning does not exists results of previous attempts'
            print (txt)


    elif bestattempt==-1:

        # averages the parameters of the different attempts
        sql='SELECT phi,k,n,phi_sup,k_sup FROM Attempt'
        if Eff_theshold>0:
            sql+=' WHERE Eff>=%s' % Eff_theshold
        sql+=';'
        cur.execute(sql)
        ListParam=cur.fetchall()

        if len(ListParam)>0:
            ParamArray=np.array(ListParam)
            ParamArrayMean=np.mean(ParamArray, axis=0)

            ListParamMean= ParamArrayMean.tolist()

            ListParamMeanTuple=tuple(ListParamMean)

            table='RIVERBASIN'

            sql='UPDATE %s' % (table)
            sql+=' SET phi=%s, k=%s, n=%s, phi_sup=%s, k_sup=%s' % (ListParamMeanTuple)
            cur.execute(sql)
            conn.commit()

            # update tuple
            ListParam = ListParamMeanTuple

        else:
            txt='Warning does not exists results of previous attempts'
            print (txt)

    elif bestattempt==0:

        # Get data from database
        TableName='InitialValues'
        sql='SELECT A_kmq, phi, k, n, phi_sup, k_sup, description FROM %s' % TableName
        sql+=';'
        cur.execute(sql)
        record = cur.fetchone()

        Area,phi,k,n,phi_sup,k_sup,description = record


        table='RIVERBASIN'

        # clears the contents of the table
        sql='DELETE FROM %s;' % table
        cur.execute(sql)
        conn.commit()

        sql='INSERT INTO %s (A_kmq,phi,k,n,phi_sup,k_sup,description) VALUES (' % table
        sql+='%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,"%s");' % (Area,phi,k,n,phi_sup,k_sup,description)
        cur.execute(sql)
        conn.commit()

        # load updates
        sql='SELECT phi,k,n,phi_sup,k_sup FROM %s' % table
        cur.execute(sql)
        ListParam=cur.fetchone()

    else:
        bestattempt_val = bestattempt*1
        sql='SELECT phi,k,n,phi_sup,k_sup FROM Attempt'
        sql+=' WHERE attempt=%d' % bestattempt_val
        cur.execute(sql)
        ListParam=cur.fetchone()

        if ListParam!=None:

            table='RIVERBASIN'

            sql='UPDATE %s' % (table)
            sql+=' SET phi=%s, k=%s, n=%s, phi_sup=%s, k_sup=%s' % (ListParam)
            cur.execute(sql)
            conn.commit()

        else:
            txt='Warning attempt = %d does not exists' % bestattempt_val
            txt+='\nyou need to update the config data'
            print (txt)


    # Close communication with the database
    cur.close()
    conn.close()

    return ListParam,bestattempt_val,BestSplit

def main():

    pass

if __name__ == '__main__':
    main()
