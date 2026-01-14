#-------------------------------------------------------------------------------
# Name:        Model_IUH_NASH
# Purpose:
#
# Author:      MANCUSI
#
# Created:     20/09/2021
# Copyright:   (c) MANCUSI 2021
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""
Istantaneus Unit Hydrograph of Nash
"""
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import configparser

from scipy.special import gamma
from functools import reduce
from operator import add

import numpy as np
import math
from sklearn.metrics import mean_absolute_error
import os, sys
import csv
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def Select_periodi(cur):
    """
    Identify continuous observed discharge periods from database.
    Breaks at missing/zero values to find calibration windows.
    Returns: QobsArray, continuous_periods dict, period_mask, longest_period_id
    """
    # TSTYPE=20: Observed total discharge (Qtot) from database schema
    TimeTable='TimeSeries'
    TSTYPE=20
    sql='SELECT TSDate,value FROM %s' % TimeTable
    sql+=' WHERE TSTYPE=%d' % TSTYPE
    sql+=' ORDER BY TSDate'
    sql+=';'
    cur.execute(sql)
    ListaQobs=cur.fetchall()

    DataIniObs=ListaQobs[0][0]
    DataFinObs=ListaQobs[-1][0]

    Qobs_series=[]
    dic_periodi_continui={}
    periodo=1
    start_periodo=bool()
    ListaPeriodi=[]

    Lista_date_mancanti=[]

    for rec in ListaQobs:
        if rec[1]>0:
            ListaPeriodi.append(periodo)
            if not start_periodo:
                start_periodo=bool('True')
                lista_date_periodo=[]
                lista_date_periodo.append(rec[0])
            else:
                lista_date_periodo.append(rec[0])
        else:
            ListaPeriodi.append(-1)
            Lista_date_mancanti.append(rec[0])
            if start_periodo:
                dic_periodi_continui[periodo]=lista_date_periodo
                periodo+=1
                start_periodo=bool()

        Qobs_series.append(rec[1])
    if start_periodo:
        dic_periodi_continui[periodo]=lista_date_periodo

    Periodi_array=np.array(ListaPeriodi)
    QobsArray=np.array(Qobs_series)

    # Create boolean mask for missing observations (negative values indicate no-data)
    mask_nodata=QobsArray<0

    Periodi_num_mesi={}
    num_max=0
    for key in dic_periodi_continui:
        nn=len(dic_periodi_continui[key])
        if nn>num_max:
            periodo_max=key
            num_max=nn*1
        Periodi_num_mesi[key]=nn

    return QobsArray,dic_periodi_continui,Periodi_array,periodo_max


def Graph(ListaY,ListaLabels,Variabile,txt_param=None,Eff=None,RMSE_model=None,MAE_model=None,chk_vol=None,FileOut=None,EffVer=None,period_valid_verify=None,mask=None):

##    fontP = FontProperties()
##    fontP.set_size('small')

##    fig = plt.figure()
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
##            if mask.any()!=None:
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

    if FileOut!=None:
        fig.savefig(FileOut,dpi=150,format='png')
    else:
        plt.show()

    plt.close("all")

class IUH_NASH_LinearRes:
    """
    Instantaneous Unit Hydrograph (IUH) Nash model with linear reservoir cascade.
    Separates discharge into baseflow (groundwater) and surface runoff components.
    
    Basin Parameters:
    - A_kmq: Basin surface area (km²)
    
    Baseflow Calibration Parameters (Nash model):
    - phi: Ratio between surface and groundwater basin areas
    - k: Depletion constant of Nash model cascade
    - N: Number of linear reservoirs in series
    
    Surface Runoff Calibration Parameters (Linear reservoir):
    - phi_sup: Ratio between surface basin area and closure section contribution area
    - k_sup: Depletion constant of linear reservoir model
    """

    def __init__(self, ProjectName,ProjectPath,dic_param,ParametersList,ListMinMax='',i_max=100):

        self.ProjectName = ProjectName       # file name
        self.ProjectPath = ProjectPath       # file full path
        self.AreaSup=dic_param['AreaSup']    # Area sup km2
        if 'Qtot' in dic_param:
            self.Qtot=dic_param['Qtot']       # Qtot Observed
            self.exist_obs=bool('True')
            self.period=dic_param['period']
            self.nYear=int(len(self.Qtot)/self.period)
        else:
            self.exist_obs=bool()
        self.Q_runoff=dic_param['Q_runoff']   # Q_runoff
        self.Q_reach=dic_param['Q_reach']     # Q_reach
        if self.exist_obs:
            if 'Vtot_obs' in dic_param:
                self.Vtot_obs_1=dic_param['Vtot_obs']   # Vtot_obs
                self.exist_obs=bool('True')
            else:
                self.exist_obs=bool()

        if self.exist_obs:
            if 'CalibrationMask' in dic_param:
                self.calib_mask = dic_param['CalibrationMask']
                self.exist_calib=bool('True')
            else:
                self.exist_calib=bool()
                self.calib_mask = self.Qtot>0
        else:
            self.exist_calib=bool()


        if 'verify_period' in dic_param:
            self.exist_verify=bool('True')
            self.verify_period=dic_param['verify_period']
            # input verify Time Series
            self.Qtot_Verify=self.verify_period[0]
            self.Q_runoff_Verify=self.verify_period[1]
            self.Q_reach_Verify=self.verify_period[2]
            self.numsteps_Verify=len(self.Qtot_Verify)
            self.mask_valid_verify=self.verify_period[3]
            self.period_valid_verify=self.verify_period[4]
        else:
            self.exist_verify=bool()


        # Baseflow volume coefficient: converts m³/s to million m³
        # Assumes 30-day average month: 30 days × 86400 sec/day × 10^-6 unit conversion
        # This is used in volume balance checks (chk_Vol method)
        self.C_BaseFlow=30.0*86400/1000000.0


        # Historical window of groundwater recharge data for convolution
        # PreviousMonths: lag period needed for Nash cascade impulse response
        # Longer groundwater recharge history than observed discharge due to time delay
        if self.exist_obs:
            self.PreviousMonths=len(self.Q_reach)-len(self.Qtot)+1
            # num steps
            self.numsteps=len(self.Qtot)
        elif 'PreviousMonths' in dic_param:
            self.PreviousMonths=dic_param['PreviousMonths']+1
            # num steps
            self.numsteps=len(self.Q_reach)-self.PreviousMonths+1
        else:
            self.PreviousMonths=13
            # num steps
            self.numsteps=len(self.Q_reach)-self.PreviousMonths+1


        # number of previous months of the runoff
        # including the current one
        if self.exist_obs:
            self.PreviousMonthsSup=len(self.Q_runoff)-len(self.Qtot)+1
        else:
            difflen=len(self.Q_reach)-len(self.Q_runoff)
            self.PreviousMonthsSup=self.PreviousMonths -difflen

        self.chromosomes= ParametersList

        Parameters=np.array(ParametersList,dtype=np.float64)
        NumParam=len(ParametersList)

        if ListMinMax!='':

            # -----------------------------
            # Parameter for calibration
            # -----------------------------

            # groundwater part
            # ----------------------

            # phi: ratio between surface and groundwater basin area
            i_par=0
            self.phi = ListMinMax[i_par][0]+ (ListMinMax[i_par][1]-ListMinMax[i_par][0]) * Parameters[i_par]/i_max

            # k Coefficient : depletion constant of the Nash model
            i_par+=1
            self.k = ListMinMax[i_par][0]+ (ListMinMax[i_par][1]-ListMinMax[i_par][0]) * Parameters[i_par]/i_max

            # N : Number of linear reservoirs in series of the Nash model
            i_par+=1
            self.N = ListMinMax[i_par][0]+ (ListMinMax[i_par][1]-ListMinMax[i_par][0]) * Parameters[i_par]/i_max

            # surface part
            # ----------------------

            # phi: increase/decrease surface basin area
            i_par+=1
            self.phi_sup = ListMinMax[i_par][0]+ (ListMinMax[i_par][1]-ListMinMax[i_par][0]) * Parameters[i_par]/i_max

            # k Coefficient : depletion constant of the surface Nash model
            i_par+=1
            self.k_sup = ListMinMax[i_par][0]+ (ListMinMax[i_par][1]-ListMinMax[i_par][0]) * Parameters[i_par]/i_max

        else:

            # -----------------------------
            # Parameters
            # -----------------------------

            # groundwater part
            # ----------------------

            # phi: ratio between surface and groundwater basin area
            i_par=0
            self.phi = Parameters[i_par]

            # k Coefficient : depletion constant of the Nash model
            i_par+=1
            self.k = Parameters[i_par]

            # N : Number of linear reservoirs in series of the Nash model
            i_par+=1
            self.N = Parameters[i_par]

            # Surface runoff parameters
            # ----------------------

            # phi_sup: increase/decrease surface basin area contribution
            i_par+=1
            self.phi_sup =  Parameters[i_par]

            # k_sup Coefficient: depletion constant of surface Nash model
            i_par+=1
            self.k_sup =  Parameters[i_par]

        # Nash model baseflow computation
        # ================================
        # Creates impulse response function for cascade of N linear reservoirs
        # with depletion constant k. IUH describes how groundwater recharge
        # translates into baseflow over time.
        GN=gamma(self.N)
        i=np.arange(self.PreviousMonths)+1
        # Instantaneous Unit Hydrograph of Nash - impulse response function
        hi=self.IUH_NASH_np(GN,self.k,self.N,i)
        # Reverse order for convolution with recharge series (most recent first)
        self.hi=np.flip(hi)
        # Verification: check impulse response function normalization
        somma=self.hi.sum()


    def Calc_Ws_ini(self, k, Pe):
        """
        Calculate initial water storage (mm) in linear reservoir using
        antecedent rainfall/recharge series. Uses exponential decay approximation
        to estimate pre-period equilibrium state from input time series.
        """
        esp=1.0/k
        Ws_cur=0.0
        for Pe_i in Pe:
            # Ws (mm)
            Ws_cur=k*Pe_i*(1.0-math.exp(-esp))+Ws_cur*math.exp(-esp)

        return Ws_cur

    def IUH_NASH_np(self, GN, k, n, i):
        """
        Instantaneous Unit Hydrograph of Nash: gamma distribution impulse response.
        Describes how one unit of recharge is distributed over future months.
        Formula: hi(t) = (1/k*Gamma(n)) * (t/k)^(n-1) * exp(-t/k)
        i: array of time steps (months)
        """
        hi=1.0/(k*GN)*(i/k)**(n-1.0)*np.exp(-i/k)
        return hi

    def UpdateCalibrationPeriod(self,mask):
        """
        update calibration period
        """
        self.exist_verify=bool('True')
        self.calib_mask=mask
        self.verify_mask=np.logical_not(self.calib_mask)

    def NashSutcliffeVerifyPeriod(self):
        """
        Run model for verify period and calculate Nash-Sutcliffe

        # input verify Time Series
        self.Qtot_Verify=self.verify_period[0]
        self.Q_runoff_Verify=self.verify_period[1]
        self.Q_reach_Verify=self.verify_period[2]
        self.numsteps_Verify=len(self.Qtot_Verify)
        """
        # Calc Qbase Verify period
        QbaseList=[]
        for i in range(self.numsteps_Verify):
            Qi=self.Q_reach_Verify[i:i+self.PreviousMonths]
            Qi=Qi*self.hi
            Qbasei=Qi.sum()
            QbaseList.append(Qbasei)
        nn=len(QbaseList)
        QbaseArray=np.array(QbaseList)
        Qbase_Verify=self.phi*QbaseArray

        # Initial water storage in surface linear reservoir
        Pe_i=self.Q_runoff_Verify[:self.PreviousMonthsSup]
        Ws_ini =  self.Calc_Ws_ini(self.k_sup,Pe_i)


        # Calc Qsup
        QsupList=[Ws_ini/self.k_sup]
        esp=1.0/self.k_sup
        for i in range(1,self.numsteps_Verify):
            Qi=self.Q_runoff_Verify[i+self.PreviousMonthsSup-1]
            Qsupi=Qi*(1.0-math.exp(-esp))+QsupList[i-1]*math.exp(-esp)
            QsupList.append(Qsupi)
        nn_sup=len(QsupList)
        QsupArray=np.array(QsupList)
        Qsup_Verify=self.phi_sup*QsupArray

        # Sum Qbase+Qsup
        Qm=Qbase_Verify+Qsup_Verify

        # Nash–Sutcliffe model efficiency coefficient (NSE)
        # -------------------------------------------------

        Qo=self.Qtot_Verify

        # only valid values ​​are used
        # --------------------------
        Qo=Qo[self.mask_valid_verify]
        Qm=Qm[self.mask_valid_verify]

        # mean of observed
        QoM=Qo.mean()


        diff1=Qo-QoM
        nn1=len(diff1)
        S1= reduce(add, (diff1[i]**2 for i in range(nn1)))
        diff2=Qo-Qm
        S2= reduce(add, (diff2[i]**2 for i in range(nn1)))
        Eff=(S1-S2)/S1

        self.EffVeify=Eff

        return Eff


    def Run(self):
        """
        Run model
        """
        # Calc Qbase
        QbaseList=[]
        for i in range(self.numsteps):
            Qi=self.Q_reach[i:i+self.PreviousMonths]
            Qi=Qi*self.hi
            Qbasei=Qi.sum()
            QbaseList.append(Qbasei)
        nn=len(QbaseList)
        QbaseArray=np.array(QbaseList)
        self.Qbase=self.phi*QbaseArray

        # Initial water storage in surface linear reservoir
        Pe_i=self.Q_runoff[:self.PreviousMonthsSup]
        Ws_ini =  self.Calc_Ws_ini(self.k_sup,Pe_i)


        # Calc Qsup
        QsupList=[Ws_ini/self.k_sup]
        esp=1.0/self.k_sup
        for i in range(1,self.numsteps):
            Qi=self.Q_runoff[i+self.PreviousMonthsSup-1]
            Qsupi=Qi*(1.0-math.exp(-esp))+QsupList[i-1]*math.exp(-esp)
            QsupList.append(Qsupi)
        nn_sup=len(QsupList)
        QsupArray=np.array(QsupList)
        self.Qsup=self.phi_sup*QsupArray

        # Sum Qbase+Qsup
        self.QtotCalc=self.Qbase+self.Qsup

    def NashSutcliffe(self):
        """
        Nash–Sutcliffe model efficiency coefficient (NSE)
        Calibration
        """

        # only valid values ​​are used
        Qo= self.Qtot[self.calib_mask]
        Qm= self.QtotCalc[self.calib_mask]

        # mean of observed
        QoM=Qo.mean()

        diff1=Qo-QoM
        nn1=len(diff1)
        S1= reduce(add, (diff1[i]**2 for i in range(nn1)))
        diff2=Qo-Qm
        S2= reduce(add, (diff2[i]**2 for i in range(nn1)))
        Eff=(S1-S2)/S1

        self.Eff=Eff

        return Eff

    def NashSutcliffeVerify(self):
        """
        Nash–Sutcliffe model efficiency coefficient (NSE)
        Verify period
        """
        if self.exist_verify:

            # only valid values ​​are used
            Qo= self.Qtot[self.mask_valid_verify]
            Qm= self.QtotCalc[self.mask_valid_verify]
            # mean of observed
            QoM=Qo.mean()

            diff1=Qo-QoM
            nn1=len(diff1)
            S1= reduce(add, (diff1[i]**2 for i in range(nn1)))
            diff2=Qo-Qm
            S2= reduce(add, (diff2[i]**2 for i in range(nn1)))
            Eff=(S1-S2)/S1
        else:
            Eff=-1.0


        self.EffVeify=Eff

        return Eff


    def MAE(self):
        """
        Mean Absolute Error (MAE)
        Calibration
        """
        # only valid values ​​are used
        Qo= self.Qtot[self.calib_mask]
        Qm= self.QtotCalc[self.calib_mask]

        # mean_absolute_error(y_true, y_pred)
        MAE= mean_absolute_error(Qo, Qm)

        self.MAE=MAE

        return MAE


    def RMSE(self):
        """
        Root Mean Square Error (RMSE)
        calibration
        """

        # only valid values ​​are used
        Qo= self.Qtot[self.calib_mask]
        Qm= self.QtotCalc[self.calib_mask]

        nn=len(Qo)
        diff=Qo-Qm
        Sum2= reduce(add, (diff[i]**2 for i in range(nn)))
        Sum2_mean=Sum2/nn
        model_RMSE=math.sqrt(Sum2_mean)

        self.RMSE=model_RMSE

        return model_RMSE

    def CalcVolume(self):

        # mean Qobs
        # only valid values ​​are used
        Qo= self.Qtot[self.calib_mask]
        Qm= self.QtotCalc[self.calib_mask]
        numsteps=int(self.calib_mask.sum())

        Qobs_mean=Qo.mean()
        self.Vtot_obs=Qobs_mean*numsteps*self.C_BaseFlow

        # Volume error percentage
        err=(self.Vtot_obs_1-self.Vtot_obs)/self.Vtot_obs_1*100.0

        # mean Calc
        Qcal_mean=Qm.mean()
        # Vcal
        self.Vtot_calc=Qcal_mean*numsteps*self.C_BaseFlow


    def chk_Vol(self):

        chk_vol= self.Vtot_calc/self.Vtot_obs

        return chk_vol

def main():
    pass


if __name__ == '__main__':
    main()
