#ver 15: update start and stop for real-time plot
#ver 16: decoration
#ver 17: good layout of console and plot
#ver 18: add channel selection for single plot
#ver 19: unify chunk source, add single selected channel display
#ver 20: simplify plotting code
#ver 21： update GA fields, simplify ui codes
#ver 22: combine GA module [need to be further improved]
#ver 23: improve GA parts [update logic, timing]
#ver 24: improve GA parts [prompts, timing]
#ver 25: deactivate start GA button after start;checked GA stimulation settings, save data (with more info)
#ver 26: added threshold to config. artiface threshold is saved
#ver 27: to add event by event
#ver 28: adjust event params positions, almost fix plotting regions
#ver 29: added stream and channel detection
#ver 30: fixed plots, real-time status monitor: plots title; gen, ind
#ver 31: added ERNA amp (on plots), freq
#ver 32: adjusted color, updated stimu settings for spinbox
#var 33: added spinbox to threshold,ta, tb, ya, yb (no manual inputs allowed)
#var 34: adjusted space (both plots and threshold)
#ver 35: combined rough GA, updated J with random values
#ver 36: updated J, to add manual inputs, updated saving dicts
#ver 37: added eli no. 
#ver 38: allowed one-channel stream
#ver 39: added 3D plot
#ver 40: added axes3D, updated y lim labels. updated for single-channel stream
#ver 41: test events/chunk sample counts
#ver 42: add ERNA amplitudes variation 
#ver 43: @21 May, test, add smooth
#ver 44: without stimulator: comment port in ini and close parts. updated channel index
#ver 45: test at KCL
#ver 46: updated bandpass filter
#ver 47: added dynamic amplitude, only filter of selected duration
#ver 48: added results filter based on clicking or not
#ver 49: added results compare, and save filtered
#ver 50: added paired pulse
#ver 51: updated paired pulse interval to erna duration, added log save
#ver 52: add receive samples status log, change layout of status label, saved events amps,
#ver 53： added plots to other stimu modes
#ver 54: adjusted saving for different modes.
#ver 55: updated GA for two params
#ver 56: added DC remove + rectify 
#ver 57: specified number of single pulses/bursts
#ver 58: added stimulaiton status  
#ver 59: updated ERNA detection method for first negative peak ERNA type; updated burst,sigle mode,
#ver 60: combined single mode and burst mode
#ver 61: updated pair
#ver 62: updated GUI, added reset plot button, added rectify
#ver 63: updated log reset, updated GA mode
#ver 63: to update continuous stimulation mode, remove heartbeat, keep writing
#ver 64: allow update setting when stimulating (except num of pulse decrease to 1 in non-continuous burst mode)
#ver 65： ~~
#ver 66： updated pw-based ta_erna/tb_erna
#ver 67: addded stop to update threshold, updated GA for saving info
#ver 68: updated J=erna_score-pw_score*0.1-freq_score*0.1
#ver 69: ensured top 2 with highest J, avoided duplicate inds (except manual inds), with full test
#ver 70： updated preset_seen_individuals
#ver 71: KCL
#ver 72: share with Alek
#ver 73: added 'Config LSL'
#ver 74: version at KCL @ 22 July
#ver 75: added multi-click in LSL window



#notes by Bo Yin:
#hearbeat prompts are hidden
#LSL data are saved to folder 'GA_LSL_Chunks' in the currenting working directory
#for each loop, only the last one threshold is saved for later analysis
#DC_remove is always applied to erna plot no matter it's ticked or not
#!!!!!!!!!!!!!!!if for Pure recording, any mode works except GA mode (which is reserved for GA evolution)
#configure selected channel before start.
#for GA mode, 2 pulses are reserved for test of ERNA detection params, so if you want 20 pulses, set 20+2=22


import os
current_folder = os.path.abspath(os.path.dirname(__file__))

import serial
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter  # for UI background
from tabulate import tabulate  # to show limit table (optional)
from MoStim import MoStim
from setup_ui import setup_ui
import Config
import numpy as np
import matplotlib.pyplot as plt
from mne_lsl.lsl import StreamInlet, resolve_streams
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from erna_receive import receive_chunks, bp_filter, notch_filter, erna_check2, event_detect_pair
from queue import Queue
#from GA_module import ga_generator
from GA_module_binary5 import ga_generator
import random
from mpl_toolkits.mplot3d import Axes3D
from erna_receive import rectify_sig, DC_remove
import pandas as pd
from tkinter import ttk
import sys

class StimulatorApp:
    def __init__(self, root):
        self.chunk_queue = Queue()
        self.ga_summary_records = []  # to store cumulative GA results
 
        self.root = root
        self.root.title("Stimulator via genetic algorithm (GA)")
      
        self.root.rowconfigure(30, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        
        # self.port = serial.Serial(Config.port, Config.BaudRate, timeout=0.1)
        
        self.runstim = False
        self.receiving = False
        self.runplot = False
        
        self.fonts_label=9

        self.total_event_plotted = 0  # Total number of ERNA events ever added
 
        self.selected_channel_name = tk.StringVar(value='') 
  
        setup_ui(self)

    
    def on_channel_change(self, *_):
        ch_name = self.selected_channel_name.get()
        
        # Prevent repeated print if channel name didn't change
        if hasattr(self, '_last_channel_name') and self._last_channel_name == ch_name:
            return  # no change
    
        self._last_channel_name = ch_name
        self.selected_channel_index = Config.selected_channels.index(ch_name)
        
        
        self.console_log(f'selected channel is changed to {ch_name}')

    def _apply_axis_font(self, axis):
        for label in axis.get_xticklabels():
            label.set_fontname("Helvetica")
            label.set_fontsize(self.fonts_label)
        for label in axis.get_yticklabels():
            label.set_fontname("Helvetica")
            label.set_fontsize(self.fonts_label)

    def _populate_option_menu(self, option_menu, variable, options, callback=None):
        menu = option_menu['menu']
        menu.delete(0, 'end')
        for option in options:
            command = tk._setit(variable, option, callback) if callback else tk._setit(variable, option)
            menu.add_command(label=option, command=command)

    def _build_analysis_cfg_snapshot(self):
        return {
            "freq": self.freq_var.get(),
            "pw": self.pw_var.get(),
            "gap": self.gap_var.get(),
            "amp": self.amp_var.get(),
            "burst_interval_default": self.burst_interval_var.get(),
            "burst_interval_stim": self.BstInter_var.get(),
            "num_pulses": self.num_pulses_var.get(),
            "mode": self.mode_var.get(),
            "file_name": self.file_name_var.get(),
            "ta_erna": float(self.ta_erna.get()),
            "tb_erna": float(self.tb_erna.get()),
            "ta_plot": float(self.ta_var.get()),
            "tb_plot": float(self.tb_var.get()),
            "ya_plot": float(self.ya_var.get()),
            "yb_plot": float(self.yb_var.get()),
            "selected_channel": self.selected_channel_name.get() if hasattr(self, "selected_channel_name") else "unknown",
            "bp_filter_applied": self.bp_filter_var.get() if hasattr(self, "bp_filter_var") else False,
            "bp_low": float(self.bp_f1.get()) if hasattr(self, "bp_f1") else 0.0,
            "bp_high": float(self.bp_f2.get()) if hasattr(self, "bp_f2") else 0.0,
            "bp_order": int(self.bp_n.get()) if hasattr(self, "bp_n") else 2,
            "arti_amp": int(self.arti_amp_var.get()) if hasattr(self, "arti_amp_var") else int(Config.arti_amp),
            "rectify": self.Rectify_var.get() if hasattr(self, "Rectify_var") else False,
        }

    def _get_current_threshold(self):
        try:
            return int(self.arti_amp_var.get())
        except ValueError:
            return Config.arti_amp

    def _compute_plot_ylim(self, data):
        y_min = np.min(data)
        y_max = np.max(data)
        if y_min == y_max:
            margin = abs(y_min) * 0.1 if y_min != 0 else 1
            return y_min - margin, y_max + margin

        max_abs = max(abs(y_min), abs(y_max))
        margin = max_abs * 0.1
        return -max_abs - margin, max_abs + margin
        
    def start_plotting_and_streaming(self):

        def plotting_loop():
            while self.runplot:
                try:
                    chunk, timestamps = self.inlet.pull_chunk(timeout=1)
                    #chunk, timestamps = self.inlet.pull_chunk(timeout=1.0, max_samples=4096)
                    if chunk.size > 0:
                        chunk_data = np.array(chunk).T  # shape: (channels, samples)
                        self.chunk_queue.put(chunk_data)
                        ch_idx = self.selected_channel_index
                        
                        fs = self.fs 
    
                        # Update plot data
                        self.plot_data = np.roll(self.plot_data, -len(chunk_data[ch_idx]))#****************************************
                        inter=chunk_data[ch_idx]

                        if hasattr(self, 'DC_remov_var') and self.DC_remov_var.get():
                            inter = DC_remove(inter)
                        if hasattr(self, 'Rectify_var') and self.Rectify_var.get():
                            inter = rectify_sig(inter)
                        
                        self.plot_data[-len(chunk_data[ch_idx]):] = inter
                        # Update plot visuals (on UI thread)
                        def refresh_plot():
                            self.plot_line.set_ydata(self.plot_data)#****************************************

                            current_val = self._get_current_threshold()
                            self.threshold_line.set_ydata([current_val] * len(self.plot_data))

                            y_min, y_max = self._compute_plot_ylim(self.plot_data)
                            self.ax.set_ylim([y_min, y_max])
                            #self.canvas.draw_idle()
                            self.canvas.draw()
                        self.root.after(0, refresh_plot)
                        # Push to queue for ERNA

                        #below is for event plot
                        fs = self.fs

                        signal = DC_remove(chunk_data[ch_idx])
                        self.signal_buffer = np.concatenate((self.signal_buffer, signal))

                        ta = Config.ta_plot
                        tb = Config.tb_plot
                        n_before = int(ta * fs)
                        n_after = int(tb * fs)
                        total_len = n_before + n_after
                        
                        if hasattr(self, 'Rectify_var') and self.Rectify_var.get():
                            rising_edges = event_detect_pair(self,rectify_sig(self.signal_buffer), fs)
                        else:
                            rising_edges = event_detect_pair(self,self.signal_buffer, fs)
                        
                        # Extract valid segments
                        self.event_buffer = []
                        for edge in rising_edges:
                            if edge - n_before >= 0 and edge + n_after < len(self.signal_buffer):
                                seg = self.signal_buffer[edge - n_before: edge + n_after]#****************************************
                                if len(seg) == total_len:
                                    #seg=smooth_filter(seg,fs,Config.smooth_size,Config.envelop_size)
                                    self.event_buffer.append(seg)#****************************************
                                    #if len(self.event_buffer) > 10:
                                        #self.event_buffer.pop(0) # Removes the oldest segment (at index 0)  
                        
                        # Keep a tail of buffer (for future overlap)
                        #self.signal_buffer = self.signal_buffer[-fs * 20:]  # 4 seconds of context
                        # Update event plot
                        self.root.after(0, self.update_event_plot)
                except Exception as e:
                    print(f"Error in unified plot/stream loop: {e}")
                    break

        self.runplot = True
        self.plot_thread = threading.Thread(target=plotting_loop, daemon=True)
        self.plot_thread.start()
    
    def setup_stimulator(self):
        self.stimulator = MoStim()

        # Send limits
        limit_message = self.stimulator.get_limit_message()
        #print(f"✅ [LIMIT] Sending: {limit_message}")
        self.port.write(f"{limit_message}\n".encode())
        response = self.port.readline().decode().strip()
        #print(f"✅ [Response of limit] {response}")

        # Send init setup
        ramp_time = self.ramp_var.get()
        ramp_enable=self.ramp_OnOff.get()
        burst_init_msg = self.stimulator.get_init_message(ramp_time, ramp_enable)

        #print(f"✅ [INIT] Sending: {burst_init_msg}")
        self.port.reset_input_buffer()
        self.port.write(f"{burst_init_msg}\n".encode())
        response = self.port.readline().decode().strip()
        #print(f"✅ [Response of init] {response}")
 

    def stimulation_loop(self):
        """Main thread to handle stimulation"""
        heartbeat_msg = self.stimulator.heartbeat()
        tHeart = 1.0
        t_start2 = time.time()
        

        try:
            mode = self.mode_var.get()
            freq = self.freq_var.get()
            pw = self.pw_var.get()#µs
            gap = self.gap_var.get()#µs
            amp = self.amp_var.get()
            burst_interval = self.burst_interval_var.get()#ms
            num_pulses = self.num_pulses_var.get()

            # Use channel enable defaults (can be enhanced later)
            ch1_en = Config.ch1_en_ini
            ch2_en = Config.ch2_en_ini
                
            if mode == "Burst" and num_pulses!=1:
                
                if self.cBst_var.get():#continuous burst mode
                    burst_interval = self.BstInter_var.get()#ms
                    self.update_msg = self.stimulator.get_burst_update_message(freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)
                
                    self.port.write(f"{self.update_msg}\n".encode())
                    
                    while self.runstim:

                        if time.time() - t_start2 > 1:
                            t_start2 = time.time()
                            self.port.write(f"{self.update_msg}\n".encode())
                    
                else:
                    
                    self.update_msg = self.stimulator.get_burst_update_message(freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)

                    #for burst mode, if not default mode, the minimal good interval with randomness is 250 ms
                    
                    total_num=self.StiNum_var.get()
                    bst_len=num_pulses*(pw/1000000*2+gap/1000000)+(num_pulses-1)*burst_interval/1000
     
                    for i in range(total_num):
                         
                        
                        freq = self.freq_var.get()
                        pw = self.pw_var.get()#µs
                        gap = self.gap_var.get()#µs
                        amp = self.amp_var.get()
                        burst_interval = self.burst_interval_var.get()#ms
                        num_pulses = self.num_pulses_var.get()
                        self.update_msg = self.stimulator.get_burst_update_message(freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)

                         
                        self.setup_stimulator()
                        print(f"✅ [UPDATE{i+1}] Sending: {self.update_msg}")
                        self.pass_var.set(f'{i+1}') 
                        self.port.write(f"{self.update_msg}\n".encode())
                        time.sleep(1.5*bst_len)#minimal effective burst interval is 1.5*bst_len
                        #1.5 is used in case more than one burst [burst is usually generated at end of the interval]
                        self.stop_stimulation()  
                        rand_offset=random.randint(-self.Rand_var.get(),self.Rand_var.get())/100
                        rand_inter=self.BstInter_var.get()*(1+rand_offset)/1000#BstInter_var-ms
                        time.sleep(max(-1.5*bst_len+rand_inter-0.025,0))#0.025 is the empirical delay
                
 
            elif mode == "Burst" and num_pulses==1:
                self.update_msg = self.stimulator.get_single_update_message(pw, gap, amp, ch1_en, ch2_en)
                total_num=self.StiNum_var.get()
                for i in range(total_num):
                    freq = self.freq_var.get()
                    pw = self.pw_var.get()#µs
                    gap = self.gap_var.get()#µs
                    amp = self.amp_var.get()
                    burst_interval = self.burst_interval_var.get()#ms
                    num_pulses = self.num_pulses_var.get()
                    #self.update_msg = self.stimulator.get_burst_update_message(freq, pw, gap, amp, burst_interval, num_pulses)
                    self.update_msg = self.stimulator.get_single_update_message(pw, gap, amp, ch1_en, ch2_en)
                     
                    self.setup_stimulator()
                    print(f"✅ [UPDATE{i+1}] Sending: {self.update_msg}")
                    self.pass_var.set(f'{i+1}') 
                    self.port.write(f"{self.update_msg}\n".encode())
                    rand_offset=random.randint(-self.Rand_var.get(),self.Rand_var.get())/100
                    time.sleep(self.BstInter_var.get()*(1+rand_offset)/1000)
                    self.stop_stimulation()    
                        
 
            elif mode == "Continuous":
                self.update_msg = self.stimulator.get_continuous_update_message(freq, pw, gap, amp, ch1_en, ch2_en)
                print(f"✅ [UPDATE] Sending: {self.update_msg}")
                self.port.write(f"{self.update_msg}\n".encode())
                
                while self.runstim:
                    if time.time() - t_start2 > 1:
                        t_start2 = time.time()
                        #self.port.write(f"{self.update_msg}\n".encode())
                        self.port.write(f"{heartbeat_msg}\n".encode())#keep writing doesn't work
                
                
            elif mode == "GA":
                self.update_msg = self.stimulator.get_burst_update_message(freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)
                total_num=self.StiNum_var.get()
                bst_len=num_pulses*(pw/1000000*2+gap/1000000)+(num_pulses-1)*burst_interval/1000
 
                for i in range(total_num):
                    #if i== 2:
                        #input('Have you corrected the arti-threshold/ERNA duration? (Press Enter to continue...)')   
                    self.setup_stimulator()
                    print(f"✅ [UPDATE{i+1}] Sending: {self.update_msg}")
                    self.pass_var.set(f'{i+1}') 
                    self.port.write(f"{self.update_msg}\n".encode())
                    time.sleep(1.5*bst_len)#minimal effective burst interval is 1.5*bst_len
                    #1.5 is used in case more than one burst [burst is usually generated at end of the interval]
                    self.stop_stimulation()  
                    rand_offset=random.randint(-self.Rand_var.get(),self.Rand_var.get())/100
                    rand_inter=self.BstInter_var.get()*(1+rand_offset)/1000#BstInter_var-ms
                    time.sleep(max(-1.5*bst_len+rand_inter-0.025,0))#0.025 is the empirical delay

            else:
                raise ValueError("Unknown mode selected")

        except Exception as e:
            print(f"[ERROR] Failed to send update command: {e}")


        #while self.runstim and mode != 'Single' or (mode == 'Burst' and self.cBst_var.get()):
            #if time.time() - t_start2 > tHeart:
                #t_start2 = time.time()
                #self.port.write(f"{heartbeat_msg}\n".encode())
    

    def start_stimulation(self):
        self.runstim = True
        #self.start_btn.config(state=tk.DISABLED)
        #self.stop_btn.config(state=tk.NORMAL)
        self.setup_stimulator() #
        self.stim_thread = threading.Thread(target=self.stimulation_loop, daemon=True) #
        self.stim_thread.start()

    def stop_stimulation(self):
        self.runstim = False
        #self.start_btn.config(state=tk.NORMAL)
        #self.stop_btn.config(state=tk.DISABLED)
        stop_msg = self.stimulator.shutdown()
        #print(f"✅<<< Stop stimulation, sending: {stop_msg}")
        self.port.write(f"{stop_msg}\n".encode())
        
    def update_stimulation_from_ui(self):
        if not self.runstim:
            return  # Only update if stimulation is running
    
        try:
            mode = self.mode_var.get()
            freq = self.freq_var.get()
            pw = self.pw_var.get()
            gap = self.gap_var.get()
            amp = self.amp_var.get()
            burst_interval = self.burst_interval_var.get()
            num_pulses = self.num_pulses_var.get()
    
            ch1_en = Config.ch1_en_ini
            ch2_en = Config.ch2_en_ini
            
            
    
            if mode == "Burst":
                if self.cBst_var.get():#continuous burst mode
                    burst_interval = self.BstInter_var.get()#ms
                    
                self.update_msg = self.stimulator.get_burst_update_message(
                    freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)
                
            elif mode == "Continuous":
                self.update_msg = self.stimulator.get_continuous_update_message(
                    freq, pw, gap, amp, ch1_en, ch2_en)
            
            elif mode == "GA":
                self.update_msg = self.stimulator.get_burst_update_message(
                    freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses)
            else:
                return
    
            
            if mode == 'Continuous':
                self.port.write(f"{self.update_msg}\n".encode())
            #response = self.port.readline().decode().strip()
            print(f"✅ update: {self.update_msg}")
            #print(f"✅ [Auto-Update] Response: {response}")
    
        except Exception as e:
            print(f"[Auto-Update ERROR] {e}")

        
    def start_receiving_chunks(self, generation=None, individual=None):
        self.receiving = True
        self.runplot = True
        self.file_name_entry.config(state='disabled')
        
        def log(msg):
            self.console_log(msg)
    
        # Setup LSL inlet
        #streams = resolve_streams('name', self.selected_stream_name.get())
        #streams = resolve_streams(f"name='{self.selected_stream_name.get()}'")
        
        stream_name = self.selected_stream_name.get()
        streams = resolve_streams(timeout=2.0, name=stream_name)
        if not streams:
            self.console_log(f"⚠️ Stream '{stream_name}' not found.")
            self.receiving = False
            self.runplot = False
            self.file_name_entry.config(state='normal')
            self.stop_receive_btn.config(state=tk.DISABLED)
            self.receive_btn.config(state=tk.NORMAL)
            return

        selected_stream = next((s for s in streams if s.name == stream_name), streams[0])

        #time.sleep(0.5)
        self.inlet = StreamInlet(selected_stream)
        self.inlet.open_stream()
        info = self.inlet.get_sinfo()
        fs = int(info.sfreq)
        n_channels = info.n_channels
        
        self.console_log(f"✅ Connected to stream '{info.name}' with {n_channels} channels @ {fs} Hz")

        #start plotting
        self.create_plot_canvas(fs)    
        self.create_event_plot_canvas(fs)
        self.create_amp_plot_canvas(fs)
        self.start_plotting_and_streaming()
        self.stop_receive_btn.config(state=tk.NORMAL)
        self.receive_btn.config(state=tk.DISABLED)
        #self.detect_button.config(state=tk.DISABLED)

        analysis_cfg = self._build_analysis_cfg_snapshot()

        # ERNA Detection
        def receive_loop():
            try:
                info = self.inlet.get_sinfo()
                fs = int(info.sfreq)
        
                self.save_folder = os.path.join(os.getcwd(), "GA_LSL_Chunks")
                os.makedirs(self.save_folder, exist_ok=True)
        
                receive_chunks(self,log,self.chunk_queue,fs,lambda: self.receiving,
                    save_dir=self.save_folder,gen=generation,ind=individual,info=info,analysis_cfg=analysis_cfg)
            finally:
                self.console_log("✅ Finished ERNA analysis.")
    
        self.receive_thread = threading.Thread(target=receive_loop, daemon=True)
        self.receive_thread.start()
    
    def stop_receiving_chunks(self):
        self.console_log("✅<<< Stop receiving chunks ...")
        self.receiving = False
        self.runplot = False

        self.stop_receive_btn.config(state=tk.DISABLED)
        self.receive_btn.config(state=tk.NORMAL)
        self.file_name_entry.config(state='normal')
        #self.detect_button.config(state=tk.NORMAL)

    def _append_console_log(self, message):
        print(message)  # Console
        self.log_lines = (self.log_lines + [message])[-6:]
        self.log_label.config(text="\n".join(self.log_lines))
        self.log_history.append(message)

    def console_log(self, message):
        if threading.current_thread() is threading.main_thread():
            self._append_console_log(message)
        else:
            self.root.after(0, lambda msg=message: self._append_console_log(msg))

    def create_plot_canvas(self, fs):

        for widget in self.plot_raw.winfo_children():
            widget.destroy()

        self.selected_channel_index = Config.selected_channels.index(self.selected_channel_name.get())

        #fig setup
        self.fig = Figure(figsize=(5.6, 0.95), dpi=100)
        self.fig.patch.set_facecolor('none')
         
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.patch.set_facecolor('none')
        self.ax.set_xlim([0, Config.ws])
        self.ax.set_ylim([-1, 1])
        self.ax.grid(True)
        #self.ax.set_xlabel("t (s)", fontname='Helvetica',fontsize=9)
        self.ax.set_ylabel("Amp (µA)", fontname='Helvetica',fontsize=self.fonts_label)
        self._apply_axis_font(self.ax)
            
        self.fig.subplots_adjust(left=0.12, right=0.98, top=0.95, bottom=0.2)

        self.plot_data = np.zeros(fs * Config.ws)
        self.plot_line, = self.ax.plot(np.linspace(0, Config.ws, fs * Config.ws), self.plot_data, color='blue')
        self.threshold_line = self.ax.plot(np.linspace(0, Config.ws, fs * Config.ws),
            [Config.arti_amp] * int(fs * Config.ws),color='red',linestyle='--',label='Threshold')[0]
        #self.ax.legend(loc='upper right', prop={'family': 'Helvetica', 'size': 9})
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_raw)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.place(x=5, y=0, width=540, height=98)
        canvas_widget.configure(bg=self.plot_raw.cget("bg"), highlightthickness=0, bd=0)#!
        #canvas_widget.grid(row=0, column=0, sticky="nsew")

        self.selected_channel_name.trace_add("write", self.on_channel_change)
      
    def create_event_plot_canvas(self, fs):
        # Clear old widgets if re-creating
        for widget in self.plot_event.winfo_children():
            widget.destroy()
    
        self.fs = fs
        self.event_buffer = []
        self.signal_buffer = np.array([])
        
        #fig setup
        self.event_fig = Figure(figsize=(5.65, 1.35), dpi=100)
        self.event_fig.patch.set_facecolor('none')
        
        self.event_ax = self.event_fig.add_subplot(111)
        self.event_ax.grid(True)
        self.event_ax.set_facecolor('none')
        
        #self.event_ax.set_xlabel("t (s)", fontname='Helvetica',fontsize=9)
        self.event_ax.set_ylabel("Amp (µA)", fontname='Helvetica',fontsize=self.fonts_label)
        self._apply_axis_font(self.event_ax)
        self.event_fig.subplots_adjust(left=0.12, right=0.97, top=0.95, bottom=0.15)
        
        self.event_canvas = FigureCanvasTkAgg(self.event_fig, master=self.plot_event)
        canvas_widget = self.event_canvas.get_tk_widget()
        canvas_widget.place(x=5, y=0, width=545, height=162)
        canvas_widget.configure(bg=self.plot_raw.cget("bg"), highlightthickness=0, bd=0)#!


        # Make sure the frame allows canvas expansion
        self.plot_event.rowconfigure(0, weight=1)
        self.plot_event.columnconfigure(0, weight=1)
        self.plot_event.grid_propagate(False)
        
    def create_amp_plot_canvas(self, fs):
        # Clear old widgets if re-creating
        for widget in self.plot_amp.winfo_children():
            widget.destroy()
    
        self.fs = fs
        self.amp_buffer = []

        self.amp_fig = Figure(figsize=(4.0, 1.35), dpi=100)
        self.amp_fig.patch.set_facecolor('none')
        
        self.amp_ax = self.amp_fig.add_subplot(111)
        self.amp_ax.grid(True)
        self.amp_ax.set_facecolor('none')
        
        #self.event_ax.set_xlabel("t (s)", fontname='Helvetica',fontsize=9)
        self.amp_ax.set_ylabel("Amp (µA)", fontname='Helvetica',fontsize=self.fonts_label)
        self._apply_axis_font(self.amp_ax)
        self.amp_fig.subplots_adjust(left=0.15, right=0.98, top=0.95, bottom=0.17)
        
        self.amp_canvas = FigureCanvasTkAgg(self.amp_fig, master=self.plot_amp)
        canvas_widget = self.amp_canvas.get_tk_widget()
        canvas_widget.place(x=5, y=0, width=393, height=120)
        canvas_widget.configure(bg=self.plot_amp.cget("bg"), highlightthickness=0, bd=0)#!


        # Make sure the frame allows canvas expansion
        self.plot_amp.rowconfigure(0, weight=1)
        self.plot_amp.columnconfigure(0, weight=1)
        self.plot_amp.grid_propagate(False)
        
    
    def update_event_plot(self):
        if not hasattr(self, "event_ax"):
            return
    
        self.event_ax.clear()
        self.event_ax.grid(True)
    
        ta = float(self.ta_var.get())
        tb = float(self.tb_var.get())
        ya = float(self.ya_var.get())
        yb = float(self.yb_var.get())
        erna_t1 = float(self.ta_erna.get())
        erna_t2 = float(self.tb_erna.get())
        arti = int(self.arti_amp_var.get())
        fs = self.fs
        n_before = int(Config.ta_plot * fs)
        n_after = int(Config.tb_plot * fs)
        total_len = n_before + n_after
        time_axis = np.linspace(-Config.ta_plot, Config.tb_plot, total_len)
    
        self.event_ax.set_xlim(-ta, tb)
        self.event_ax.set_ylim(-ya, yb)
        self.event_ax.set_ylabel("Amp (µA)", fontname='Helvetica', fontsize=self.fonts_label)
        self._apply_axis_font(self.event_ax)
    
        if self.event_buffer:
            fa, fb, order = self.bp_f1.get(), self.bp_f2.get(), self.bp_n.get()
            filtered_traces = []
            
            #plot 10 latest events
            recent_traces = self.event_buffer[-10:]#****************************************
            for trace in recent_traces:
                if hasattr(self, 'bp_filter_var') and self.bp_filter_var.get():
                    # Apply partial filtering only in ERNA window
                    trace_copy = trace.copy()
                    idx1 = int((erna_t1 + Config.ta_plot) * fs)
                    idx2 = int((erna_t2 + Config.ta_plot) * fs)
                    #print(f'erna_t1:{erna_t1},erna_t2:{erna_t2},idx1:{idx1},idx2:{idx2}~~~~~~~~~~~~~~~')
                    if 0 <= idx1 < idx2 <= total_len:
                        filtered_section = bp_filter(trace_copy[idx1:idx2], fs, fa, fb, order)
                        trace_copy[idx1:idx2] = filtered_section
                    self.event_ax.plot(time_axis, trace_copy, color='gray', alpha=0.4)#****************************************
                else:
                    self.event_ax.plot(time_axis, trace, color='gray', alpha=0.4)#****************************************

            self.amp_erna_list = []
            #evaluate amps of all events
            for trace in self.event_buffer:
                if hasattr(self, 'bp_filter_var') and self.bp_filter_var.get():
                    # Apply partial filtering only in ERNA window
                    trace_copy = trace.copy()
                    idx1 = int((erna_t1 + Config.ta_plot) * fs)
                    idx2 = int((erna_t2 + Config.ta_plot) * fs)
                    if 0 <= idx1 < idx2 <= total_len:
                        filtered_section = bp_filter(trace_copy[idx1:idx2], fs, fa, fb, order)
                        trace_copy[idx1:idx2] = filtered_section
                    #self.event_ax.plot(time_axis, trace_copy, color='gray', alpha=0.4)
                    filtered_traces.append(trace_copy)
                    result_filtered = erna_check2(trace_copy, fs, Config.ta_plot, erna_t1, erna_t2, time_axis)
                    if result_filtered:
                        amp_pos1, amp_neg1, amp_pos2, t1, t2, t3, lag, f_erna, latency = result_filtered
                        amp_erna = amp_pos1 - amp_neg1
                        self.amp_erna_list.append(amp_erna)#****************************************
                        
                else:
                    #self.event_ax.plot(time_axis, trace, color='gray', alpha=0.4)
                    filtered_traces.append(trace)
                    result_nonfiltered = erna_check2(trace, fs, Config.ta_plot, erna_t1, erna_t2, time_axis)
                    if result_nonfiltered:
                        amp_pos1, amp_neg1, amp_pos2, t1, t2, t3, lag, f_erna, latency = result_nonfiltered
                        amp_erna = amp_pos1 - amp_neg1
                        self.amp_erna_list.append(amp_erna)#****************************************
                        

            mean_trace = np.mean(filtered_traces[-10:], axis=0)
            
            self.event_ax.plot(time_axis, mean_trace, color='red', linewidth=2)#****************************************
            self.event_ax.plot([erna_t1, erna_t1], [-arti, arti], 'm--', linewidth=2)
            self.event_ax.plot([erna_t2, erna_t2], [-arti, arti], 'm--', linewidth=2)
            
            result_mean = erna_check2(mean_trace, fs, Config.ta_plot, erna_t1, erna_t2, time_axis)
            if result_mean:
                amp_pos1, amp_neg1, amp_pos2, t1, t2, t3, lag, f_erna, latency = result_mean
                self.event_ax.plot(t1, amp_pos1, 'ro')
                self.event_ax.plot(t2, amp_neg1, 'bo')
                #self.event_ax.plot(t3, amp_pos2, 'go')
                self.last_erna_score = amp_pos1 - amp_neg1
                #print (f'ERNA: amplitude {amp_pos1-amp_neg1:.1f}')
                # Update status label
                #status_msg = (f" Amp= {amp_pos1:.1f} + {-amp_neg1:.1f} = {amp_pos1-amp_neg1:.1f}, P2: {amp_pos2:.1f}, f_ERNA: {f_erna:.1f} Hz")
                
                status_msg = (f" ERNA Monitor:\n • Mean amp: {amp_pos1-amp_neg1:.1f} µA \n • Freq: {f_erna:.1f} Hz \n • Event: {len(self.amp_erna_list)}")
                self.status_var2.set(status_msg) 

            # Use the mean trace for visual markers if any results found
            if self.amp_erna_list:
                #if not hasattr(self, 'amp_buffer'):
                    #self.amp_buffer = []
                

                self.update_amp_plot()
    
        self.event_canvas.draw()

    def update_amp_plot(self):
        if not hasattr(self, "amp_ax"):
            return
    
        self.amp_ax.clear()
        self.amp_ax.grid(True)
        self.amp_ax.set_facecolor('none')
        self.amp_ax.set_ylabel("Amp (µA)", fontname='Helvetica', fontsize=self.fonts_label)
        self._apply_axis_font(self.amp_ax)
    
        if self.amp_erna_list:
            # Always keep only the last 50 entries
            self.amp_erna_list_total=self.amp_erna_list
            if len(self.amp_erna_list) > 50:
                self.amp_erna_list = self.amp_erna_list[-50:]
    
            num_vals = len(self.amp_erna_list)
            # Determine the logical start index (for x-axis labeling)
            start_index = max(1, len(self.amp_erna_list_total) - num_vals + 1) if hasattr(self, 'amp_erna_list_total') else 1
    
            # Track full history for accurate x tick labeling
            if not hasattr(self, 'amp_erna_list_total'):
                self.amp_erna_list_total = []
            self.amp_erna_list_total.extend(self.amp_erna_list[-(num_vals - len(self.amp_erna_list_total)):] if len(self.amp_erna_list_total) < len(self.amp_erna_list) else [])
    
            x_vals = list(range(start_index, start_index + num_vals))
            y_vals = self.amp_erna_list#****************************************
    
            self.amp_ax.plot(x_vals, y_vals, marker='o', color='green', linewidth=1, markersize=4)#****************************************
            self.amp_ax.set_xlim(start_index - 1, start_index + 50)
    
            base_ticks = [1, 10, 20, 30, 40, 50]
            tick_labels = [t + start_index - 1 for t in base_ticks]
            self.amp_ax.set_xticks(tick_labels)
    
            # Y-axis scaling
            y_max = max(y_vals)
            margin = 20 if y_max > 0 else 1
            raw_top = y_max + margin
            tick_spacing = int(np.ceil(raw_top / 4 / 10.0)) * 10
            top_tick = tick_spacing * 4
    
            self.amp_ax.set_ylim(0, top_tick)
            self.amp_ax.set_yticks(np.arange(0, top_tick + 1, tick_spacing))
    
        self.amp_canvas.draw()

    def _show_ga_progress_plot(self, gen, current_individual, previous_individuals):
        """Render GA scatter plot on the Tk main thread."""
        try:
            fig = plt.figure(figsize=(6, 5))
            ax = fig.add_subplot(111)
            ax.set_title(f"Generation {gen} - Individuals (2D)")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Pulse Width (µs)")

            # Keep axes stable across individuals.
            ax.set_xlim(90, 145)
            ax.set_ylim(20, 100)

            if previous_individuals:
                prev = np.array(previous_individuals)
                ax.scatter(prev[:, 0], prev[:, 1], c='gray', label="Previous")
                ax.plot(prev[:, 0], prev[:, 1], c='gray', linewidth=1)

            ax.scatter(current_individual[0], current_individual[1], c='red', s=50, label="Current")
            ax.legend()
            fig.tight_layout()

            plt.show(block=False)
            self.root.after(1500, lambda f=fig: plt.close(f))
        except Exception as e:
            print(f"[2D PLOT ERROR] {e}")

    
    def start_ga_process(self):
        def ga_loop():
            all_prev_individuals = []
    
            for params in ga_generator(Config.manual_inputs_text):
                
                gen = params['generation']
                ind = params['individual']
                current_individual = (params['freq'], params['pw'], params['amp'])
    
                prev_snapshot = list(all_prev_individuals)
                self.root.after(
                    0,
                    lambda g=gen, cur=current_individual, prev=prev_snapshot:
                        self._show_ga_progress_plot(g, cur, prev)
                )
    
                # Store for next gen
                all_prev_individuals.append(current_individual)
    
                # === GUI + GA ===
                self.console_log(f"===== Gen {gen} - Ind {ind} =====")
                self.root.after(0, lambda g=gen, i=ind: self.status_var.set(f" Evolution Progress:\n • Gen: {g}, Ind: {i}"))
                self.console_log(f"✅ Freq: {params['freq']} Hz, PW: {params['pw']} µs, Amp: {params['amp']} µA")
    
                self.freq_var.set(params['freq'])
                self.pw_var.set(params['pw'])
                self.gap_var.set(params['gap'])
                self.amp_var.set(params['amp'])
                self.burst_interval_var.set(params['burst_interval'])
                self.num_pulses_var.set(params['num_pulses'])
                
                self.reset_btn.invoke()
 
                self.start_receiving_chunks(generation=gen, individual=ind)
                
                time.sleep(0.5)
                self.console_log(f"✅ >>> Prepare stimulation ({self.StiNum_var.get()} bursts)...")
                
                self.start_stimulation()
                
       
                self.stim_thread.join()
                time.sleep(0.1)
                
                user_input='nothing'
                user_input =input('Receiving in progress ... (i) Adjust parameters? (ii) Reset J? [Press Enter to continue/ Press 1 to set J as -inf/ Press 2 to customize J]') 
 
                self.stop_receiving_chunks()
       
    
                time.sleep(2.0)#to wait for plotting
    
                ind_obj = params.get("ind_obj")
                if ind_obj:
                    erna_score = getattr(self, "last_erna_score", None)
                    if erna_score is None:
                        erna_score = -999999999  # No ERNA detected
                            
                    pw_score = self.pw_var.get()
                    freq_score = self.freq_var.get()
                    
                    #J=erna_score-pw_score*0.1-freq_score*0.1
                    J=erna_score 
                    
                    if user_input.strip() == '1':
                        J = -999999999  # Penalize this individual
                        self.console_log("User-adjusted: Fitness set to -999")
                    
                    if user_input.strip() == '2':
                        J =int(input('Please input J: '))
                    ind_obj.fitness.values = (J, )
                    print(f"✅ [GA Evaluation ** ] Fitness = {ind_obj.fitness.values[0]:.3f}")
                    
                    # === Save to GA Summary ===
                    sorted_flag = 33  # placeholder, can be updated if GA sorting is applied
                    record = {
                        "Generation": gen,
                        "Individual (Eval Order)": ind,
                        "Sorted": sorted_flag,
                        "Frequency (Hz)": params["freq"],
                        "Pulse Width (µs)": params["pw"],
                        "ERNA amp": erna_score,
                        "Fitness (J)": J
                    }
                    self.ga_summary_records.append(record)
                    
                    # === Save to Excel ===
                    df = pd.DataFrame(self.ga_summary_records)
                    excel_filename = self.file_name_var.get()+f"_summary_Gen{gen:02d}.xlsx"
                    
                    self.save_folder = os.path.join(os.getcwd(), "GA_LSL_Chunks")
                    excel_path = os.path.join(self.save_folder,excel_filename)
                    
                    
                   
                    
                    df.to_excel(excel_path, index=False)
                    self.console_log(f"✅ Saved GA summary to {excel_filename}")

    
                self.console_log(f"===== End of Gen {gen} - Ind {ind} =====\n")
                 
                
                input("Press Enter to continue for next individual...")
    
            self.console_log("GA optimization complete.")
    
        threading.Thread(target=ga_loop, daemon=True).start()
        self.start_ga_btn.config(state=tk.DISABLED)
    
    def apply_arti_amp(self):
        """Apply the user-defined threshold to be used in ERNA logic"""
        try:
            new_value = int(self.arti_amp_var.get())
            Config.arti_amp = new_value
            self.console_log(f"[Threshold] arti_amp applied: {new_value}")
        except ValueError:
            self.console_log("[ERROR] Invalid arti_amp value")
            
    def update_threshold_line(self):
        """Update threshold line visually on plot (real-time) without changing arti_amp"""
        try:
            val = int(self.arti_amp_var.get())
            if hasattr(self, "threshold_line"):
                self.threshold_line.set_ydata([val] * len(self.plot_data))
                self.canvas.draw_idle()
        except ValueError:
            pass  # Ignore invalid inputs (e.g., empty or non-integer)
    
    def on_close(self):
        self.runstim = False
        self.runplot = False
        self.receiving = False

        if hasattr(self, 'inlet'):
            self.inlet.close_stream()
        #if self.port.is_open:
            #self.port.close()
        self.root.destroy()
        print("[CLOSED] Manual stop and window closed.")    
        
    
    def detect_streams(self):
        def apply_detection_results(streams):
            self.streams = streams
            self.detected_streams = [s.name for s in streams]
            if not self.detected_streams:
                self.console_log("⚠️ No streams found.")
                return

            self.selected_stream_name.set(self.detected_streams[0])
            self._populate_option_menu(self.stream_menu, self.selected_stream_name, self.detected_streams, self.on_stream_selected)

            self.console_log(f"✅ Found {len(self.detected_streams)} streams.")
            self.on_stream_selected()

        def do_detection():
            try:
                self.console_log("🔍 Detecting LSL streams...")
                print('*******************************')
                
                streams = resolve_streams()
                print(streams)
                self.root.after(0, lambda s=streams: apply_detection_results(s))

            except Exception as e:
                self.console_log(f"[ERROR] Stream detection failed: {e}")
    
        threading.Thread(target=do_detection, daemon=True).start()
    
    
    def on_stream_selected(self, *_):
        stream_name = self.selected_stream_name.get()
        if not stream_name:
            return

        inlet = None
        try:
            streams = getattr(self, "streams", [])
            selected_stream = next((s for s in streams if s.name == stream_name), None)

            if selected_stream is None:
                streams = resolve_streams(timeout=2.0, name=stream_name)
                selected_stream = next((s for s in streams if s.name == stream_name), streams[0] if streams else None)

            if selected_stream is None:
                self.console_log(f"⚠️ Stream '{stream_name}' not found.")
                return

            inlet = StreamInlet(selected_stream)
            inlet.open_stream()
            info = inlet.get_sinfo()
            ch_info = info.desc.child("channels").child("channel")
    
            self.detected_channels = []
            for _ in range(info.n_channels):
                self.detected_channels.append(ch_info.child_value("label"))
                ch_info = ch_info.next_sibling()
    
            if not self.detected_channels:
                self.detected_channels = [f"Ch{i+1}" for i in range(info.n_channels)]
    
            self.selected_detected_channel.set(self.detected_channels[0])
            self._populate_option_menu(self.channel_detect_menu, self.selected_detected_channel, self.detected_channels)
    
            self.console_log(f"✅ Channels from '{stream_name}' loaded.")
    
        except Exception as e:
            self.console_log(f"[ERROR] Failed to read channels: {e}")

        finally:
            if inlet is not None:
                try:
                    inlet.close_stream()
                except Exception:
                    pass

    def reset_all_plots(self):
        # Stop any ongoing plotting
        self.stop_receiving_chunks()
        #self.runplot = False
        #self.receiving = False
        
        self.log_history=[]
    
        # Clear raw plot data
        if hasattr(self, "plot_data"):
            self.plot_data[:] = 0
            if hasattr(self, "plot_line") and hasattr(self, "threshold_line"):
                self.plot_line.set_ydata(self.plot_data)
                self.threshold_line.set_ydata([Config.arti_amp] * len(self.plot_data))
                self.canvas.draw()
    
        # Clear event buffer
        if hasattr(self, "event_buffer"):
            self.event_buffer.clear()
        if hasattr(self, "signal_buffer"):
            self.signal_buffer = np.array([])
    
        # Clear amp buffer
        if hasattr(self, "amp_erna_list"):
            self.amp_erna_list.clear()
        if hasattr(self, "amp_erna_list_total"):
            self.amp_erna_list_total.clear()
    
 
        if hasattr(self, "plot_event"):
            for widget in self.plot_event.winfo_children():
                widget.destroy()
        if hasattr(self, "fs"):
            self.create_event_plot_canvas(self.fs)
 
        if hasattr(self, "plot_amp"):
            for widget in self.plot_amp.winfo_children():
                widget.destroy()
        if hasattr(self, "fs"):
            self.create_amp_plot_canvas(self.fs)
    
        # Reset status
        self.status_var2.set(" ERNA Monitor:\n • Mean amp: XX.X µA \n • Freq: XXX Hz \n • Event: X")
        self.status_receive_var.set(" Received Samples:\n • New chunk: XX \n • Total: XX \n • Duration: XX")
    
        self.console_log("✅ Reset all plots and buffers.")  
        
    def open_lsl_config_window(self):
        # Disable button to prevent multiple windows
        self.config_lsl_button.config(state=tk.DISABLED)
    
        window = tk.Toplevel(self.root)
        window.title("Select Channels")
        window.geometry("280x420")
        window.protocol("WM_DELETE_WINDOW", lambda: (window.destroy(), self.config_lsl_button.config(state=tk.NORMAL)))
    
        # All possible channels
        all_channels_a = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']
        
        all_channels_b = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8']
        
        all_channels_c = ['Lfp','Ac2X','Ac2Y','Ac2Z']
    
        # Keep track of checkboxes
        self.channel_vars = {}
    
        # Frame for checkboxes
        checkbox_frame = tk.Frame(window)
        checkbox_frame.pack(pady=10)

        # Add Detect Button
        self.detect_button = ttk.Button(checkbox_frame, text="Detect LSL", command=self.detect_streams,width=12)
        self.detect_button.grid(row=0, column=0, columnspan=4, pady=4)
        
        # Add Stream Menu
        self.stream_menu = ttk.OptionMenu(checkbox_frame, self.selected_stream_name, self.selected_stream_name.get(), *self.detected_streams)
        self.stream_menu.config(width=30)
        self.stream_menu.grid(row=1, column=0, columnspan=4, pady=4)
        
        # Add Channel Menu
        #self.channel_detect_menu = ttk.OptionMenu(checkbox_frame, self.selected_detected_channel, self.selected_detected_channel.get(), *self.detected_channels)
        self.channel_detect_menu = ttk.OptionMenu(checkbox_frame, self.selected_detected_channel, self.selected_detected_channel.get(), *self.detected_channels, command=lambda val: self.selected_channel_name.set(val))
        self.channel_detect_menu.config(width=20)
        self.channel_detect_menu.grid(row=2, column=0, columnspan=4, pady=4)
        
        # Separator
        separator = tk.Label(checkbox_frame, text="-------- Select detected channels ----------")
        separator.grid(row=3, column=0, columnspan=4, pady=(5, 5))
        
        val_y=0.1
        
        self.all_l_var = tk.BooleanVar(value=True)
        all_l_checkbox = tk.Checkbutton(checkbox_frame,text="All 'L'",variable=self.all_l_var,
            command=lambda: [self.channel_vars[ch].set(self.all_l_var.get()) for ch in all_channels_a])
        all_l_checkbox.grid(row=4, column=0, sticky="w", padx=10, pady=val_y)
        
        self.all_r_var = tk.BooleanVar(value=False)
        all_r_checkbox = tk.Checkbutton(checkbox_frame,text="All 'R'",variable=self.all_r_var,
            command=lambda: [self.channel_vars[ch].set(self.all_r_var.get()) for ch in all_channels_b])
        all_r_checkbox.grid(row=4, column=1, sticky="w", padx=10, pady=val_y)
        
        self.all_c_var = tk.BooleanVar(value=False)
        all_c_checkbox = tk.Checkbutton(checkbox_frame,text="All below",variable=self.all_c_var,
            command=lambda: [self.channel_vars[ch].set(self.all_c_var.get()) for ch in all_channels_c])
        all_c_checkbox.grid(row=4, column=2, sticky="w", padx=10, pady=val_y)

        for i, ch in enumerate(all_channels_a):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(checkbox_frame, text=ch, variable=var)
            cb.grid(row=i+5, column=0, sticky="w", padx=10, pady=val_y)
            self.channel_vars[ch] = var
            
        for i, ch in enumerate(all_channels_b):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(checkbox_frame, text=ch, variable=var)
            cb.grid(row=i+5, column=1, sticky="w", padx=10, pady=val_y)
            self.channel_vars[ch] = var
            
        for i, ch in enumerate(all_channels_c):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(checkbox_frame, text=ch, variable=var)
            cb.grid(row=i+5, column=2, sticky="w", padx=10, pady=val_y)
            self.channel_vars[ch] = var

        

        # --- Save Button ---
        def apply_channels():
            
            #Config.ch_name=self.selected_detected_channel
            
            selected = [ch for ch, var in self.channel_vars.items() if var.get()]
            if not selected:
                tk.messagebox.showwarning("No Channel Selected", "Please select at least one channel.")
                return
    
            # Update Config
            Config.selected_channels = selected
    
            # Update channel selection menu
            #if not self.selected_channel_name.get():
                #self.selected_channel_name.set(selected[0])
                #self.selected_channel_name.set(self.selected_detected_channel.get() )
            
            self.selected_channel_name.set(self.selected_detected_channel.get() )
            
            self._populate_option_menu(self.channel_menu, self.selected_channel_name, selected)
    
            self.console_log(f"✅ Updated selected channels: {selected}")
            window.destroy()
            self.config_lsl_button.config(state=tk.NORMAL)
    
        apply_btn = tk.Button(window, text="Apply and Close", command=apply_channels)
        apply_btn.pack(pady=5)        
 
 
if __name__ == "__main__":

    root = tk.Tk()
    app = StimulatorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
