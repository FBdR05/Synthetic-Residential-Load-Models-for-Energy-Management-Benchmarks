# Synthetic-Residential-Load-Models-for-Energy-Management-Benchmarks

Synthetic residential load models for Smart City energy management simulations can be generated. For detailed clarifications of how the loads are synthetic generated please view the paper cited at the end of this file.  

## Quick Start

To generate your desired synthetic residential load, you will most likely have to make changes to "main_queue.py" file. The changes are to define the time period, type, and overall parameters to generate the desired synthetic residential load. The changes are from Line 471 to Line 475.

Running the code in your local machine requires selecting 1 node and the number of workers refers to the number of customers being generated in parallel. The number of workers is recommended to be smaller than the number of available CPUs in your local machine.

## Data 
This section describes the required input data and the generated output data.

### Input data
load_data.h5 --> contains a mock data referring to the aggregated hourly energy consumption. The paper that describes the code made used of the ComEd utility aggregated hourly energy consumption. Data from "PJM. ‘PJM estimated hourly load’. Available from: http://www.pjm.com/markets-and-operations/energy/real-time/loadhryr.aspx"

The file contains time (as the index) and the hourly energy (Wh). Only time and hourly energy are present at the file. To read the file run "pandas.read_hdf('load_data.h5')".

ZIP_appliances.csv --> appliance ZIP characteristics from "Bokhari, A., Alkan, A., Dogan, R., Diaz.Aguiló, M., de León, F., Czarkowski, D., et al.: ‘Experimental Determination of the ZIP Coefficients for Modern Residential, Commercial, and Industrial Loads’, IEEE Transactions on Power Delivery, 2014, 29, (3), pp. 1372–1381"

The file contains "Ntest", "Po", "Qo", "Zp", "Ip", "Pp", "Zq", "Iq", "Pq", "Vcut", and "Vo". Where "Ntest" is the number of tested equipment’s; "Po" appliance active power (W) at nominal voltage; "Qo" appliance reactive power (VAR) at nominal voltage; "Zp", "Ip", "Pp" active power polynomial ZIP parameters; "Zq", "Iq", "Pq" reactive power polynomial ZIP parameters; "Vcut" lower bound voltage the appliance was tested (V); and "Vo" is the appliance nominal voltage (V). The rows on the file are a given appliance.

ZIP_spring.csv, ZIP_summer.csv, ZIP_winter.csv --> are the contributions the appliances have on each season. The rows in each of those files are a given appliance. The season of Fall has the same contributions as Spring. Contributions from "Bokhari, A., Alkan, A., Dogan, R., Diaz.Aguiló, M., de León, F., Czarkowski, D., et al.: ‘Experimental Determination of the ZIP Coefficients for Modern Residential, Commercial, and Industrial Loads’, IEEE Transactions on Power Delivery, 2014, 29, (3), pp. 1372–1381"

Each file contains the "A_index", "P_A", "P_B", "P_C", "P_D", "P_E", and "P_F". Where "A_index" is the appliances index; and "P_A", "P_B", "P_C", "P_D", "P_E", and "P_F" are the percentual contribution for each of the Stratum. Stratum are utilized to classify residential customers in Consolidated Edison Inc (the utility company of New York City) based on the customer annual peak power consumption. The Stratum are is not utilized in this paper. Thus, all customers are assumed Stratum D.

To read the ".csv" files run "pandas.read_csv('file_name.csv')".

### Output data

The output data is separated in two sub folders, i.e., "summary", and "multy". Once the code has finished running. The "summary" and "multy" folder contains multiple files, i.e., one for each customer. Each file in the "summary" folder contains a summary of the complete arrival of appliances for an individual customer. Thus, having a customer active (W) and reactive (VAR) power for the generated time period in minute resolution. Each file in the "multy" folder contains the complete data of the arrival of appliances for an individual customer. Thus, having all the individual appliance information and the time the appliance starts to be served. The appliance information are "start time", "duration", "power", "skedulable", "shifting window -", "shifting window +", "reactive", "Zp", "Ip", "Pp", "Zq", "Iq", "Pq", and "indeX". Where "start time" time the appliance arrived in the queue; "duration" duration of the appliance; "skedulable" boolean to classify if appliance is schedulable or not; "shifting window -" and  "shifting window +" start and end of the schedulable window; "power" active power (W); "reactive" reactive power of the appliance (VAR); "Zp", "Ip", "Pp" active power polynomial ZIP parameters; "Zq", "Iq", "Pq" reactive power polynomial ZIP parameters; and the "indeX" is the index of the appliance in the list (dependent on Season).

To read the customer "1" summary file run "pandas.read_hdf('outputdata/summary/summaryHDF1.h5',key=str(1))".
To read the customer "1" complete file run "pandas.read_hdf('outputdata/multy/multHDF1.h5',key=str(1))".

## Utilized python packages (Python 3.7.4)
future==0.18.2
scoop==0.7.1.1
numpy==1.17.2
pandas==0.25.1
tables==3.5.2
scipy==1.3.1

## License

The work is released under the Creative Commons Attribution (CC BY) license. Which in summary allows the distribute, remix, tweak, and build upon the work, even commercially, as long as you credit the original creation. For your reference, the file "ccby_licence.pdf" from "https://digital-library.theiet.org/journals/oa-author-guide#copyright" is part of the repository. 

To credit the original creation citing the published paper below is required:
dos Reis, F. B., Tonkoski, R., Hansen, T, "Synthetic Residential Load Models for Smart City Energy Management Simulations," in IET Smart Grid, 2020, doi: 10.1049/iet-stg.2019.0296


BibTeX:
@article{FBR2020synthetic,
  title={Synthetic Residential Load Models for Smart City Energy Management Simulations},
  author={dos Reis, Fernando B. and Tonkoski, Reinaldo and Hansen, Timothy},
  journal={IET Smart Grid},
  year={2020},
  doi={10.1049/iet-stg.2019.0296},
  month = {February},
  publisher ={Institution of Engineering and Technology},
  copyright = {This is an open access article published by the IET under the Creative Commons Attribution			License (http://creativecommons.org/licenses/by/3.0/)			},
  url = {https://digital-library.theiet.org/content/journals/10.1049/iet-stg.2019.0296}
}
