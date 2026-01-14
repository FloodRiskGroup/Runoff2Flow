#-------------------------------------------------------------------------------
# Name:        Load_Discharge_RSE_file
# Purpose:     Parse CSV discharge observations and create monthly time series.
#              Handles missing years by inserting no-data (-1.0) values.
#              Output: historical_river_flows.csv for database upload.
# Author:      MANCUSI
# Created:     03/02/2022
#-------------------------------------------------------------------------------
import os
from datetime import date
import matplotlib.pyplot as plt
import configparser

def main():

    NotErr=bool('True')
    msg='OK'

    dir_script=os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_script)

    config_input='Input_Setup.ini'
    config_input_location=os.path.realpath(config_input)
    configuration = configparser.ConfigParser()
    configuration.read(config_input_location)

    MainDirInput=configuration.get('globalOptions','MainDirInput')
    MainDirInput = os.path.realpath(MainDirInput)

    if not os.path.exists(MainDirInput):
        NotErr= bool()
        msg='Dir %s does not exists' % MainDirInput
        return NotErr, msg


    MainDirOutput=configuration.get('globalOptions','MainDirOutput')
    MainDirOutput = os.path.realpath(MainDirOutput)

    if not os.path.exists(MainDirOutput):
        os.mkdir(MainDirOutput)

    Discharge_file_RSE=configuration.get('input_data','Discharge_file_RSE')
    Discharge_file_RSE = MainDirInput + os.sep + Discharge_file_RSE

    if not os.path.exists(Discharge_file_RSE):
        NotErr= bool()
        msg='file %s does not exists' % Discharge_file_RSE
        return NotErr, msg

    historical_river_flows_csv=configuration.get('output','historical_river_flows_csv')
    historical_river_flows_csv = MainDirOutput + os.sep + historical_river_flows_csv


    last_year=0
    no_data=-1.0
    # Negative values mark missing observations; used by Select_periodi() to identify data gaps

    fin=open(Discharge_file_RSE,'r')
    i_ini=0
    LineList=[]
    for line in fin:
        LineList.append(line)
        if 'Anno' in line:
            # Read station name
            line_name=LineList[-3]
            pp=line_name[:-1].split(';')
            Station_name=pp[0]
            # Read headers
            pp=line[:-1].split(';')
            ii=-1
            for field in pp:
                ii+=1
                if 'Gennaio' in field:
                    i_ini=ii
                    break
            break

    DateList=[]
    ValuesList=[]
    for line in fin:
        pp=line[:-1].split(';')
        if pp[0]!='':
            year=int(pp[0])
            if year>last_year:
                delta=year-last_year-1
                if last_year!=0 and delta>0:
                    # Insert Nodata:
                    for i in range(delta):
                        last_year+=1
                        txt='NoData for year: %d' % last_year
                        print(txt)
                        for ii in range(12):
                            data_cur=date(last_year,ii+1,1)
                            DateList.append(data_cur)
                            ValuesList.append(no_data)
                for ii in range(12):
                    data_cur=date(year,ii+1,1)
                    k=i_ini+ii
                    try:
                        value=float(pp[k])
                    except:
                        value=no_data

                    DateList.append(data_cur)
                    ValuesList.append(value)
                last_year=year*1

    fig = plt.figure(figsize=[15, 7.8])
    ax = fig.add_subplot(111)
    ax.plot(DateList,ValuesList,'-', linewidth=2.0, label='monthly flows')

    title='River station: %s' % (Station_name)
    plt.title(title, fontsize=14)

    ax.legend(loc='upper right')

    ax.grid(True)

    plt.xlabel("Date")
    plt.ylabel("River flow (m3/s)")

    plt.show()

    sep=','
    # Save CSV file
    fout=open(historical_river_flows_csv,'w')
    txt='Date%sQtotObs\n' % sep
    fout.write(txt)
    nn=len(DateList)
    for ii in range(nn):
        txt='%s%s%s\n' % (DateList[ii].strftime('%Y-%m-%d'),sep,ValuesList[ii])
        fout.write(txt)
    fout.close()

    txt='Saved file: %s' % historical_river_flows_csv
    print(txt)

    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)
