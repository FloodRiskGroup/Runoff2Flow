#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      MANCUSI
#
# Created:     07/09/2022
# Copyright:   (c) MANCUSI 2022
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

def convert_to_date(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo).date()

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

from Utils import Select_continuos_periods

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

    # connessione al database sqlite
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
##    conn = sqlite3.connect(mydb_path)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()

    TableNameBasin='RIVERBASIN'
    sql='SELECT description FROM %s;' % TableNameBasin
    cur.execute(sql)
    description=cur.fetchall()


    # Select continuos periods of discharge observation
    QobsArray,dic_continuous_periods,Periods_array,period_max = Select_continuos_periods(cur)

    fig = plt.figure(figsize=[15, 7.8])

    # Create a new subplot from a grid of 1x1
    ax = fig.add_subplot(111)

    for key in dic_continuous_periods:
        mask=Periods_array==key
        label_cur='period: from %s to %s' % (dic_continuous_periods[key][0],dic_continuous_periods[key][-1])
        Y1=QobsArray[mask]
        ax.plot(dic_continuous_periods[key],Y1,'-', linewidth=2.5, label=label_cur)

    mask=Periods_array==period_max
    Y1=QobsArray[mask]
    ax.plot(dic_continuous_periods[period_max],Y1,'o', linewidth=2.5, label='max continuous period')

    title='Observed river discharge: %s' % description[0][0]
    ax.set_title(title, fontsize=25)

    ax.grid(True)

    ax.legend(loc='upper right')

    ax.set_ylabel('Q (m3/s)', fontsize=18)
    ax.set_xlabel('Date', fontsize=18)

    plt.show()



if __name__ == '__main__':
    main()
