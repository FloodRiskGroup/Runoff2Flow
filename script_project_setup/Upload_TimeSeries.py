#-------------------------------------------------------------------------------
# Name:        Load_TimeSeries
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys
import csv
import sqlite3
import configparser
from calendar import monthrange
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

def Load_TimeSerie_from_csv(csv_file,dic_desc_TSType):

    fin = open(csv_file, 'r')
    reader = csv.DictReader(fin, delimiter=',')

    dic_field_tstype={}
    for name in reader.fieldnames:
        for key in dic_desc_TSType:
            if name in key:
                dic_field_tstype[name]=dic_desc_TSType[key]
                break

    headers= reader.fieldnames
    header_value=headers[1]
    Nodata=-9999

    rows=[]
    Dates=[]
    for row in reader:
        # for field in Field_list_upload
        data_str=row['Date']
        TSDateTime=date.fromisoformat(data_str)
        TSDateTimeIsoformat=TSDateTime.strftime("%Y-%m-%d")
        Dates.append(TSDateTime)

        record=[]
        record.append(dic_field_tstype[name])
        record.append(TSDateTimeIsoformat)
        try:
            val= float(row[header_value])
        except:
            val=Nodata
        record.append(val)
        rows.append(record)

    fin.close()

    return rows,Dates,name

def Load_TimeSerie_at_Dates_from_csv(csv_file,dic_desc_TSType,Dates):

    fin = open(csv_file, 'r')
    reader = csv.DictReader(fin, delimiter=',')

    dic_field_tstype={}
    for name in reader.fieldnames:
        for key in dic_desc_TSType:
##            print(key)
            if name in key:
                dic_field_tstype[name]=dic_desc_TSType[key]
                break

    headers= reader.fieldnames
    header_value=headers[1]
    Nodata=-9999

    rows=[]

    for row in reader:
        # for field in Field_list_upload
        data_str=row['Date']
        TSDateTime=date.fromisoformat(data_str)
        if TSDateTime>=Dates[0] and TSDateTime<=Dates[-1]:
            record=[]
            record.append(dic_field_tstype[name])
            TSDateTimeIsoformat=TSDateTime.strftime("%Y-%m-%d")
            record.append(TSDateTimeIsoformat)
            try:
                val= float(row[header_value])
                if val<0:
                    val=Nodata
            except:
                val=Nodata
            record.append(val)
            rows.append(record)

    fin.close()

    return rows,name

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

    MainDirOutput=configuration.get('globalOptions','MainDirOutput')
    MainDirOutput = os.path.realpath(MainDirOutput)

    # get timeseries filename
    # ------------------------

    surface_runoff_csv=configuration.get('output','surface_runoff_csv')
    surface_runoff_csv = MainDirOutput + os.sep +surface_runoff_csv

    groundwater_recharge_csv=configuration.get('output','groundwater_recharge_csv')
    groundwater_recharge_csv = MainDirOutput + os.sep +groundwater_recharge_csv


    historical_river_flows_csv=configuration.get('output','historical_river_flows_csv')
    historical_river_flows_csv = MainDirOutput + os.sep + historical_river_flows_csv


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

    # =================================
    # connect to sqlite database
    # =================================
    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur= conn.cursor()


    LegendTable='TSTYPES'

    sql='SELECT TSTYPE,TSCODE FROM %s' % LegendTable
    cur.execute(sql)
    ListTSType=cur.fetchall()

    dic_TSType_desc={}
    dic_desc_TSType={}
    for rec in ListTSType:
        dic_TSType_desc[rec[0]]=rec[1]
        dic_desc_TSType[rec[1]]=rec[0]


    table='TimeSeries'
    sql="PRAGMA table_info(%s);" % table
    cur.execute(sql)
    data = cur.fetchall()

    Field_type={}
    Field_notnull={}
    Field_pk={}
    for rec in data:
        Field_type[rec[1]]=rec[2]
        Field_notnull[rec[1]]=rec[3]
        Field_pk[rec[1]]=rec[5]

    Field_list_upload=[]
    for key in Field_notnull:
        if key!='PKUID':
            Field_list_upload.append(key)

    _template='INSERT INTO %s (' % table
    for field in Field_list_upload:
        _template+='%s, ' % field
    _template='%s) VALUES (' % _template[:-2]

    num_field=len(Field_list_upload)
    newholder=''
    for i in range(num_field):
        newholder+='?,'
    newholder=newholder[:-1]
    _template+='%s)' % newholder
    _template+=';'

    # load surface runoff csv
    if os.path.exists(surface_runoff_csv):

        rows,Dates,name = Load_TimeSerie_from_csv(surface_runoff_csv,dic_desc_TSType)

        # delete old data
        sql='DELETE FROM %s' % table
        sql+=' WHERE TSTYPE=%s' % dic_desc_TSType[name]
        sql+=';'
        cur.execute(sql)
        conn.commit()

        for row in rows:
            try:
                cur.execute(_template,row)
            except:
                pass
        conn.commit()
        print('Upload', name)

    # load groundwater recharge
    if os.path.exists(groundwater_recharge_csv):

        rows,Dates,name = Load_TimeSerie_from_csv(groundwater_recharge_csv,dic_desc_TSType)


        # delete old data
        sql='DELETE FROM %s' % table
        sql+=' WHERE TSTYPE=%s' % dic_desc_TSType[name]
        sql+=';'
        cur.execute(sql)
        conn.commit()

        for row in rows:
            try:
                cur.execute(_template,row)
            except:
                pass
        conn.commit()
        print('Upload', name)


    # Load historical river flows at same date of groundwater recharge
    if os.path.exists(historical_river_flows_csv):

        rows,name = Load_TimeSerie_at_Dates_from_csv(historical_river_flows_csv,dic_desc_TSType,Dates)

        # delete old data
        sql='DELETE FROM %s' % table
        sql+=' WHERE TSTYPE=%s' % dic_desc_TSType[name]
        sql+=';'
        cur.execute(sql)
        conn.commit()

        for row in rows:
            try:
                cur.execute(_template,row)
            except:
                pass
        conn.commit()
        print('Upload', name)


    # calculate the values ​​in m3/s
    # -------------------------
    table='RIVERBASIN'
    sql='SELECT A_kmq FROM %s' % table
    cur.execute(sql)
    record=cur.fetchone()
    Area=record[0]
    # coefficient for calculating the flow rate
    CI_0=1000.0/86400.*Area

    table='TimeSeries'

    _template='INSERT INTO %s (' % table
    for field in Field_list_upload:
        _template+='%s, ' % field
    _template='%s) VALUES (' % _template[:-2]

    num_field=len(Field_list_upload)
    newholder=''
    for i in range(num_field):
        newholder+='?,'
    newholder=newholder[:-1]
    _template+='%s)' % newholder
    _template+=';'

    dic_val_mm_mcs={}
    dic_val_mm_mcs['Runoff']='Q_surface'
    dic_val_mm_mcs['Recharge']='Q_groundwater'

    for key in dic_val_mm_mcs:
        TSTypeID=dic_desc_TSType[key]
        dic_rec={}
        dic_rec['TSTYPE']=dic_desc_TSType[dic_val_mm_mcs[key]]

        sql='SELECT TSDate,value FROM %s WHERE TSTYPE=%d' % (table,TSTypeID)
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        records = cur.fetchall()
        for rec in records:
            dic_rec['TSDate']=rec[0]
            num_dys=monthrange(rec[0].year,rec[0].month)[1]
            QQ=CI_0/num_dys*rec[1]
            dic_rec['value']=QQ
            row_new=[]
            for field in Field_list_upload:
                row_new.append(dic_rec[field])
            try:
                cur.execute(_template,row_new)
            except:
                pass

        conn.commit()



    # Close communication with the database
    cur.close()
    conn.close()

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)

