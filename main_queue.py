"""
@author: Fernando Bereta dos Reis

file: main_queue.py
"""
from __future__ import print_function
from scoop import futures
import multiprocessing
import numpy as np 
import pandas as pd 
import timeit
import ZIPapliences as A_ZIP

class load_generation:
    """ Class prepares the system for generating load
    
    Attributes
    ----------
    START_TIME_Q (pandas datetime): start time to generate load data
    END_TIME_Q (pandas datetime): end time to generate load data
    Queue_type (int): 0=inf; 1=C; 2=Ct
    P_U_B (int): percentage upper boud --> e.g. 2 = 200% from the reference
    physical_machine (int): 1 = single node 2 = multiple nodes
    NUM_WORKERS (int): number of workers used when generating load in a single node
    NUM_HOMES (int): number of homes being generated
    OUT_PUT_FILE_NAME_pre (str): file path to write output 
    OUT_PUT_FILE_NAME (str): prefix of file name to be writen
    OUT_PUT_FILE_NAME_end (str): end of file name
    OUT_PUT_FILE_NAME_summary_pre (str): file path to write output 
    OUT_PUT_FILE_NAME_summary (str): prefix of summary file name to be writen
    
    TIME_DELT (pandas datetime): 1 minute 
    TIME_DELT_FH (pandas datetime): 1 hour 
    TIME_DELT_FD (pandas datetime): 1 day 
    
    base_max (float): rescaling load reference uper bound 
    base_min (float): rescaling load reference lower bound 
    
    ref_load (pandas series): reference load
    DF_A (pandas dataframe): appliances characteristics
    DF_ZIP_summer (pandas dataframe): appliances participation during the summer
    DF_ZIP_winter (pandas dataframe): appliances participation during the winter
    DF_ZIP_spring (pandas dataframe): appliances participation during the spring
    
    APP_parameter_list (list): input parameters 
        [(float) p.u. percentage of schedulable appliances 0.5=50%,
        (int) appliance set size,
        (int) average power rating in Watts,
        (int) stander power rating in Watts,
        (float) average duration in hours,
        (float) stander duration in hours,
        (float) average duration of the scheduling window in hours,
        (float) stander duration of the scheduling window in hours]
    
    Methods
    -------
    __init__ : create object with the parameters for the load generation
    read_data : load input data
    """
    def __init__(self,ST,ET,T,P,M,NW,NH):
        """ Create load_generation object
        
        Parameters
        ----------
        ST (str): start time to generate load data e.g. '2014-01-01 00:00:00'
        ET (str): end time to generate load data
        T (int): 0=inf; 1=C; 2=Ct
        P (int): percentage upper boud --> e.g. 2 = 200% from the reference
        M (int): 1 = single node 2 = multiple nodes
        NW (int): number of workers used when generating load in a single node
        NH (int): number of homes being generated
        """
        self.START_TIME_Q                  = pd.to_datetime(ST)
        self.END_TIME_Q                    = pd.to_datetime(ET)
        self.Queue_type                    = T
        self.P_U_B                         = P
        self.physical_machine              = M
        self.NUM_WORKERS                   = NW
        self.NUM_HOMES                     = NH
        self.OUT_PUT_FILE_NAME_pre         = 'outputdata/multy/'
        self.OUT_PUT_FILE_NAME             = 'multHDF'
        self.OUT_PUT_FILE_NAME_end         = '.h5'
        self.OUT_PUT_FILE_NAME_summary_pre = 'outputdata/summary/'
        self.OUT_PUT_FILE_NAME_summary     = 'summaryHDF'
        #Auxiliary variables
        self.TIME_DELT = pd.to_timedelta('0 days 00:01:00')
        self.TIME_DELT_FH = pd.to_timedelta('0 days 01:00:00')
        self.TIME_DELT_FD = pd.to_timedelta('1 days 00:00:00')
        
        self.base_max  = 5000.0
        self.base_min  =  100.0
        
        #From data
        self.ref_load = None
        self.DF_A = None
        self.DF_ZIP_summer = None
        self.DF_ZIP_winter = None
        self.DF_ZIP_spring = None
        
        #DEFINITIONS APPLIANCES
        self.APP_parameter_list = [0.5,100,500,100,0.5,0.25,6.0,2.0]
        
    def read_data(self,IF='inputdata/'):
        """ Load reference load and appliance data
        
        Parameters
        ----------
        IF (str): folder of input data
        """
        # Reference Energy
        sys_load = pd.read_hdf(IF+'load_data.h5')
        sys_load = sys_load['load']
        sys_load = sys_load[self.START_TIME_Q:self.END_TIME_Q+self.TIME_DELT_FD]#*1e6 #DATA IS IN HOURS
        sys_load = sys_load.resample(self.TIME_DELT_FH).max().ffill()#fix empty locations
        
        scale_min = sys_load[self.START_TIME_Q:self.END_TIME_Q].min()
        scale_max = sys_load[self.START_TIME_Q:self.END_TIME_Q].max()
        
        ref = sys_load
        
        ref = self.base_min+((ref-scale_min)/(scale_max-scale_min))*(self.base_max-self.base_min)
        ref.name = 'Load [W]'
        ref = ref.resample(self.TIME_DELT).max().interpolate(method='polynomial', order=0,limit_direction='forward')
        
        self.ref_load = ref
        # ZIP load
        self.DF_A = pd.read_csv(IF+'ZIP_appliances.csv')
        self.DF_ZIP_summer = pd.read_csv(IF+'ZIP_summer.csv')
        self.DF_ZIP_winter = pd.read_csv(IF+'ZIP_winter.csv')
        self.DF_ZIP_spring = pd.read_csv(IF+'ZIP_spring.csv')
        
###########################################
# save data to file
########################################### 
def save_HD5(a,b,x):
    """ Save the generated load to HDF5 files
    
    Parameters
    ----------
    a (pandas dataframe): complete  dataframe
    b (pandas dataframe): summary dataframe
    x (str): string number of the individual home id
    """
    a.to_hdf(LG.OUT_PUT_FILE_NAME_pre+LG.OUT_PUT_FILE_NAME+x+LG.OUT_PUT_FILE_NAME_end, key=x,format='table',mode='w',dropna = True)
    b.to_hdf(LG.OUT_PUT_FILE_NAME_summary_pre+LG.OUT_PUT_FILE_NAME_summary+x+LG.OUT_PUT_FILE_NAME_end, key=x,format='table',mode='w',dropna = True)
    return None

###########################################
#APLAENCES seasson 
###########################################
def makeAPP(DF_A,DF_ZIP_summer,DF_ZIP_winter,DF_ZIP_spring,APP_P_L):
    """ Generate individual appliances set for homes during the season of the year
    
    Parameters
    ----------
    DF_A (pandas dataframe): appliances characteristics
    DF_ZIP_summer (pandas dataframe): appliances participation during the summer
    DF_ZIP_winter (pandas dataframe): appliances participation during the winter
    DF_ZIP_spring (pandas dataframe): appliances participation during the spring
    
    Returns
    ----------
    APP_L_obj (list of applience objecs): applience objects list for seasons 
    """
    strataN=4 #from the ZIP study paper
    c_index = np.array(DF_ZIP_summer['A_index'])
    c_winter = np.array(DF_ZIP_winter.iloc[:,strataN])
    c_spring = np.array(DF_ZIP_spring.iloc[:,strataN])
    c_summer = np.array(DF_ZIP_summer.iloc[:,strataN])
    
    APP_L_obj = []
    APP_L_obj.append(A_ZIP.AppSET(DF_A,c_index,c_spring,APP_P_L))
    APP_L_obj.append(A_ZIP.AppSET(DF_A,c_index,c_summer,APP_P_L))
    APP_L_obj.append(A_ZIP.AppSET(DF_A,c_index,c_winter,APP_P_L))
    
    return APP_L_obj

def season(date, HEMISPHERE = 'north'):
    """ Informe season of the year
    
    Parameters
    ----------
    date (pandas datetime): time being generated 
    HEMISPHERE (str): north or south hemisphere
    
    Returns
    ----------
    s (int): indicates the season 
    """
    md = date.month * 100 + date.day

    if ((md > 320) and (md < 621)):
        s = 0 #spring
    elif ((md > 620) and (md < 923)):
        s = 1 #summer
    elif ((md > 922) and (md < 1223)):
        s = 2 #fall
    else:
        s = 3 #winter

    if not HEMISPHERE == 'north':
        s = (s + 2) % 3
        
    if s ==2:
        s=0 #spring and fall have same loads
    if s == 3:
        s=2
    return s

def SeasonUPdate(temp):
    """ Update appliance characteristics given the change in season
    
    Parameters
    ----------
    temp (obj): appliance set object for an individual season
    
    Returns
    ----------
    app_expected_load (float): expected load power in Watts
    app_expected_dur (float): expected duration in hours
    appliance_set (list of applience objects): applience list for a given season
    t_delta_exp_dur (pandas datetime): expected appliance duration
    app_index (array): index for each applience
    """
    app_expected_load = temp.app_expected_load
    app_expected_dur = temp.app_expected_dur
    appliance_set = temp.appliance_set
    t_delta_exp_dur = temp.t_delta_exp_dur
    app_index = np.arange(0,len(temp.appliance_set))
    
    return app_expected_load,app_expected_dur,appliance_set,t_delta_exp_dur,app_index

###########################################
#MAKE QUEUE MODEL C = infinity 
###########################################
def solverZIPl_inf(x):
    """ Generate load with C = infinity
    
    Parameters
    ----------
    x (str): string number of the individual home id
    
    Returns
    ----------
    x (str): string number of the individual home id
    """
    START_TIME_Q = LG.START_TIME_Q
    END_TIME_Q   = LG.END_TIME_Q
    ref_load     = LG.ref_load
    current_time = START_TIME_Q

    customer_loads_GL = (ref_load*0.0).copy()
    customer_loads_GL_VAR = (ref_load*0.0).copy()
    
    L1=[];L2=[];L3=[];L4=[];L5=[];L6=[];L7=[];L8=[];L9=[];L10=[];L11=[];L12=[];L13=[];L14=[];
    L1=list();L2=list();L3=list();L4=list();L5=list();L6=list();L7=list()
    L8=list();L9=list();L10=list();L11=list();L12=list();L13=list();L14=list();
    
    APP_L_obj = makeAPP(LG.DF_A,LG.DF_ZIP_summer,LG.DF_ZIP_winter,LG.DF_ZIP_spring,LG.APP_parameter_list)
    app_expected_load,app_expected_dur,appliance_set,t_delta_exp_dur,app_index = SeasonUPdate(APP_L_obj[season(current_time,'north')])
    
    dates = ref_load.index
    while current_time < END_TIME_Q:
        m_t_plus_delta = ref_load.asof(where=current_time+t_delta_exp_dur)
        lambda_t = m_t_plus_delta / (app_expected_load*app_expected_dur) #lam(t) = m(t + E[D])/(E[D]E[L])
        
        delta_t = np.random.exponential(1.0/lambda_t) #lambda_t is the rate parameter, numpy requires the scale which is the reciprocal of rate. Alternatively can switch the calculation of lambda_t, but this way matches the derived equations.
        if delta_t < 0.00000003:
            delta_t = 0.00000003
        current_time += pd.to_timedelta('%s s' % (delta_t*3600.0)) #converted to seconds as some delta_t in hours was too small for pandas to parse correctly
        
        if current_time < END_TIME_Q: #check after time is updated we are still in sim time
            ###########################################
            #Season 
            ###########################################
            app_expected_load,app_expected_dur,appliance_set,t_delta_exp_dur,app_index = SeasonUPdate(APP_L_obj[season(current_time,'north')])

            app = appliance_set[np.random.choice(app_index,size=1,replace=True)[0]]
            add_time = current_time
            
            this_app_endtime = add_time + pd.to_timedelta('%s h' % app.duration)
            this_app_curtime = add_time
            
            customer_loads_GL[dates.asof(this_app_curtime):dates.asof(this_app_endtime)] += app.power
            customer_loads_GL_VAR[dates.asof(this_app_curtime):dates.asof(this_app_endtime)] += app.reactive
            
            L1.append(dates.asof(this_app_curtime))#['start time']=dates.asof(this_app_curtime)
            L2.append(pd.to_timedelta('%s h' % app.duration).round('1min'))#['duration']=pd.to_timedelta('%s h' % app.duration).round('1min')
            L3.append(app.power)#['power']=app.power
            L4.append(app.skedulable)#['skedulable']=app.skedulable
            L5.append(pd.to_timedelta('%s h' % app.SWn).round('1min'))#['shifting window -']=pd.to_timedelta('%s h' % app.SWn).round('1min')
            L6.append(pd.to_timedelta('%s h' % app.SWp).round('1min'))#['shifting window +']=pd.to_timedelta('%s h' % app.SWp).round('1min')
            L7.append(app.reactive)#['reactive']=app.reactive
            L8.append(app.Zp)#['Zp']=app.Zp
            L9.append(app.Ip)#['Ip']=app.Ip
            L10.append(app.Pp)#['Pp']=app.Pp
            L11.append(app.Zq)#['Zq']=app.Zq
            L12.append(app.Iq)#['Iq']=app.Iq
            L13.append(app.Pq)#['Pq']=app.Pq
            L14.append(app.indeX)#['indeX']=app.indeX
            
    sagra = pd.DataFrame({'start time': L1,
                 'duration': L2,
                 'power': L3,
                 'skedulable': L4,
                 'shifting window -': L5,
                 'shifting window +': L6,
                 'reactive': L7,
                 'Zp': L8,
                 'Ip': L9,
                 'Pp': L10,
                 'Zq': L11,
                 'Iq': L12,
                 'Pq': L13,
                 'indeX': L14
                })     

    sagra = sagra[sagra['start time'] >= START_TIME_Q]
    sagra = sagra.reset_index(drop=True)
    sagra = sagra[sagra['start time'] <= END_TIME_Q]
    sagra = sagra.reset_index(drop=True)
    
    customer_loads_GL = customer_loads_GL[START_TIME_Q:END_TIME_Q]
    customer_loads_GL_VAR = customer_loads_GL_VAR[START_TIME_Q:END_TIME_Q]
    activeANDreactive = pd.DataFrame({'W':customer_loads_GL, 'VAR':customer_loads_GL_VAR})
    
    save_HD5(sagra,activeANDreactive,x)
    return x

###########################################
#MAKE QUEUE MODEL C <-- limited
###########################################
def solverZIPl_C(x):
    """ Generate load with C <-- limited
    
    Parameters
    ----------
    x (str): string number of the individual home id
    
    Returns
    ----------
    x (str): string number of the individual home id
    """
    START_TIME_Q = LG.START_TIME_Q
    END_TIME_Q   = LG.END_TIME_Q
    P_U_B        = LG.P_U_B
    ref_load     = LG.ref_load
    TIME_DELT    = LG.TIME_DELT
    
    current_time = START_TIME_Q
    customer_loads_GL = (ref_load*0.0).copy()
    customer_loads_GL_VAR = (ref_load*0.0).copy()
    
    L1=[];L2=[];L3=[];L4=[];L5=[];L6=[];L7=[];L8=[];L9=[];L10=[];L11=[];L12=[];L13=[];L14=[];
    L1=list();L2=list();L3=list();L4=list();L5=list();L6=list();L7=list()
    L8=list();L9=list();L10=list();L11=list();L12=list();L13=list();L14=list();
    
    W_TIME = pd.to_timedelta('0 days 22:00:00')
    if LG.Queue_type == 1:
        S_W = (ref_load*0.0 + 1) * ((ref_load[START_TIME_Q:END_TIME_Q].max())*P_U_B)
    if LG.Queue_type == 2:
        S_W = ref_load*P_U_B
    
    APP_L_obj = makeAPP(LG.DF_A,LG.DF_ZIP_summer,LG.DF_ZIP_winter,LG.DF_ZIP_spring,LG.APP_parameter_list)
    app_expected_load,app_expected_dur,appliance_set,t_delta_exp_dur,app_index = SeasonUPdate(APP_L_obj[season(current_time,'north')])
    
    dates = ref_load.index
    while current_time < END_TIME_Q:
        m_t_plus_delta = ref_load.asof(where=current_time+t_delta_exp_dur)
        lambda_t = m_t_plus_delta / (app_expected_load*app_expected_dur) #lam(t) = m(t + E[D])/(E[D]E[L])
        
        delta_t = np.random.exponential(1.0/lambda_t) #lambda_t is the rate parameter, numpy requires the scale which is the reciprocal of rate. Alternatively can switch the calculation of lambda_t, but this way matches the derived equations.
        if delta_t < 0.00000003:
            delta_t = 0.00000003
        current_time += pd.to_timedelta('%s s' % (delta_t*3600.0)) #converted to seconds as some delta_t in hours was too small for pandas to parse correctly
        
        if current_time < END_TIME_Q: #check after time is updated we are still in sim time
            ###########################################
            #Season 
            ###########################################
            app_expected_load,app_expected_dur,appliance_set,t_delta_exp_dur,app_index = SeasonUPdate(APP_L_obj[season(current_time,'north')])

            app = appliance_set[np.random.choice(app_index,size=1,replace=True)[0]]
            V_W = (customer_loads_GL[dates.asof(current_time):dates.asof(current_time+W_TIME)] + app.power) < (S_W[dates.asof(current_time):dates.asof(current_time+W_TIME)])
            add_time = current_time
            while add_time <= current_time + W_TIME:
                VV_W = V_W[dates.asof(add_time):dates.asof(add_time + pd.to_timedelta('%s h' % app.duration))]
                VV_W_L = VV_W.index[VV_W == True].tolist()
                if len(VV_W_L) >= VV_W.size:
                    break
                add_time += TIME_DELT
            
            this_app_endtime = add_time + pd.to_timedelta('%s h' % app.duration)
            this_app_curtime = add_time
            
            customer_loads_GL[dates.asof(this_app_curtime):dates.asof(this_app_endtime)] += app.power
            customer_loads_GL_VAR[dates.asof(this_app_curtime):dates.asof(this_app_endtime)] += app.reactive
            
            L1.append(dates.asof(this_app_curtime))#['start time']=dates.asof(this_app_curtime)
            L2.append(pd.to_timedelta('%s h' % app.duration).round('1min'))#['duration']=pd.to_timedelta('%s h' % app.duration).round('1min')
            L3.append(app.power)#['power']=app.power
            L4.append(app.skedulable)#['skedulable']=app.skedulable
            L5.append(pd.to_timedelta('%s h' % app.SWn).round('1min'))#['shifting window -']=pd.to_timedelta('%s h' % app.SWn).round('1min')
            L6.append(pd.to_timedelta('%s h' % app.SWp).round('1min'))#['shifting window +']=pd.to_timedelta('%s h' % app.SWp).round('1min')
            L7.append(app.reactive)#['reactive']=app.reactive
            L8.append(app.Zp)#['Zp']=app.Zp
            L9.append(app.Ip)#['Ip']=app.Ip
            L10.append(app.Pp)#['Pp']=app.Pp
            L11.append(app.Zq)#['Zq']=app.Zq
            L12.append(app.Iq)#['Iq']=app.Iq
            L13.append(app.Pq)#['Pq']=app.Pq
            L14.append(app.indeX)#['indeX']=app.indeX
            
    sagra = pd.DataFrame({'start time': L1,
                 'duration': L2,
                 'power': L3,
                 'skedulable': L4,
                 'shifting window -': L5,
                 'shifting window +': L6,
                 'reactive': L7,
                 'Zp': L8,
                 'Ip': L9,
                 'Pp': L10,
                 'Zq': L11,
                 'Iq': L12,
                 'Pq': L13,
                 'indeX': L14
                })     

    sagra = sagra[sagra['start time'] >= START_TIME_Q]
    sagra = sagra.reset_index(drop=True)
    sagra = sagra[sagra['start time'] <= END_TIME_Q]
    sagra = sagra.reset_index(drop=True)
    
    customer_loads_GL = customer_loads_GL[START_TIME_Q:END_TIME_Q]
    customer_loads_GL_VAR = customer_loads_GL_VAR[START_TIME_Q:END_TIME_Q]
    activeANDreactive = pd.DataFrame({'W':customer_loads_GL, 'VAR':customer_loads_GL_VAR})

    save_HD5(sagra,activeANDreactive,x)
    return x

###########################################
# Where to solve
###########################################   
def SDSU_cluster():
    """ Generate load with multiple nodes
    """
    x = [str(i) for i in range(1,LG.NUM_HOMES+1)]
    if LG.Queue_type == 2 or LG.Queue_type == 1:
        returnValues = list(futures.map(solverZIPl_C, x))
    else:
        returnValues = list(futures.map(solverZIPl_inf, x))
    print("\n".join(returnValues))
    
def local():
    """ Generate load with a single node
    """
    p = multiprocessing.Pool(LG.NUM_WORKERS)
    x = [str(i) for i in range(1,LG.NUM_HOMES+1)]
    if LG.Queue_type == 2 or LG.Queue_type == 1:
        p.map(solverZIPl_C, x)
    else:
        p.map(solverZIPl_inf, x)
    p.close()
    p.join()
    
###########################################
# Global Object 
###########################################
#load start time, end time, type, 200%, 1 node, 2 workers, 4 homes
LG = load_generation('2154-11-06 00:00:00','2154-11-08 00:00:00',2,2,2,2,79)
LG.read_data() # read input data
LG.base_max  = 5000.0 #rescaling load reference uper bound 
LG.base_min  =  100.0 #rescaling load reference lower bound 
LG.APP_parameter_list = [0.5,100,500,100,0.5,0.25,6.0,2.0]#[p.u. percentage of schedulable appliances 0.5=50%,(int) appliance set size,(int) average power rating in Watts,(int) stander power rating in Watts,(float) average duration in hours,(float) stander duration in hours,(float) average duration of the scheduling window in hours,(float) stander duration of the scheduling window in hours]
###########################################
# Main
###########################################
if __name__ == '__main__':
    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    
    start_time = timeit.default_timer()
    print("Time it takes initialize:")
    print(timeit.default_timer() - start_time)
    start_time = timeit.default_timer()
#    solverZIPl_inf('40')
#    solverZIPl_C('41')
    if LG.physical_machine == 1:
        local()
    if LG.physical_machine == 2:
        SDSU_cluster()
    
    print("Time it takes [all costomer] :")
    print(timeit.default_timer() - start_time)


