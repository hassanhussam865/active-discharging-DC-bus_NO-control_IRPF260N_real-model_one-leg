import sys
import traceback
import ltspice
import PyLTSpice
from PyLTSpice import SimCommander
from PyLTSpice import RawRead
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import axes3d
import os
from PyLTSpice import SimRunner, SpiceEditor, LTspice
import spicelib
import numpy as np
import pandas as pd
import time as tim
import plotly.graph_objects as go
# This is local commit

class RawFileWatcher:
    """
    Watches an LTspice .raw file and checks when it's ready to be parsed.
    """
    def __init__(self, filepath, stable_wait=1.0):
        self.filepath = filepath
        self.stable_wait = stable_wait  # seconds to wait between size checks

    def is_file_ready(self):
        """Check if file exists and its size is stable after a short delay."""
        if not os.path.exists(self.filepath):
            return False
        try:
            size1 = os.path.getsize(self.filepath)
            tim.sleep(self.stable_wait)
            size2 = os.path.getsize(self.filepath)
            return size1 == size2
        except Exception:
            return False

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for stream in self.streams:
            stream.write(message)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


# # to clear command window at begining
os.system('cls')


# Force another simulatior
simulator = r"C:\Program Files\ADI\LTspice\XVIIx64.exe"

# paths netlist
# filepath_net= r'.\source\active discharging DC bus 10 100 TI_fixed frequency_VarDuty.net'

# filepath_net= r'.\New folder (2)\source - Copy\active discharging DC bus_NO control_saturation region__2.net'

# filepath_net= r'.\New folder (2)\active discharging DC bus_NO control_C3M0040120K_real model_one switch.net'
filepath_net= r'.\New folder (2)\active discharging DC bus_NO control_IRPF260N_real model_one switch.net'


# paths netliOutputst
output_dir = './Outputs'
plot_path = './Outputs/plots'
# Define Excel file path (inside Output folder)
excel_path = os.path.join(output_dir, 'simulation_results.xlsx')
log_path = "./Outputs/simulation_log.txt"

log_file = open(log_path, "w", encoding="utf-8")

# Redirect stdout and stderr to both console and file
sys.stdout = Tee(sys.__stdout__, log_file)
sys.stderr = Tee(sys.__stderr__, log_file)



# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

netlist = spicelib.SpiceEditor(filepath_net)  # Loading the Netlist


## edit on netlist file ##


# # Save netlist file after edits
# Remove_all_instructions_netlist(filepath_net,filepath_temp_net)


# Define sweep ranges and Parameters
#sweeping from 10Hz to 100KHz
# Frequency_values = np.array([5455.59 , 8858.67, 14384.5 , 23357.21 , 37926.9 , 61584.82 , 100000])
# Frequency_values = np.array([8858.67])

# Frequency_values = np.linspace(1000, 10000,50)
# Frequency_values = np.array ([5040.81632653 , 5224.48979592,
#   5408.16326531 , 5591.83673469 , 5775.51020408 , 5959.18367347,
#   6142.85714286 , 6326.53061224 , 6510.20408163 , 6693.87755102,
#   6877.55102041 , 7061.2244898 ,  7244.89795918 , 7428.57142857,
#   7612.24489796 , 7795.91836735 , 7979.59183673 , 8163.26530612,
#   8346.93877551 , 8530.6122449  , 8714.28571429 , 8897.95918367,
#   9081.63265306 , 9265.30612245 , 9448.97959184 , 9632.65306122,
#   9816.32653061, 10000])


Tper_values = [1]

#sweeping from 0.01 to 1
# Duty_values = np.linspace(25, 100 ,74)
# Duty_values = np.arange(100, 176, 2)
# Duty_values = np.arange(2.4, 6.1, 0.1)

Duty_values = [10]

V_safe = 60
time_Vsafe_index_threshold = 0
Time_before_discharging = 5
list_Tper = []
list_Duty = []
list_Data = []
list_Time_Vsafe = []

k1 = 0.0322
k2 = -0.99
T0 = 60
SF = 1.2
tick = 5
Run_timeout = 3600.0

counter = 0
Running_Counter = (len(Tper_values)*len(Duty_values))
first_run_flag = 1 


# netlist.save_netlist(filepath_net)  # writes the modified netlist to the indicated file
# Set up simulation runner
# runner = SimRunner(output_folder= output_dir, simulator=LTspice)

for Tper in Tper_values:
    for Duty in Duty_values:
        print(f"Running sim with Tper={Tper}, Vctrl={Duty}")

        # Set parameters dynamically
        netlist.set_parameters(Tper=Tper, Vctrl=Duty)
        netlist.save_netlist(filepath_net)  # writes the modified netlist to the indicated file

        # Optional: Customize output name
        output_path = os.path.join(output_dir)

        # filepath_raw_out = r'.\Outputs\active discharging DC bus_NO control_C3M0040120K_real model_one switch_1.raw'
        filepath_raw_out = r'.\Outputs\active discharging DC bus_NO control_IRPF260N_real model_one switch_1.raw'

        # filepath_raw_out = r'.\Output\active discharging DC bus_NO control_saturation region__2_1.raw'

        if os.path.exists(filepath_raw_out):
            try:
                os.remove(filepath_raw_out)
                tim .sleep(5) 

            except PermissionError :
                print(f"❌ the Raw file is locked")
                x=1  
            
        runner = SimRunner(output_folder= output_path, simulator=LTspice ,timeout=Run_timeout)
        # time_sleep= (k1 * (Tper**k2) * SF) +T0 

        watch_raw_file = RawFileWatcher(filepath_raw_out , tick)

        # rawfile_status = watch_raw_file.is_file_ready()

        # rawfile_status = 0
        tim.sleep(1)  
        runner.run(filepath_net)

        watch_raw_file = RawFileWatcher(filepath_raw_out , tick)
        
        rawfile_status = watch_raw_file.is_file_ready()

        # counter = 0
        start_time = tim.time()  # Capture the start
        while not rawfile_status:
            # print("Raw file not ready yet.")
            elapsed = tim.time() - start_time
            # print(f"Counts = {counter}")
            print(f"⏳ Running in progress...Raw file not ready yet  {elapsed:.2f} seconds", end='\r', flush=True)
            # print(f"⏱️  Running in progress...Raw file not ready yet {counter}.", end='\r', flush=True)
            tim.sleep(1)
            rawfile_status = watch_raw_file.is_file_ready()

            if  rawfile_status:
                print("\n")
                print(f"✅ Raw file is ready to parse!")
                break


        # print("\n",output_path)
        
        # watcher.is_file_ready()  
        # incase of running the simulation it returns 0 
        # incase of finish the simulation it returns 1



        tim.sleep(20)        
        try :
            l = ltspice.Ltspice(filepath_raw_out)
            # Make sure that the .raw file is located in the correct path
            l.parse() 
            # x = input('')
            time = l.get_time()
            # print("time = " ,time)
        
            Tj_switching = l.get_data('V(tj_sw)')
            tj_switching_max = np.max(Tj_switching)
            tj_switching_max=np.array([1000])
            Vc_switching = l.get_data('V(v_dc)')
            time_Vsafe_index = np.where(Vc_switching <= V_safe) 
            print("time_Vsafe_index = " ,time_Vsafe_index)

            if len(time_Vsafe_index[0]) <= time_Vsafe_index_threshold  :
                    time_to_Vsafe = np.array([100])
                    print("time_Vsafe_index = " ,time_Vsafe_index[0])
                    # print ("Vc didn't reach Vsafe =" , )
            else:
                    time_to_Vsafe = time[np.min(time_Vsafe_index[0])]-Time_before_discharging
                    # time_to_Vsafe = 35
                    print ("time_to_Vsafe =" , time_to_Vsafe)
            list_Tper .append(Tper)
            list_Duty .append(Duty)
            list_Data.append([Tper, Duty, float(tj_switching_max) , float(time_to_Vsafe) ])

            # print("list_Data = " , list_Data)
            # add to excel during running
            # Define headers
            columns = ['Tper', 'Duty', 'Tj_max', 'Time_to_Vsafe']

            # Convert list_Data to DataFrame
            df = pd.DataFrame(list_Data, columns=columns)

            # Save to Excel
            df.to_excel(excel_path, index=False)

            print(f"✅ Data saved to Excel at Tper={Tper}, Duty={Duty} : {excel_path}")
            Running_Counter = Running_Counter -1
            print(f"✅ loading {Running_Counter} / {(len(Tper_values)*len(Duty_values)) }\n ")

        except Exception as er:
            # print("list_Data = " , list_Data)
            print("trace back = ",er)
            print("trace back = ",traceback.format_exc())
            print(f"❌ Error: The parsing of Raw file at Tper={Tper}, Duty={Duty} . Please close it and try again.")

############################################################
            if len(list_Data) < time_Vsafe_index_threshold  :
                    # print("time_Vsafe_index = " ,time_Vsafe_index[0])
                    print (f"❌ Vc didn't reach Vsafe =" )
            else:
                    time_to_Vsafe = time[np.min(time_Vsafe_index[0])]-Time_before_discharging
                    # print ("time_to_Vsafe =" , time_to_Vsafe)
                    list_Tper .append(Tper)
                    list_Duty .append(Duty)
                    list_Data.append([Tper, Duty, float(tj_switching_max) , float(time_to_Vsafe) ])
        # if (Running_Counter < 0) or (Running_Counter == 0) :
        #     break

#############################################################
# 1. Convert to numpy array

# try:
data = np.array(list_Data)
# 2. Extract columns
Tper_col            = data[:, 0]
Duty_col            = data[:, 1]
Tj_col              = data[:, 2]
time_Vsafe_col      = data[:, 3]

# 3. Get unique Tper and Duty values
Tper_vals  = np.unique(Tper_col)
Duty_vals  = np.unique(Duty_col)

# 4. Create meshgrid
X, Y = np.meshgrid(Tper_vals, Duty_vals)

# 5. Create Z matrix for Tj values
Z_Tj = np.full(X.shape, np.nan)
Z_Time_Vsafe = np.full(X.shape, np.nan)

# 6. Fill Z using data points
for t, d, Tj_val ,time_vsafe_val in list_Data:
    i = np.where(Duty_vals == d)[0][0]
    j = np.where(Tper_vals == t)[0][0]
    Z_Tj[i, j] = Tj_val
    Z_Time_Vsafe[i, j] = time_vsafe_val

#################################################################
# 3D plot for Temp_max and Time to Vasfe
colormaps = 'coolwarm'
edgecolors = 'k' # for black color

#fig 1 for Tj_max
fig = plt.figure(1)
ax = plt.axes(projection='3d')
surf = ax.plot_surface (X ,Y ,Z_Tj ,cmap= colormaps, edgecolor=edgecolors)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)

# html figure of Tj_max 
fig_html = go.Figure(data=[go.Surface(z=Z_Tj, x=X, y=Y)])

fig_html.update_layout(
    title="Tj_max 3D Surface Plot",
    title_x=0.5,  # Center the title
    scene=dict(
        xaxis_title="Tper (s)",
        yaxis_title="Duty",
        zaxis_title="Tj_max (°C)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        ),
        zaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        )
    ),
    margin=dict(l=10, r=10, t=50, b=10),
    height=700,
)

fig_html.write_html("Tj_max.html")

# Axis labels
ax.set_xlabel('Tper')
ax.set_ylabel('Duty')
ax.set_zlabel('Tj_max (°C)')

#fig 2 for time to Vsafe
fig = plt.figure(2)
ax = plt.axes(projection='3d')
surf = ax.plot_surface (X ,Y ,Z_Time_Vsafe ,cmap= colormaps, edgecolor= edgecolors)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)

# html figure of Time to Vsafe 
fig_html = go.Figure(data=[go.Surface(z=Z_Time_Vsafe, x=X, y=Y)])
fig_html.update_layout(
    title="Time to Vsafe 3D Surface Plot",
    title_x=0.5,  # Center the title
    scene=dict(
        xaxis_title="Tper (s)",
        yaxis_title="Duty",
        zaxis_title="Time to Vsafe (Sec)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        ),
        zaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False,
        )
    ),
    margin=dict(l=10, r=10, t=50, b=10),
    height=700,
)
fig_html.write_html("Time_Vsafe.html")

# Axis labels
ax.set_xlabel('Tper')
ax.set_ylabel('Duty ')
ax.set_zlabel('Time to Vsafe (Sec)')

# np.set_printoptions(threshold=np.inf)

print("Reading data done\n")

print(f"✅ Data saved to Excel at: {excel_path}")
# # open excel file when finished
os.startfile(excel_path)

plt.grid()
plt.show()


# except:
# print("list_Data = " ,list_Data)
# print (f"❌ list data error")


print("done\n")


# Close the log file
log_file.close()
