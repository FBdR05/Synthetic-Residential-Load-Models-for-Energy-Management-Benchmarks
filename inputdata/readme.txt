The files in this folder are the inputs files for "main_queue.py".

load_data.h5 --> contains a mock data referring to the aggregated hourly energy consumption. The paper that describes the code made used of the ComEd utility aggregated hourly energy consumption. Data from "PJM. ‘PJM estimated hourly load’. Available from: http://www.pjm.com/markets-and-operations/energy/real-time/loadhryr.aspx"

The file contains time (as the index) and the hourly energy (Wh). Only time and hourly energy are present at the file. To read the file run "pandas.read_hdf('load_data.h5')".

ZIP_appliances.csv --> appliance ZIP characteristics from "Bokhari, A., Alkan, A., Dogan, R., Diaz.Aguiló, M., de León, F., Czarkowski, D., et al.: ‘Experimental Determination of the ZIP Coefficients for Modern Residential, Commercial, and Industrial Loads’, IEEE Transactions on Power Delivery, 2014, 29, (3), pp. 1372–1381"

The file contains "Ntest", "Po", "Qo", "Zp", "Ip", "Pp", "Zq", "Iq", "Pq", "Vcut", and "Vo". Where "Ntest" is the number of tested equipment’s; "Po" appliance active power (W) at nominal voltage; "Qo" appliance reactive power (VAR) at nominal voltage; "Zp", "Ip", "Pp" active power polynomial ZIP parameters; "Zq", "Iq", "Pq" reactive power polynomial ZIP parameters; "Vcut" lower bound voltage the appliance was tested (V); and "Vo" is the appliance nominal voltage (V). The rows on the file are a given appliance.

ZIP_spring.csv, ZIP_summer.csv, ZIP_winter.csv --> are the contributions the appliances have on each season. The rows in each of those files are a given appliance. The season of Fall has the same contributions as Spring. Contributions from "Bokhari, A., Alkan, A., Dogan, R., Diaz.Aguiló, M., de León, F., Czarkowski, D., et al.: ‘Experimental Determination of the ZIP Coefficients for Modern Residential, Commercial, and Industrial Loads’, IEEE Transactions on Power Delivery, 2014, 29, (3), pp. 1372–1381"

Each file contains the "A_index", "P_A", "P_B", "P_C", "P_D", "P_E", and "P_F". Where "A_index" is the appliances index; and "P_A", "P_B", "P_C", "P_D", "P_E", and "P_F" are the percentual contribution for each of the Stratum. Stratum are utilized to classify residential customers in Consolidated Edison Inc (the utility company of New York City) based on the customer annual peak power consumption. The Stratum are is not utilized in this paper. Thus, all customers are assumed Stratum D.

To read the ".csv" files run "pandas.read_csv('file_name.csv')".
