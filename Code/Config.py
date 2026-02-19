#Procedure:
#for MoStimulator, test stimulation first, always two adjacent pulses after connected
#udpate visualization parameters; BP filter?
#if set preset_seen_individuals_text
#if set manual_inputs_text
#GA setting: elitism no. (2), gen no. (10), gen size (12+8), select fixed amplitude, number of pulses (20) for each ind; 25 mins for experiment
#Configure LSL
#file name
#check two manual inputs
#check J definition

BaudRate=9600
port='COM3'

#-------visualization parameters--------
ta_show=0.01
tb_show=0.045
ya_show=180
yb_show=200
arti_amp=2000
dc_rem_start, dc_rem_end = 0.01, 0.004
#--------------------------------
#Standard setting: 130 Hz, pw = 60 μs, gap = 20 μs;

#preset_seen_individuals_text: no blank lines between each pair of parameters
preset_seen_individuals_text= """



 
"""

#130 60 #standard setting
#no blank lines between each pair of parameters
manual_inputs_text =  """

130 60


"""
#manual inputs are not restricted by preset_seen_individuals.
#manual_inputs=[]

eli=2 # elitism inds of each gen 

#selected_channels = ['R1','R2','R3','R4','R5','R6','R7','R8']
#selected_channels = ['L1','L2','L3','L4','L5','L6','L7','L8']
 
# ==================== broadcast via Matlab (pair) ==================== 
#ch_name, arti_amp='R6', 1000
#selected_channels = ['R1','R2','R3','R4','R5','R6','R7','R8']

# ==================== broadcast via Matlab (0613) ==================== 
#ch_name ='Lfp'
#selected_channels = ['Lfp','Ac2X','Ac2Y','Ac2Z']
 
#ch_name ,arti_amp='EOG', 1000
#elected_channels = ['EOG','ECG']
 

# ==================== KCL 22 Jun ==================== 
#ch_name='L6'
#selected_channels = ['R1','R2','R3','R4','R5','R6','R7','R8']
selected_channels = ['L1','L2','L3','L4','L5','L6','L7','L8']

 
#bandpass filter
f1=60
f2=600

#Initial settings
ini_freq=130
ini_pw=60 # 60 μs
ini_gap=20 # μs

ini_StimPolarity_a = 1 # 1 = positive polarity, 2 = negative polarity
ini_StimPolarity_b = 1 # 1 = positive polarity, 2 = negative polarity
ini_ramp=10 # Ramp time (ms)
ini_RampEnable = 1 # 1 = Ramp disable, 2 = ramp enable

ini_SignalType = 1 # normal charge balanced 
ini_StimOutput = 2 # 2 = normal stim mode; 4 = burst mode

up_amp=800
up_burst_interval=100
up_num_pulses=1

ch1_en_ini = 2 # 2 = enabled
ch2_en_ini = 1


t_before, t_after = 0.1, 0.15#ony for saved trace


# set limit [code]: DB$lim/4500;300;300;500;#
# set limit [explain]: Max Amp: 4500 µA; PulseWidth: 300 µs; GapWidth: 300 µs; Freq: 500 Hz

# set init [code]: DB$set/130;70;50; 1;1;10;1; 1;4;#
# set init [explain]: frequency, PulseWidth, GapWidth, CH1 Polarity, CH2 Polarity, Ramp time (ms), Ramp Enable, Signal Type, Stim Output (2: normal, 4: burst)

# burst update [code]: DB$upBst/130;70;50; 300;300; 1;2; 200;2;#
# burst update [explain]: frequency, PulseWidth, GapWidth, CH1 amp, CH2 amp, CH1 enable, CH2 enable, burst time (ms), no. of pulses

#selected_channels = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']#selected for compare ERNA, plots (disp and selection)
#stream_name='test_Broadcast2'#stream name to detect from LSL
 
#+---------------+----------------+------------------+
#|               | Max range      | Updating range   |
#+===============+================+==================+
#| Amplitude     | 100:10:4500 mA | 100:100:Max mA   |
#+---------------+----------------+------------------+
#| Pulse width   | 100:10:300 μs  | 20:5:max μs      |
#+---------------+----------------+------------------+
#| Gap width     | 20:10:300 μs   | 20:5:max μs      |
#+---------------+----------------+------------------+
#| Frequency     | 500 Hz         | 90:5:500 Hz      |
#+---------------+----------------+------------------+
#| Burst time    | NA             | 100:5/10:500 ms  |
#+---------------+----------------+------------------+
#| No. of pulses | NA             | 1-100            |
#+---------------+----------------+------------------+
 
ui_width=12 #fixed

ui_pad_x=40
ui_pad_y=2

bg_size_x = 620  # increased from 394
bg_size_y = 380  # GA height is 860
bg_size_y_ga=860

ws=4 # window size of real-time plot

limit_frequency = 500
limit_pulsewidth = 300
limit_amplitude = 4500
limit_gapwidth = 300

ta_plot=0.1# limit duration before event timing of ERNA buffer
tb_plot=0.15# limit duration after event timing of ERNA buffer

