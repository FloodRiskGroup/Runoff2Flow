#-------------------------------------------------------------------------------
# Name:        CreateDatabaseSqlite
# Purpose:     Initialize SQLite database with schema for IUH NASH model:
#              - TimeSeries table (TSTYPE=20 observed discharge, other IDs for inputs)
#              - RIVERBASIN table (calibrated model parameters)
#              - Attempt table (optimization history)
# Author:      MANCUSI
# Created:     26/03/2024
#-------------------------------------------------------------------------------
import os
import csv
import sqlite3
import configparser

from datetime import datetime, timedelta, date
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

    if not os.path.exists(ProjectPath):
        os.mkdir(ProjectPath)

    ProjectName=configuration.get('Input_par','ProjectName')


    # =====================
    # Set Min, Max Values
    # =====================
    valmin=[]
    valmax=[]
    description=[]

    # ==========================
    # Model baseflow
    # ==========================
    # phi
    phi_min_max = [float(e.strip()) for e in configuration.get('Input_par','phi_min_max').split(',')]
    valmin.append(phi_min_max[0])
    valmax.append(phi_min_max[1])
    description.append('relationship between surface and groundwater basin area')

    # k Coefficient
    k_min_max = [float(e.strip()) for e in configuration.get('Input_par','k_min_max').split(',')]
    valmin.append(k_min_max[0])
    valmax.append(k_min_max[1])
    description.append('depletion constant of the groundwater flow Nash model')

    # N
    n_min_max = [float(e.strip()) for e in configuration.get('Input_par','n_min_max').split(',')]
    valmin.append(n_min_max[0])
    valmax.append(n_min_max[1])
    description.append('number of linear reservoirs in series of the baseflow Nash model')

    # ==========================
    # Model surface flow
    # ==========================
    # phi_sup
    phi_sup_min_max = [float(e.strip()) for e in configuration.get('Input_par','phi_sup_min_max').split(',')]
    valmin.append(phi_sup_min_max[0])
    valmax.append(phi_sup_min_max[1])
    description.append('increase in superficial basin area')

    # k_sup Coefficient sup
    k_sup_min_max = [float(e.strip()) for e in configuration.get('Input_par','k_sup_min_max').split(',')]
    valmin.append(k_sup_min_max[0])
    valmax.append(k_sup_min_max[1])
    description.append('depletion constant of the linear reservoir model of surface flow')


    # ----------------------------
    # Set initial values for model
    # ----------------------------

    # Load Description
    Description=configuration.get('Input_par','Description')

    # Load Area
    Area=float(configuration.get('Input_par','AreaKmq'))

    # Load phi
    phi=float(configuration.get('Input_par','phi'))
    # Load k
    k=float(configuration.get('Input_par','k'))
    # Load n
    n=float(configuration.get('Input_par','n'))

    # Load phi sup
    phi_sup=float(configuration.get('Input_par','phisup'))
    # Load ksup
    k_sup=float(configuration.get('Input_par','ksup'))



    # =================================
    # Create SQLite database with schema
    # TSTYPE identifiers:
    #   20 = Observed total discharge (Qtot)
    #   Other IDs reserved for climate/runoff inputs
    # =================================
    mydb='%s.sqlite' % ProjectName
    mydb_path=ProjectPath + os.sep +mydb

    mydb_path=os.path.realpath(mydb_path)

    if os.path.exists(mydb_path):
        os.remove(mydb_path)

##    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    # Create database
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES)
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()


    LegendTable='TSTYPES'
    sql='CREATE TABLE %s (' % LegendTable
    sql+='TSTYPE INTEGER'
    sql+=', TSCODE VARCHAR(20)'
    sql+=', unit VARCHAR(5)'
    sql+=', description VARCHAR(200)'
    sql+=');'
    cur.execute(sql)
    conn.commit()

    rows=[]
    row=('1','Ptot','mm','Average total precipitation in mm')
    rows.append(row)
    row=('2','Runoff','mm','Average runoff in mm')
    rows.append(row)
    row=('3','Recharge','mm','Average recharge in mm')
    rows.append(row)
    row=('11','Q_surface','m3/s','Average runoff in m3/s')
    rows.append(row)
    row=('12','Q_groundwater','m3/s','Average recharge in m3/s')
    rows.append(row)
    row=('20','QtotObs','m3/s','Total discharge observed in m3/s')
    rows.append(row)
    row=('21','Qsup_calc','m3/s','Superficial discharge calculated in m3/s')
    rows.append(row)
    row=('22','Qbase_calc','m3/s','Groundwater discharge calculated in m3/s')
    rows.append(row)
    row=('23','QTot_calc','m3/s','Total discharge calculated in m3/s')
    rows.append(row)

    newholder='?,' * len(row)
    newholder=newholder[:-1]

    cur.executemany("INSERT INTO %s VALUES (%s);" % (LegendTable, newholder),rows)
    conn.commit()

    TableName='RIVERBASIN'
    sql='CREATE TABLE %s (PKUID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,A_kmq REAL, phi REAL, k REAL, n REAL' % TableName
    sql+=', phi_sup REAL, k_sup REAL'
    sql+=', description VARCHAR(200)'
    sql+=');'
    cur.execute(sql)
    conn.commit()


    TableName='InitialValues'
    sql='CREATE TABLE %s (PKUID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, A_kmq REAL, phi REAL, k REAL, n REAL' % TableName
    sql+=', phi_sup REAL, k_sup REAL'
    sql+=', description VARCHAR(200)'
    sql+=');'
    cur.execute(sql)
    conn.commit()


    TableName='TimeSeries'

##    sql='CREATE TABLE %s (PKUID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,TSTYPE INTEGER, TSDate date' % TableName
##    sql+=', value REAL'
##    sql+=');'
    sql='CREATE TABLE %s (TSTYPE INTEGER, TSDate date' % TableName
##    sql='CREATE TABLE %s (TSTYPE INTEGER, TSDate date text' % TableName
    sql+=', value REAL'
    sql+=',  PRIMARY KEY (TSTYPE,TSDate)'
    sql+=');'
    cur.execute(sql)
    conn.commit()

    TableName='Attempt'

    # create table
    sql="CREATE TABLE IF NOT EXISTS %s (objectid INTEGER PRIMARY KEY, attempt INTEGER" % (TableName)
    sql+=', phi REAL, k REAL, n REAL'
    sql+=', phi_sup REAL, k_sup REAL'
    sql+=', Eff REAL'
    sql+=', RMSE REAL'
    sql+=', MAE REAL'
    sql+=', chkvol REAL'
    sql+=', Eff_verif REAL'
    sql+=', SplitID INTEGER'
    sql+=', Best INTEGER'
    sql+=');'
    cur.execute(sql)
    conn.commit()



    TableName='MinMaxValues'

    # create table
    sql="CREATE TABLE IF NOT EXISTS %s (objectid INTEGER PRIMARY KEY, attempt INTEGER, varid INTEGER" % (TableName)
    sql+=', valmin REAL'
    sql+=', valmax REAL'
    sql+=', description VARCHAR(200)'
    sql+=');'
    cur.execute(sql)
    conn.commit()

    TableName2='CalibrResults'

    # create table
    sql="CREATE TABLE IF NOT EXISTS %s (objectid INTEGER PRIMARY KEY, attempt INTEGER, varid INTEGER" % (TableName2)
    sql+=', percent INTEGER'
    sql+=', value REAL'
    sql+=', description VARCHAR(100)'
    sql+=');'
    cur.execute(sql)
    conn.commit()

    TableName3='Efficiency'
    # create table
    sql="CREATE TABLE IF NOT EXISTS %s (objectid INTEGER PRIMARY KEY, attempt INTEGER" % (TableName3)
    sql+=', Efficiency REAL'
    sql+=', RMSE REAL'
    sql+=', MAE REAL'
    sql+=');'
    cur.execute(sql)
    conn.commit()


    # Save initial values
    # --------------------
    table='RIVERBASIN'

    sql='INSERT INTO %s (A_kmq,phi,k,n,phi_sup,k_sup,description) VALUES (' % table
    sql+='%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,"%s");' % (Area,phi,k,n,phi_sup,k_sup,Description)
    cur.execute(sql)
    conn.commit()

    # Save default values
    # --------------------
    table='InitialValues'
    sql='INSERT INTO %s (A_kmq,phi,k,n,phi_sup,k_sup,description) VALUES (' % table
    sql+='%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,"%s");' % (Area,phi,k,n,phi_sup,k_sup,Description)
    cur.execute(sql)
    conn.commit()


    # Save min/max values
    # --------------------
    i_length=len(valmin)

    for i in range(i_length):
        # write record
        sql="INSERT INTO %s (attempt,varid,valmin,valmax,description) VALUES (" % TableName
        sql+="%d" % 0
        sql+=",%d" % i
        sql+=",%s" % valmin[i]
        sql+=",%s" % valmax[i]
        sql+=",'%s'" % description[i]
        sql+=");"
        cur.execute(sql)

    # Make the changes to the database persistent
    conn.commit()
    # Close communication with the database
    cur.close()
    conn.close()

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)
