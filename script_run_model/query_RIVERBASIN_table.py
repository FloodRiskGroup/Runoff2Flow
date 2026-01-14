#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      MANCUSI
#
# Created:     25/07/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pandas as pd
import os
import sqlite3
import configparser


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

    if not os.path.exists(ProjectPath):
        NotErr=bool()
        msg='Error ProjectPath: % does not exists' % ProjectPath
        return NotErr, msg

    ProjectName=configuration.get('Input_par','ProjectName')
    mydb='%s.sqlite' % ProjectName
    mydb_path=ProjectPath + os.sep +mydb

    if not os.path.exists(mydb_path):
        NotErr=bool()
        msg='Error mydb_path: % does not exists' % mydb_path
        return NotErr, msg

    # Read sqlite query results into a pandas DataFrame
    con = sqlite3.connect(mydb_path)
    df = pd.read_sql_query("SELECT * from RIVERBASIN", con)

    # Verify that result of SQL query is stored in the dataframe
    pd.set_option('display.max_columns',None)
    print(df.head())

    con.close()

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)
