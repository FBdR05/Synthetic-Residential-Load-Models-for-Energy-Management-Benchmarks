"""
@author: Fernando Bereta dos Reis

file: ZIPapliences.py
"""
import numpy as np # arrays similar to how R deals with arrays #document
import pandas as pd #time series
import scipy.stats as stats
###########################################
#CLASSE APLAENCES
###########################################
class ApplianceType(object):
    """ Generate individual appliance for a home
    
    Attributes
    ----------
    power (float): active power in Watts
    duration (float): duration in hours
    skedulable (bolean): True for skedulable and False if not
    SWn (float): swinting window (prior) in hours
    SWp (float): swinting window (ahead) in hours
    reactive (float): reactive power in VARs
    Zp (float): active impedance
    Ip (float): active current 
    Pp (float): active power
    Zq (float): reactive impedance
    Iq (float): reactive current
    Pq (float): reactive power
    indeX (int): number of the applience id
    """
    def __init__(self,power,duration,skedulable,SWn,SWp,reactive,Zp,Ip,Pp,Zq,Iq,Pq,indeX):
        """ Generate the appliance objects
        
        Parameters
        ----------
        Same as the attributes of the class
        """
        self.power      = power
        self.duration   = duration
        self.skedulable = skedulable
        self.SWn        = SWn
        self.SWp        = SWp
        self.reactive   = reactive
        self.Zp         = Zp
        self.Ip         = Ip
        self.Pp         = Pp
        self.Zq         = Zq
        self.Iq         = Iq
        self.Pq         = Pq
        self.indeX      = indeX
        
def gamma_get_shape_scale(mean,stdev):
    """ Getting gamma distribution shape and scale
    
    Parameters
    ----------
    mean (float): mean of the gamma distribution
    stdev (float): stander deviation of the gamma distribution
    
    Returns
    ----------
    shape (float): shape of the gamma distribution
    scale (float): scale of the gamma distribution
    """
    shape = (mean**2)/(stdev**2)
    scale = (stdev**2)/mean
    
    return shape,scale
###########################################
#MAKE APPLIANCES
###########################################
class AppSET(object):
    """ Generate individual appliances set for homes during the season of the year
    
    Attributes
    ----------
    appliance_set (list of appliances objects): list of appliances objects
    app_expected_load (float): expected load in Watts
    app_expected_dur (float): expected load duration in hours 
    """
    def __init__(self,DF_A,A_index,c_summer,APP_P_L):
        """ Generates the set of appliances for a season of the year
        
        Parameters
        ----------
        DF_A (pandas dataframe): apliences caracteristics
        A_index (numpy array): index of the applience 
        c_summer (numpy array): apliences participation durring a season  
        APP_P_L (list): input parameters 
            [(float) p.u. percentage of skedulable apliences 0.5=50%,
            (int) appliance set size,
            (int) average power rating in Watts,
            (int) stander power rating in Watts,
            (float) average duration in hours,
            (float) stander duration in hours,
            (float) average duration of the scheduling window in hours,
            (float) stander duration of the scheduling window in hours]
        """
        self.appliance_set = []
        self.app_expected_load = 0.0
        self.app_expected_dur = 0.0
        
        skedulable_T = stats.norm.ppf(APP_P_L[0]) #percentage of schedulable appliances 0.5=50%
        NUM_APPLIANCES  = APP_P_L[1]  #(int) appliance set size
        AVG_POWER       = APP_P_L[2]  #(int) average power rating in Watts
        STD_POWER       = APP_P_L[3]  #(int) stander power rating in Watts
        AVG_DURATION    = APP_P_L[4]  #(float) average duration in hours
        STD_DURATION    = APP_P_L[5]  #(float) stander duration in hours
        AVG_SW_DURATION = APP_P_L[6]  #(float) average duration in hours
        STD_SW_DURATION = APP_P_L[7]  #(float) stander duration in hours
        
        
        for app in range(NUM_APPLIANCES):
            #randomly generate load and duration from a gamma distribution (nonnegative)
            l_shape,l_scale = gamma_get_shape_scale(AVG_POWER,STD_POWER)
            l = np.random.gamma(l_shape,l_scale)
            
            d_shape,d_scale = gamma_get_shape_scale(AVG_DURATION,STD_DURATION)
            d = np.random.gamma(d_shape,d_scale)
            if d < 0.0003:
                d = 0.0003
#schedulable            
            n = np.random.normal(loc=0.0, scale=1.0, size=None) # select if it is schedulable 
            if n < skedulable_T:
                s = True
                
                sw_shape,sw_scale = gamma_get_shape_scale(AVG_SW_DURATION,STD_SW_DURATION)
                sWn = np.random.gamma(sw_shape,sw_scale)
                sWp = np.random.gamma(sw_shape,sw_scale)
                
                if abs(sWn) < 0.0003:
                    sWn = 0.0003
                if abs(sWp) < 0.0003:
                    sWp = 0.0003  
            else:
                s = False
                sWn = 0
                sWp = 0


            P_bies_S = c_summer/100.0
                
            AP_c = np.random.choice(A_index,size=1,replace=True,p=(P_bies_S))[0]
            
            reactive = (DF_A.Qo[AP_c]/DF_A.Po[AP_c])*l
            Zp = DF_A.Zp[AP_c]
            Ip = DF_A.Ip[AP_c]
            Pp = DF_A.Pp[AP_c]
            Zq = DF_A.Zq[AP_c]
            Iq = DF_A.Iq[AP_c]
            Pq = DF_A.Pq[AP_c]
            
            self.app_expected_dur += d
            self.app_expected_load += l
            
            self.appliance_set.append(ApplianceType(l,d,s,sWn,sWp,reactive,Zp,Ip,Pp,Zq,Iq,Pq,app))  
        #get the E[P] and E[D] terms of the set to use in the Queue below
        self.app_expected_load /= NUM_APPLIANCES
        self.app_expected_dur  /= NUM_APPLIANCES
        #to get load at time t+E[D]
        self.t_delta_exp_dur = pd.to_timedelta('%s h' % self.app_expected_dur)

