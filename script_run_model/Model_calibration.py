#-------------------------------------------------------------------------------
# Name:        Model_calibration
# Purpose:
#
# Author:      MANCUSI
#
# Created:     26/03/2024
# Copyright:   (c) MANCUSI 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import configparser
import platform
import os
import numpy as np
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from calendar import monthrange
import time
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from Model_IUH_NASH_LinearRes import IUH_NASH_LinearRes
from Model_IUH_NASH_LinearRes import Graph
from genetic import *

from dateutil.parser import parse
def convert_to_date(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo).date()


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

from Utils import UpdateParameters

class Calib_IUH_NASH_model():

    def __init__(self,config_input,ProjectName):

        Config = configparser.ConfigParser()

        Config.read(config_input)

        # input nome
        self.ProjectName = ProjectName

        # Input lag times
        self.SupFlowMaxLagTime = int(Config.get('Input_par','SupFlowMaxLagTime'))
        self.BaseFlowMaxLagTime = int(Config.get('Input_par','BaseFlowMaxLagTime'))

        # Repeating period (typically 12 months for monthly data)
        self.period=int(Config.get('Input_par','period'))


        # Select verbose output: yes or no
        self.verbose=int(Config.get('Input_par','verbose'))


        # input parametri algoritmo genetico
        self.typefitness = Config.get('genetic','typefitness')
        if self.typefitness == 'NashSutcliffe':
            self.fitnessid=0
        elif self.typefitness == 'RMSE':
            self.fitnessid=1
        elif self.typefitness == 'MAE':
            self.fitnessid=2
        else:
            self.fitnessid=0

        self.attempts_start = [int(e.strip()) for e in Config.get('genetic', 'attempts_start').split(',')]
        self.attempts = [int(e.strip()) for e in Config.get('genetic', 'attempts').split(',')]

        self.p_count = int(Config.get('genetic','p_count'))  # num people of population
        self.MaxGeneration = int(Config.get('genetic','MaxGeneration'))  # num generation to run

        self.MainDirImageout = Config.get('globalOptions','MainDirImageout')

        # Load minmax from ini file
        # -------------------------
        self.dic_param_min ={}
        self.dic_param_max ={}

        # relationship between surface and groundwater basin area
        phi_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'phi_min_max').split(',')]).tolist()
        self.dic_param_min['phi']=phi_min_max[0]
        self.dic_param_max['phi']=phi_min_max[1]

        # depletion constant of the groundwater flow Nash model
        k_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'k_min_max').split(',')]).tolist()
        self.dic_param_min['k']=k_min_max[0]
        self.dic_param_max['k']=k_min_max[1]

        # number of linear reservoirs in series of the baseflow Nash model
        n_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'n_min_max').split(',')]).tolist()
        self.dic_param_min['n']=n_min_max[0]
        self.dic_param_max['n']=n_min_max[1]

        # increase in superficial basin area
        phi_sup_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'phi_sup_min_max').split(',')]).tolist()
        self.dic_param_min['phi_sup']=phi_sup_min_max[0]
        self.dic_param_max['phi_sup']=phi_sup_min_max[1]


        # depletion constant of the linear reservoir model of surface flow
        k_sup_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'k_sup_min_max').split(',')]).tolist()
        self.dic_param_min['k_sup']=k_sup_min_max[0]
        self.dic_param_max['k_sup']=k_sup_min_max[1]


        ProjectPath=Config.get('globalOptions','ProjectPath')
        self.ProjectPath = os.path.realpath(ProjectPath)
        mydb='%s.sqlite' % self.ProjectName
        mydb_path=self.ProjectPath + os.sep +mydb
        self.mydb_path=os.path.realpath(mydb_path)

        # --------------
        # open database
        # --------------
        conn = sqlite3.connect(self.mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        # select name river basin
        sql='SELECT description FROM RIVERBASIN;'
        cur.execute(sql)
        record=cur.fetchone()

        self.Description = record[0]
        txt='river station: %s' % record[0]
        print(txt)

        # check splitperiods
        Tableslipt='splitperiods'

        sql='SELECT SplitID FROM %s' % Tableslipt
        sql+=' ORDER BY SplitID DESC'
        sql+=';'
        cur.execute(sql)
        self.List_splitperiods=cur.fetchall()

        self.NumSplit = len(self.List_splitperiods)

        # check if first attempts exist
        sql="SELECT attempt FROM Attempt"
        sql+=' ORDER BY attempt'
        sql+=';'
        cur.execute(sql)
        List_Attempt=cur.fetchall()

        # Check whether any starting attempts have been made
        if len(List_Attempt)< len(self.attempts_start):
            self.To_do_start_attempts=bool('True')
        else:
            self.To_do_start_attempts=bool()

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
        self.date_end_TimeSeries = List_date[-1][0]

        MaxLag=max(self.SupFlowMaxLagTime,self.BaseFlowMaxLagTime)
        self.date_ini_TimeSeries=date_ini_TimeSeries+relativedelta(months=MaxLag)


        # Input range for genetic algorithm parameter search
        self.dic_min_max={}

        update_minmax_type = int(Config.get('genetic','update_minmax_type'))

        if update_minmax_type != 0:

            TabName='Attempt'
            Fields=['phi','k','n','phi_sup','k_sup']
            # seleziona parametri
            sql="SELECT "
            for field in Fields:
                sql+='%s,' % field
            sql='%s' % sql[:-1]
            sql+=" FROM %s" % (TabName)
            sql+=';'
            cur.execute(sql)
            records=cur.fetchall()

            if len(records)>1:

                ParamArray=np.array(records)
                ParamMin= np.amin(ParamArray, axis=0)
                ParamMax= np.amax(ParamArray, axis=0)
                ParamMean= np.mean(ParamArray, axis=0)
                Delta=ParamMean *0.2
                ParamMin=ParamMin-Delta
                ParamMax = ParamMax + Delta

                ii=-1
                for field in Fields:
                    ii+=1
                    self.dic_min_max[ii]=[ParamMin[ii],ParamMax[ii]]
            else:
                update_minmax_type = 0

        # load observed discharge
        # QtotObs m3/s
        TSTYPE=20
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % self.date_ini_TimeSeries
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        records=cur.fetchall()

        List_date_obs=[]
        List_Q_obs=[]
        for rec in records:
            List_date_obs.append(rec[0])
            List_Q_obs.append(rec[1])


        date_ini_TimeSeries_obs = List_date_obs[0]
        date_end_TimeSeries_obs = List_date_obs[-1]
        self.date_end_TimeSeries_obs=date_end_TimeSeries_obs

        delta_days=date_end_TimeSeries_obs-date_ini_TimeSeries_obs

        new_date= records[0][0]

        lista_obs_period=[]
        lista_obs_mask=[]

        ii=0
        while new_date<=date_end_TimeSeries_obs:
            if new_date==List_date_obs[ii]:
                lista_obs_mask.append(1)
                ii+=1
            else:
                lista_obs_mask.append(0)

            lista_obs_period.append(new_date)
            new_date = new_date + relativedelta(months=1)

        mask_array=np.array(lista_obs_mask)
        self.obs_data_mask=mask_array>0

        # Load Train Test Period last
        self.dic_RecordSplits={}
        Tableslipt='splitperiods'

        for rec_split_period in self.List_splitperiods:
            split_period= rec_split_period[0]
            sql='SELECT SplitID,TrainDateIni,TrainDateEnd'
            sql+=',TestDateIni,TestDateEnd FROM %s' % Tableslipt
            sql+=' WHERE SplitID=%d' % split_period
            sql+=';'

            cur.execute(sql)
            RecordSplit=cur.fetchone()
            self.dic_RecordSplits[split_period]=RecordSplit


        # Close communication with the database
        cur.close()
        conn.close()

        if update_minmax_type == 0:

                # ratio between surface and groundwater basin area
                phi_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'phi_min_max').split(',')]).tolist()
                self.dic_min_max[0]= phi_min_max
                # depletion constant of the Nash baseflow model
                k_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'k_min_max').split(',')]).tolist()
                self.dic_min_max[1]= k_min_max
                # Number of linear reservoirs in series of the Nash baseflow model
                n_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'n_min_max').split(',')]).tolist()
                self.dic_min_max[2]= n_min_max
                # increase surface basin area
                phi_sup_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'phi_sup_min_max').split(',')]).tolist()
                self.dic_min_max[3]= phi_sup_min_max
                # depletion constant of the linear reservoir model of surface flow
                k_sup_min_max = np.array([float(e.strip()) for e in Config.get('genetic', 'k_sup_min_max').split(',')]).tolist()
                self.dic_min_max[4]= k_sup_min_max

        dir_out_img = Config.get('out_img','dir_out_img')
        dir_out_img = self.MainDirImageout + os.sep+ dir_out_img
        self.dir_out_img = os.path.realpath(dir_out_img)
        if not os.path.exists(self.dir_out_img):
            os.mkdir(self.dir_out_img)

        # Load split data
        # ================
        # Initialize from first split
        self.set_current_split(0)
        self.Load_split_param()


    def Load_split_param(self):

        # Load split period parameters
        self.split_period=self.List_splitperiods[self.curren_split][0]
        RecordSplit=self.dic_RecordSplits[self.split_period]
        self.TrainDateIni = RecordSplit[1]
        self.TrainDateEnd = RecordSplit[2]
        self.TestDateIni = RecordSplit[3]
        self.TestDateEnd = RecordSplit[4]
        self.verify_period=bool('True')

        # Load historical time series data into memory for calibration
        self.set_timeseries()

        # Count number of years in dataset
        num_steps=len(self.dic_param['Qtot'])
        nY=int(num_steps/self.period)
        self.dic_param['period']=self.period
        self.dic_param['nYear']=nY

    def CreatePopulation(self, p1):
        """Instantiate IUH_NASH_LinearRes models from chromosome genes.
        
        Decodes normalized gene values (0-i_max) to actual parameter ranges
        using ListMinMax bounds, then evaluates fitness of each individual.
        """
        p = []
        count = len(p1)

        for i in range(count):
            param_cur = p1[i]
            Model = IUH_NASH_LinearRes(self.ProjectName, self.ProjectPath, self.dic_param, param_cur, self.ListMinMax, self.i_max)
            Model.Run()
            Eff = Model.NashSutcliffe()
            RMSE = Model.RMSE()
            MAE = Model.MAE()
            p.append(Model)

        return p

    def update_calibration_period(self,mask):

        self.dic_param['CalibrationPeriod']=mask

    def set_current_split(self,curren_split):
        """
        Set the split data
        """
        self.curren_split = curren_split

    def set_timeseries(self):

        n_max=max(self.SupFlowMaxLagTime,self.BaseFlowMaxLagTime)

        if self.verify_period:
            self.data_ini_calibrazione=self.TrainDateIni

            if self.data_ini_calibrazione< self.date_ini_TimeSeries:
                self.data_ini_calibrazione=self.date_ini_TimeSeries

            self.data_fin_calibrazione=self.TrainDateEnd
        else:
            self.data_ini_calibrazione=self.date_ini_TimeSeries
            self.data_fin_calibrazione=self.date_end_TimeSeries_obs

        conn = sqlite3.connect( self.mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        TableNameBasin='RIVERBASIN'
        sql='SELECT A_kmq FROM %s;' % TableNameBasin
        cur.execute(sql)
        ListArea=cur.fetchall()
        AreaSup=ListArea[0][0]

        # ================================================================================================
        # Volume calculation coefficient: convert m³/s to million m³
        # ================================================================================================
        # VolMmc = (num_days * 86400 sec/day) * Q_m3/s * 10^-6 (unit conversion)
        # ================================================================================================
        CI_Vol=86.4

        TimeTable='TimeSeries'

        # Qtot Observed
        TSTYPE=20
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % (self.data_ini_calibrazione)
        sql+=" AND TSDate<='%s'" % (self.data_fin_calibrazione)
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        ListTargetQTOT=cur.fetchall()
        nn=len(ListTargetQTOT)/12
        Qtot=[]
        Vtot_obs=0.0
        for rec in ListTargetQTOT:
            num_dys=monthrange(rec[0].year,rec[0].month)[1]
            # to exclude Nodata
            if rec[1]>0:
                num_dys=monthrange(rec[0].year,rec[0].month)[1]
                Vtot_obs=Vtot_obs+CI_Vol*num_dys*rec[1]
            Qtot.append(rec[1])
        QtotArray=np.array(Qtot)

        mask_calib=QtotArray>0

        if self.verify_period:
            # Qtot Observed
            TSTYPE=20
            sql='SELECT TSDate,value FROM %s' % TimeTable
            sql+=' WHERE TSTYPE=%d' % TSTYPE
            sql+=" AND TSDate>='%s'" % (self.TestDateIni)
            sql+=" AND TSDate<='%s'" % (self.TestDateEnd)
            sql+=' ORDER BY TSDate'
            sql+=';'
            cur.execute(sql)
            ListVerifytQTOT=cur.fetchall()
            Q_Verify=[]
            T_Verify=[]
            for rec in ListVerifytQTOT:
                T_Verify.append(rec[0])
                Q_Verify.append(rec[1])
            Q_VerifyArray=np.array(Q_Verify)

            # check for valid data
            mask_valid_verify=Q_VerifyArray>0

            # Q_runoff m3/s
            TSTYPE=11
            data_ini_runoff=self.TestDateIni+relativedelta(months=-self.SupFlowMaxLagTime)
            sql='SELECT TSDate,value FROM %s' % TimeTable
            sql+=' WHERE TSTYPE=%d' % TSTYPE
            sql+=" AND TSDate>='%s'" % (data_ini_runoff)
            sql+=" AND TSDate<='%s'" % (self.TestDateEnd)
            sql+=' ORDER BY TSDate'
            sql+=';'
            cur.execute(sql)
            ListQ_runoff=cur.fetchall()
            nn1=len(ListQ_runoff)/12
            Q_runoff=[]
            for rec in ListQ_runoff:
                Q_runoff.append(rec[1])
            Q_runoffArray_Verify=np.array(Q_runoff)


            # Q_reach m3/s
            TSTYPE=12
            # Read data including 12 preceding months
            data_ini_reac=self.TestDateIni+relativedelta(months=-self.BaseFlowMaxLagTime)
            sql='SELECT TSDate,value FROM %s' % TimeTable
            sql+=' WHERE TSTYPE=%d' % TSTYPE
            sql+=" AND TSDate>='%s'" % (data_ini_reac)
            sql+=" AND TSDate<='%s'" % (self.TestDateEnd)
            sql+=' ORDER BY TSDate'
            sql+=';'
            cur.execute(sql)
            ListQ_reach=cur.fetchall()
            nn2=len(ListQ_reach)/12
            Q_reach=[]
            for rec in ListQ_reach:
                Q_reach.append(rec[1])
            Q_reachArray_Verify=np.array(Q_reach)


            T_ini_year_verify=self.TestDateIni.year
            T_end_year_verify=self.TestDateEnd.year
            self.period_valid_verify=[T_ini_year_verify,T_end_year_verify]

        # Q_runoff m3/s
        TSTYPE=11
        data_ini_runoff=self.data_ini_calibrazione+relativedelta(months=-self.SupFlowMaxLagTime)
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % (data_ini_runoff)
        sql+=" AND TSDate<='%s'" % (self.data_fin_calibrazione)
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        ListQ_runoff=cur.fetchall()
        nn1=len(ListQ_runoff)/12
        Q_runoff=[]
        for rec in ListQ_runoff:
            Q_runoff.append(rec[1])
        Q_runoffArray=np.array(Q_runoff)


        # Q_reach m3/s
        TSTYPE=12
        # read with the 12 previous months
        data_ini_reac=self.data_ini_calibrazione+relativedelta(months=-self.BaseFlowMaxLagTime)
        sql='SELECT TSDate,value FROM %s' % TimeTable
        sql+=' WHERE TSTYPE=%d' % TSTYPE
        sql+=" AND TSDate>='%s'" % (data_ini_reac)
        sql+=" AND TSDate<='%s'" % (self.data_fin_calibrazione)
        sql+=' ORDER BY TSDate'
        sql+=';'
        cur.execute(sql)
        ListQ_reach=cur.fetchall()
        nn2=len(ListQ_reach)/12
        Q_reach=[]
        for rec in ListQ_reach:
            Q_reach.append(rec[1])
        Q_reachArray=np.array(Q_reach)

        self.dic_param={}
        self.dic_param['AreaSup']=AreaSup
        self.dic_param['Qtot']=QtotArray
        self.dic_param['Q_runoff']=Q_runoffArray
        self.dic_param['Q_reach']=Q_reachArray
        self.dic_param['Vtot_obs']=Vtot_obs
        self.dic_param['CalibrationMask']=mask_calib
        if self.verify_period:
            self.dic_param['verify_period']=[Q_VerifyArray,Q_runoffArray_Verify,Q_reachArray_Verify,mask_valid_verify,self.period_valid_verify]

        TableName='MinMaxValues'

        sql='SELECT valmin, valmax FROM %s WHERE attempt=0 ORDER BY varid;' % TableName
        cur.execute(sql)
        self.ListMinMax=cur.fetchall()

        sql='SELECT description,varid FROM %s WHERE attempt=0 ORDER BY varid;' % TableName
        cur.execute(sql)
        self.description=cur.fetchall()

        # Dictionary mapping variable IDs to descriptions
        self.dic_varid_descr={}
        for rec in self.description:
            self.dic_varid_descr[rec[1]]=rec[0]

        # Close communication with the database
        cur.close()
        conn.close()

    def update_min_max(self):

        conn = sqlite3.connect(self.mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        TableName='MinMaxValues'

        for i in self.dic_min_max:

            sql='UPDATE %s' % (TableName)
            sql+=' SET valmin=%s, valmax=%s' % (self.dic_min_max[i][0],self.dic_min_max[i][1])
            sql+=' where varid=%d' % i
            sql+=';'
            cur.execute(sql)
        conn.commit()

        sql='SELECT valmin, valmax FROM %s WHERE attempt=0 ORDER BY varid;' % TableName
        cur.execute(sql)
        self.ListMinMax=cur.fetchall()

        # Close communication with the database
        cur.close()
        conn.close()

    def update_min_max_from_attempts(self):

        """
        Update max and min parameters based on previous attempts
        """

        conn = sqlite3.connect(self.mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        TabName='Attempt'
        Fields=['phi','k','n','phi_sup','k_sup']
        # seleziona parametri
        sql="SELECT "
        for field in Fields:
            sql+='%s,' % field
        sql='%s' % sql[:-1]
        sql+=" FROM %s" % (TabName)
        sql+=';'
        cur.execute(sql)
        records=cur.fetchall()

        if len(records)>1:

            ParamArray=np.array(records)
            ParamMin= np.amin(ParamArray, axis=0)
            ParamMax= np.amax(ParamArray, axis=0)
            ParamMean= np.mean(ParamArray, axis=0)
            Delta=ParamMean *0.2
            ParamMin=ParamMin-Delta
            ParamMax = ParamMax + Delta

            ii=-1
            for field in Fields:
                ii+=1
                # check that you do not go outside the range of the initial values
                param_min = max(self.dic_param_min[field],ParamMin[ii])
                param_max = min(self.dic_param_max[field],ParamMax[ii])
                self.dic_min_max[ii]=[param_min,param_max]

            update_minmax_type = 1

        else:
            update_minmax_type = 0

        if update_minmax_type>0:

            TableName='MinMaxValues'

            for i in self.dic_min_max:

                sql='UPDATE %s' % (TableName)
                sql+=' SET valmin=%s, valmax=%s' % (self.dic_min_max[i][0],self.dic_min_max[i][1])
                sql+=' where varid=%d' % i
                sql+=';'
                cur.execute(sql)

            conn.commit()

            sql='SELECT valmin, valmax FROM %s WHERE attempt=0 ORDER BY varid;' % TableName
            cur.execute(sql)
            self.ListMinMax=cur.fetchall()

        # Close communication with the database
        cur.close()
        conn.close()


    def fitness_model(self,individual):
        """
        Determine the fitness of an individual. Higher is better.
        individual: the individual to evaluate
        """
        individual.Run()
        Eff=individual.NashSutcliffe()
        if self.verbose>0:
            print (Eff)
        return Eff

    def grade_model_eff(self,pop):
        """
        'Find average fitness for a population.'
        """
        'Find average fitness for a population.'

        if self.fitnessid==0:
            A=np.array([float(e) for e in (x.Eff for x in pop)])
        elif self.fitnessid==1:
            A=np.array([float(e) for e in (x.RMSE for x in pop)])
        elif self.fitnessid==2:
            A=np.array([float(e) for e in (x.MAE for x in pop)])

        mean=A.mean()

        return mean

    def attempt(self,attempt):

        """
        Execute a calibration attempt
        attempt:  identifying number of the attempt whose results
                  are saved in the 'Attempt' table of the database
        """
        # start time
        start_time = time.time()

        self.i_length=len(self.ListMinMax)

        i_min = 0          # range min
        self.i_max = 1000       # range max

        # create a generic population with random chromosomes with values
        # between i_min and i_max
        p = population(self.p_count, self.i_length, i_min, self.i_max)

        # transform the generic population into a population of objects
        # the objects consist of many IUH_NASH_LinearRes models
        # whose parameters are calculated in the variation interval
        # chosen for the model through linear interpolation
        # starting from the chromosomes of p
        pop = self.CreatePopulation(p)

        # calculate the fitness of the entire population
        fitness_history = [self.grade_model_eff(pop),]

        if self.fitnessid==0:
            graded = [ (x.Eff, x.chromosomes) for x in pop]
            Eff_list= [ x[0] for x in sorted(graded,reverse=True)]
            graded = [ x[1] for x in sorted(graded,reverse=True)]
        elif self.fitnessid==1:
            graded = [ (x.RMSE, x.chromosomes) for x in pop]
            Eff_list= [ x[0] for x in sorted(graded,reverse=False)]
            graded = [ x[1] for x in sorted(graded,reverse=False)]
        elif self.fitnessid==2:
            graded = [ (x.MAE, x.chromosomes) for x in pop]
            Eff_list= [ x[0] for x in sorted(graded,reverse=False)]
            graded = [ x[1] for x in sorted(graded,reverse=False)]

        Model=IUH_NASH_LinearRes(self.ProjectName,self.ProjectPath,self.dic_param,graded[0],self.ListMinMax,self.i_max)
        Model.Run()

        if self.verbose>0:
            txt='\nStarting attemt n: %d' % attempt
            print(txt)
            txt='='*len(txt)
            print(txt)

            txt='Best chromosome ini'
            print (txt)
            print (graded[0])

        if self.fitnessid==0:
            Eff=Model.NashSutcliffe()
            txt='Best efficency ini= %.3f' % Eff
        elif self.fitnessid==1:
            RMSE=Model.RMSE()
            txt='Best RMSE ini= %.3f' % RMSE
        elif self.fitnessid==2:
            MAE=Model.MAE()
            txt='Best MAE ini= %.3f' % MAE

        if self.verbose>0:
            print (txt)
            print ('................')
            txt='Parameters ini'
            print (txt)
            for i in range(self.i_length):
                value= self.ListMinMax[i][0]+ (self.ListMinMax[i][1]-self.ListMinMax[i][0]) * float(graded[0][i])/self.i_max
                txt='{:>10.2f} : {:<40}'.format(value,self.description[i][0])
                print (txt)
            print ('................')

        lista_gen=[]
        lista_EFF=[]
        lista_grade=[]

        for i in range(self.MaxGeneration):

            p, Eff_list, graded = evolve_pop(pop,self.fitnessid)

            pop = self.CreatePopulation(p)

##            if self.verbose>0:
##                txt='Generation %d  best_fit=%s' % (i,Eff_list[0])
##
##                print (txt)
##                txt='Best chromosome generation i=%d' % i
##                print (txt)
##                print (graded[0])
##                print ('................')

            gr=self.grade_model_eff(pop)
            fitness_history.append(gr)

            lista_gen.append(i)
            lista_EFF.append(Eff_list[0])
            lista_grade.append(gr)


        graded = [ (x.Eff, x.chromosomes) for x in pop]
        Eff_list= [ x[0] for x in sorted(graded,reverse=True)]
        graded = [ x[1] for x in sorted(graded,reverse=True)]

        Model=IUH_NASH_LinearRes(self.ProjectName,self.ProjectPath,self.dic_param,graded[0],self.ListMinMax,self.i_max)
        Model.Run()
        Model.CalcVolume()

        Eff=Model.NashSutcliffe()
        RMSE_model=Model.RMSE()
        MAE_model=Model.MAE()
        if Model.exist_verify:
            Eff_ver=Model.NashSutcliffeVerifyPeriod()

        chk_vol=Model.chk_Vol()

        if self.verbose>0:
            txt='chromosomes fin'
            print (txt)
            print (graded[0])
            txt='Best efficency fin= %.3f' % Eff
            print (txt)

            txt='Best parameters'
            print (txt)
            for i in range(self.i_length):
                value= self.ListMinMax[i][0]+ (self.ListMinMax[i][1]-self.ListMinMax[i][0]) * float(graded[0][i])/self.i_max
                txt='{:>10.2f} : {:<40}'.format(value,self.description[i][0])
                print (txt)
            print ('................')


##            print ('\nfitness_history')
##            for datum in fitness_history:
##               print (datum)

        # save results
        # ==============

        # connect db
        conn = sqlite3.connect(self.mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cur= conn.cursor()

        # save results
        TableName2='CalibrResults'
        for i in range(self.i_length):
            # check for old result
            sql='SELECT objectid FROM %s WHERE attempt=%d AND varid=%d'  % (TableName2,attempt,i)
            cur.execute(sql)
            record = cur.fetchone()
            if record!=None:
                sql='UPDATE %s ' %  TableName2
                sql+="SET percent=%d" % graded[0][i]
                value= self.ListMinMax[i][0]+ (self.ListMinMax[i][1]-self.ListMinMax[i][0]) * float(graded[0][i])/self.i_max
                sql+=", value=%s" % value
                sql+=" WHERE objectid=%d"  % record[0]
            else:
                sql='INSERT INTO %s (attempt, varid, percent, value,description) VALUES (' %  TableName2
                sql+="%d" % attempt
                sql+=",%d" % i
                sql+=",%d" % graded[0][i]
                value= self.ListMinMax[i][0]+ (self.ListMinMax[i][1]-self.ListMinMax[i][0]) * float(graded[0][i])/self.i_max
                sql+=",%s" % value
                sql+=",'%s'" % self.description[i][0]
                sql+=');'
            cur.execute(sql)
        conn.commit()

        TableName3='Efficiency'
        # check for old result
        sql='SELECT objectid FROM %s WHERE attempt=%d'  % (TableName3,attempt)
        cur.execute(sql)
        record = cur.fetchone()
        if record!=None:
            sql='UPDATE %s ' %  TableName3
            sql+="SET Efficiency=%s" % Eff
            sql+=", RMSE=%s" % RMSE_model
            sql+=", MAE=%s" % MAE_model
            sql+=" WHERE objectid=%d"  % record[0]
        else:
            sql='INSERT INTO %s (attempt,Efficiency,RMSE,MAE) VALUES (' %  TableName3
            sql+="%d" % attempt
            sql+=",%s" % Eff
            sql+=",%s" % RMSE_model
            sql+=",%s" % MAE_model
            sql+=');'
        cur.execute(sql)
        conn.commit()

        # save Attempt Results
        TableName='Attempt'
        sql='SELECT objectid FROM %s WHERE attempt=%d' % (TableName,attempt)
        cur.execute(sql)
        record = cur.fetchone()
        if record!=None:
            sql='UPDATE %s ' %  TableName
            sql+="SET phi=%.4f" % Model.phi
            sql+=",k=%.4f" % Model.k
            sql+=",n=%.4f" % Model.N
            sql+=",phi_sup=%.4f" % Model.phi_sup
            sql+=",k_sup=%.4f" % Model.k_sup
            sql+=",Eff=%.4f" % Eff
            sql+=",RMSE=%.4f" % RMSE_model
            sql+=",MAE=%.4f" % MAE_model
            sql+=",chkvol=%.4f" % chk_vol
            if Model.exist_verify or Model.exist_verify_period:
                sql+=",Eff_verif=%.4f" % Eff_ver
            sql+=",SplitID=%d" % self.split_period
            sql+=" WHERE objectid=%d"  % record[0]
        else:
            if Model.exist_verify:
                sql='INSERT INTO %s (attempt,phi,k,n,phi_sup,k_sup,Eff,RMSE,MAE,chkvol,Eff_verif,SplitID) VALUES (' %  TableName
            else:
                sql='INSERT INTO %s (attempt,phi,k,n,phi_sup,k_sup,Eff,RMSE,MAE,chkvol,SplitID) VALUES (' %  TableName

            sql+="%d" % attempt
            sql+=",%.4f" % Model.phi
            sql+=",%.4f" % Model.k
            sql+=",%.4f" % Model.N

            sql+=",%.4f" % Model.phi_sup
            sql+=",%.4f" % Model.k_sup

            sql+=",%.4f" % Eff
            sql+=",%.2f" % RMSE_model
            sql+=",%.2f" % MAE_model
            sql+=",%.4f" % chk_vol
            if Model.exist_verify:
                sql+=",%.4f" % Eff_ver
            sql+=",%d" % self.split_period

            sql+=');'
        cur.execute(sql)

        conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()

        if self.verbose>0:
            elapsed_time = time.time() - start_time
            txt='Elapsed time = %s' % elapsed_time
            print (txt)

        # grafico
        ListaLabels=[]
        ListaLabels.append('fitness_history')
        ListaLabels.append('Generation')

        if self.fitnessid==0:
            ListaLabels.append('Eff')
            Variabile=['Best Eff','Eff population']
        elif self.fitnessid==1:
            ListaLabels.append('RMSE')
            Variabile=['Best RMSE','RMSE population']
        elif self.fitnessid==2:
            ListaLabels.append('MAE')
            Variabile=['Best MAE','MAE population']

        ListaY=[lista_EFF]
        ListaY.append(lista_grade)
##        Graph(ListaY,ListaLabels,Variabile)


        ListaLabels=[]
        titolo='Attempt: %d - Istantaneus Unit Hydrograph of Nash %d-%d' % (attempt,self.data_ini_calibrazione.year, self.data_fin_calibrazione.year)
        ListaLabels.append(titolo)
        ListaLabels.append('x')
        ListaLabels.append('y')
        Variabile=['Qtot','Qcalc','Qbase']
        ListaY=[Model.Qtot]
        ListaY.append(Model.QtotCalc)
        ListaY.append(Model.Qbase)
        Eff=Model.NashSutcliffe()
        txt_param='Baseflow (phi=%.2f, k=%.2f, n=%.2f)' % (Model.phi,Model.k,Model.N)
        txt_param+='- Supflow ('
        txt_param+='phi=%.2f, k=%.2f)' % (Model.phi_sup,Model.k_sup)

        if Model.exist_verify:
            eff_ver= Model.EffVeify
            mask_ver = Model.mask_valid_verify
        else:
            eff_ver=None

        FileOut=None
        NameFig='Proj_%s_calibration_%d.png' % (self.ProjectName,attempt)
        FileOut=self.dir_out_img+os.sep+ NameFig

##        Graph(ListaY,ListaLabels,Variabile,txt_param,Eff,RMSE_model,MAE_model,chk_vol,FileOut,eff_ver,self.period_valid_verify,mask_ver)

    def Run_best_param(self,ListParam,BestSplit):

        Model=IUH_NASH_LinearRes(self.ProjectName,self.ProjectPath,self.dic_param,ListParam)
        Model.Run()
        Model.CalcVolume()

        Eff=Model.NashSutcliffe()
        RMSE_model=Model.RMSE()
        MAE_model=Model.MAE()
        if Model.exist_verify:
            Eff_ver=Model.NashSutcliffeVerifyPeriod()

        chk_vol=Model.chk_Vol()

        ListaLabels=[]
        if BestSplit<0:
            titolo='%s\nIstantaneus Unit Hydrograph of Nash %d-%d' % (self.Description,self.data_ini_calibrazione.year, self.data_fin_calibrazione.year)

            period_valid_verify = self.period_valid_verify

        else:
            # Set date best split
            data_ini_calibrazione = self.dic_RecordSplits[BestSplit][1]
            data_fin_calibrazione = self.dic_RecordSplits[BestSplit][2]
            titolo='%s\nIstantaneus Unit Hydrograph of Nash %d-%d' % (self.Description,data_ini_calibrazione.year, data_fin_calibrazione.year)

            period_valid_verify = [self.dic_RecordSplits[BestSplit][3].year,self.dic_RecordSplits[BestSplit][4].year]

        ListaLabels.append(titolo)
        ListaLabels.append('x')
        ListaLabels.append('y')
        Variabile=['Qtot','Qcalc','Qbase']
        ListaY=[Model.Qtot]
        ListaY.append(Model.QtotCalc)
        ListaY.append(Model.Qbase)
        Eff=Model.NashSutcliffe()
        txt_param='Baseflow (phi=%.2f, k=%.2f, n=%.2f)' % (Model.phi,Model.k,Model.N)
        txt_param+='- Supflow ('
        txt_param+='phi=%.2f, k=%.2f)' % (Model.phi_sup,Model.k_sup)

        if Model.exist_verify:
            eff_ver= Model.EffVeify
            mask_ver = None
        else:
            eff_ver=None

        FileOut=None
        NameFig='Proj_%s_calibration.png' % (self.ProjectName)
        FileOut=self.dir_out_img+os.sep+ NameFig

        Graph(ListaY,ListaLabels,Variabile,txt_param,Eff,RMSE_model,MAE_model,chk_vol,FileOut,eff_ver,period_valid_verify,mask_ver)

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
        ProjectName=pp[0]


        # start time
        start_time = time.time()

        CalibrModel = Calib_IUH_NASH_model(config_input,ProjectName)
        # updade min-max into database
        CalibrModel.update_min_max()

        if CalibrModel.To_do_start_attempts:
            for attempt in CalibrModel.attempts_start:
                CalibrModel.attempt(attempt)

        # Update min-max parameter bounds based on previous attempts
        CalibrModel.update_min_max_from_attempts()

        # Perform subsequent attempts
        for attempt in CalibrModel.attempts:
            CalibrModel.attempt(attempt)

        # TODO: Implement second split execution
        if CalibrModel.NumSplit >1:
            for i_split in range(1,CalibrModel.NumSplit):
                CalibrModel.set_current_split(i_split)
                CalibrModel.Load_split_param()
                current_attempt=attempt*1
                for attempt in CalibrModel.attempts_start:
                    current_attempt+=1
                    CalibrModel.attempt(current_attempt)


        # update best param
        mydb='%s.sqlite' % ProjectName
        mydb_path=ProjectPath + os.sep +mydb

        ListParam,bestattempt_val,BestSplit = UpdateParameters(mydb_path)

        CalibrModel.Run_best_param(ListParam,BestSplit)

        elapsed_time = time.time() - start_time
        txt='Elapsed time = %.2f sec' % elapsed_time
        print (txt)


    return NotErr, msg

if __name__ == '__main__':

    NotErr, msg = main()
    print(msg)