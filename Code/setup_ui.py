import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import Config

def setup_ui(self):
    self.font_seg='Segoe UI'
    self.font_s=9
    self.log_history=[]
    ta_erna_ini=0.003
    tb_erna_ini=0.02
    
    bg_width, bg_height = Config.bg_size_x, Config.bg_size_y_ga
    entry_width = Config.ui_width
    entry_padx = Config.ui_pad_x
    entry_pady = Config.ui_pad_y
    entry_width2=int(entry_width/1.5)
    entry_padx2=5
    
    self.pair_interval = tk.DoubleVar(value=0.0070)

    self.ta_erna = tk.DoubleVar(value=ta_erna_ini)
    self.tb_erna = tk.DoubleVar(value=tb_erna_ini)
    
    self.ta_erna.trace_add("write", lambda *_: (self.update_event_plot(),self.tb_erna_box.config(from_=min(float(self.ta_erna.get())+0.012,float(self.tb_erna.get()) - 0.012)  ) if hasattr(self, 'tb_erna_box') else None))
    self.tb_erna.trace_add("write", lambda *_: (self.update_event_plot(),self.ta_erna_box.config(to= max(float(self.tb_erna.get()) - 0.012,float(self.ta_erna.get())+0.012)) if hasattr(self, 'ta_erna_box') else None))
    
    
    #frame 1: stream detection frame
    self.stream_detect_frame = tk.Frame(self.root)
    self.stream_detect_frame.grid(row=0, column=0, columnspan=6, pady=Config.ui_pad_y) 
    self.detected_streams = []
    self.detected_channels = []
    self.selected_stream_name = tk.StringVar()
    self.selected_detected_channel = tk.StringVar()
    
    
    self.config_lsl_button = ttk.Button(self.stream_detect_frame, text="Config LSL", command=self.open_lsl_config_window)
    self.config_lsl_button.grid(row=0, column=0, padx=(8,2), pady=Config.ui_pad_y)




    # Only display the selected stream (label), no dropdown here
    ttk.Label(self.stream_detect_frame, text="Stream Name: ").grid(row=0, column=1, padx=(8, 2), pady=Config.ui_pad_y)
    self.stream_display_label = ttk.Label(self.stream_detect_frame, textvariable=self.selected_stream_name, width=20)
    self.stream_display_label.grid(row=0, column=2, pady=Config.ui_pad_y)
    

    
    ttk.Label(self.stream_detect_frame, text="File Name").grid(row=0, column=4, padx=(12,0), pady=entry_pady)
    self.file_name_var = tk.StringVar(value='test')
    self.file_name_entry = ttk.Entry(self.stream_detect_frame, textvariable=self.file_name_var, width=20)
    self.file_name_entry.grid(row=0, column=5, padx=8, pady=Config.ui_pad_y)
    
    #frame 0: root frame - mode selection
    ttk.Label(self.root, text="Select Mode").grid(row=1, column=0, padx=entry_padx, pady=entry_pady)
    #modes = ["Single", "Continuous", "Burst", "GA"]
    modes = ["Continuous", "Burst", "GA"]
    self.mode_var = tk.StringVar(value="Burst")
    
    
    #self.mode_var.trace_add("write", lambda *args: self.StiNum_var_entry.config(state='normal' if self.mode_var.get() in ('Single', 'Burst') else 'readonly'))
    mode_menu = ttk.OptionMenu(self.root, self.mode_var, self.mode_var.get(), *modes, command=lambda _: self.update_ui_fields())
    mode_menu.grid(row=1, column=1, padx=entry_padx, pady=entry_pady)
    
    self.cBst_var = tk.BooleanVar(value=False)
    self.cBst_checkbox = ttk.Checkbutton(self.root,text="cBurst",variable=self.cBst_var, command=lambda: 
        [self.StiNum_var_entry.config(state='normal' if not self.cBst_var.get() else 'disabled'),
         self.Rand_var_entry.config(state='normal' if not self.cBst_var.get() else 'disabled'),
         self.fields['ramp_onoff'][1].config(state='disabled' if not self.cBst_var.get() else 'normal'),
         self.fields['ramp_time'][1].config(state='disabled' if not self.cBst_var.get() else 'normal'),
         self.update_ui_fields()  ])
     
    
    self.freq_var = tk.IntVar(value=Config.ini_freq)
    self.freq_var.trace_add("write", lambda *_: self.pair_interval.set(round(1.0 / self.freq_var.get(), 4) if self.freq_var.get() > 0 else 0))
    
    self.pw_var = tk.IntVar(value=Config.ini_pw)
    
    #below should set the current value as diff between current pw and previous pw
    self.pw_var.trace_add("write", lambda *_: (
    self.ta_erna.set(round(ta_erna_ini + (self.num_pulses_var.get() - 1) * self.pair_interval.get(), 4)),
    self.tb_erna.set(round(tb_erna_ini + (self.num_pulses_var.get() - 1) * self.pair_interval.get(), 4)) ))
    
    
    
    self.gap_var = tk.IntVar(value=Config.ini_gap)
    self.amp_var = tk.IntVar(value=Config.up_amp)   
    self.ramp_OnOff = tk.IntVar(value=Config.ini_RampEnable)
    self.ramp_var = tk.IntVar(value=Config.ini_ramp)
    self.burst_interval_var = tk.IntVar(value=Config.up_burst_interval)
    
    # original test result: 0.00006 * self.pw_var.get() -0.00075
    self.num_pulses_var = tk.IntVar(value=Config.up_num_pulses)
    self.num_pulses_var.trace_add("write", lambda *_: (
    Config.__setattr__('ini_StimOutput', 2 if self.num_pulses_var.get() == 1 else 4),
    self.ta_erna.set(round(ta_erna_ini + (self.num_pulses_var.get() - 1) * self.pair_interval.get(), 4)),
    self.tb_erna.set(round(tb_erna_ini + (self.num_pulses_var.get() - 1) * self.pair_interval.get(), 4)) ))
    #self.ta_erna.set(round(ta_erna_ini + (self.num_pulses_var.get() - 1) * self.pair_interval.get()+ 0.00005 * self.pw_var.get() -0.00055, 4)),
    
    
    #frame 0: root frame - stimulation parameters
    self.field_vars = {
        'freq': self.freq_var,
        'pw': self.pw_var,
        'gap': self.gap_var,
        'amp': self.amp_var,
        'ramp_onoff': self.ramp_OnOff,
        'ramp_time': self.ramp_var,
        'burst_interval': self.burst_interval_var,
        'num_pulses': self.num_pulses_var}

    default_labels = {
        'freq': "Frequency (90:5:500 Hz)",
        'pw': "Pulse Width (20:5:300 µs)",
        'gap': "Gap Width (20:5:300 µs)",
        'amp': "Amplitude (100:100:4500 µA)",
        'ramp_onoff': "Ramp Enable (1-disable; 2-enable)",
        'ramp_time': "Ramp Time (10:10:5000 ms)",
        'burst_interval': "Burst Interval (100:5:500 ms)",
        'num_pulses': "Num of Pulses (1:1:100)"}

    ga_labels = {
        'freq': "Frequency (90:5:145 Hz) -- via GA",
        'pw': "Pulse Width (20:5:100 µs) -- via GA" }

    self.fields = {}
    
    def on_var_change(var_name, tk_var):
        def callback(*_):
            try:
                val = tk_var.get()
                #print(f"✅ [UI] '{var_name}' changed to {val}")
                if hasattr(self, 'update_stimulation_from_ui'):
                    self.update_stimulation_from_ui()
            except Exception as e:
                print(f"[UI Error] Failed to read '{var_name}': {e}")
        return callback

    for key, var in self.field_vars.items():
        label = ttk.Label(self.root, text=default_labels[key])
    
        if key == 'freq':
            spin = tk.Spinbox(self.root, from_=50, to=Config.limit_frequency, increment=5, textvariable=var, width=entry_width)
        elif key == 'pw':
            spin = tk.Spinbox(self.root, from_=20, to=Config.limit_pulsewidth, increment=5, textvariable=var, width=entry_width)
        elif key == 'gap':
            spin = tk.Spinbox(self.root, from_=20, to=Config.limit_gapwidth, increment=5, textvariable=var, width=entry_width)
        elif key == 'amp':
            spin = tk.Spinbox(self.root, from_=100, to=Config.limit_amplitude, increment=100, textvariable=var, width=entry_width)
        elif key == 'ramp_onoff':
            spin = tk.Spinbox(self.root, from_=1, to=2, increment=1, textvariable=var, width=entry_width)
        elif key == 'ramp_time':
            spin = tk.Spinbox(self.root, from_=10, to=5000, increment=10, textvariable=var, width=entry_width)
        elif key == 'burst_interval':
            spin = tk.Spinbox(self.root, from_=100, to=500, increment=5, textvariable=var, width=entry_width)
        elif key == 'num_pulses':
            spin = tk.Spinbox(self.root, from_=1, to=100, increment=1, textvariable=var, width=entry_width)
        else:
            spin = ttk.Entry(self.root, textvariable=var, width=entry_width)  # fallback
    
        var.trace_add("write", on_var_change(key, var))
        self.fields[key] = (label, spin)
    
    # === Field Visibility Config ===
    self.mode_fields = {
        "Single": ['pw', 'gap', 'amp', 'ramp_onoff', 'ramp_time'],
        "Continuous": ['freq', 'pw', 'gap', 'amp', 'ramp_onoff', 'ramp_time'],
        "Burst": ['freq', 'pw', 'gap', 'amp', 'ramp_onoff', 'ramp_time', 'num_pulses'],
        "GA": ['freq', 'pw', 'amp', 'gap', 'num_pulses']}
    
    # === Start-Stim/Stop-Stim & Console ===
    row_n=10
    self.stimu_frame = tk.Frame(self.root)
    self.StiNum_var = tk.IntVar(value=20)
    self.StiNum_var_entry = tk.Spinbox(self.stimu_frame, from_=1, to=10000, increment=1, textvariable=self.StiNum_var, width=entry_width2)  
    self.stimu_frame.grid(row=row_n, column=0, columnspan=9, pady=Config.ui_pad_y) 
    
    
    
    #self.ini_btn = ttk.Button(self.stimu_frame, text="Ini", command=self.setup_stimulator)
    self.start_btn = ttk.Button(self.stimu_frame, text="Start-Stim", command=self.start_stimulation)
    self.stop_btn = ttk.Button(self.stimu_frame, text="Stop-Stim", command=self.stop_stimulation)
    #self.ini_btn.grid(row=0, column=0, pady=entry_pady)
    self.start_btn.grid(row=0, column=1, pady=entry_pady)
    self.stop_btn.grid(row=0, column=2, pady=entry_pady)
    
    
    self.StiNum_var_label = ttk.Label(self.stimu_frame, text="Num")
    self.StiNum_var_label.grid(row=0, column=3, padx=(8,2), pady=entry_pady)
    self.StiNum_var_entry.grid(row=0, column=4, pady=entry_pady)
    
    self.pass_var = tk.StringVar(value="XXX")
    self.pass_label = ttk.Label(self.stimu_frame, textvariable=self.pass_var, font=(self.font_seg, self.font_s, 'bold'), foreground="#051ab3")
    self.pass_label.grid(row=0, column=5, padx=(2,8),pady=entry_pady) 
    
 
    self.BstInter_var = tk.IntVar(value=500)
    
    #self.burst_interval_var
    
    self.BstInter_var_label = ttk.Label(self.stimu_frame, text="Bst Interval (ms)")
    self.BstInter_var_label.grid(row=0, column=6, pady=entry_pady)
    self.BstInter_var_entry = tk.Spinbox(self.stimu_frame, from_=1, to=10000, increment=1, textvariable=self.burst_interval_var if self.cBst_var.get() else self.BstInter_var, width=entry_width2)
    self.BstInter_var_entry.grid(row=0, column=7, pady=entry_pady)
    
    self.Rand_var = tk.IntVar(value=10)
    self.Rand_var_label = ttk.Label(self.stimu_frame, text="Rand (%)")
    self.Rand_var_label.grid(row=0, column=8, pady=entry_pady)
    self.Rand_var_entry = tk.Spinbox(self.stimu_frame, from_=0, to=100, increment=1, textvariable=self.Rand_var, width=int(entry_width2/2))
    self.Rand_var_entry.grid(row=0, column=9, pady=entry_pady)
    

    #frame 2: button frame: select channel, receive LSL, stop receiving, start GA
    self.button_frame = tk.Frame(self.root)
    self.button_frame.grid(row=row_n+1, column=0, columnspan=7, pady=Config.ui_pad_y) 
    self.channel_label = ttk.Label(self.button_frame, text="CH")
    channels = Config.selected_channels
    self.channel_menu = ttk.OptionMenu(self.button_frame, self.selected_channel_name, self.selected_channel_name.get(), *channels)
    #self.channel_menu = ttk.OptionMenu(self.button_frame, self.selected_channel_name, "", *channels)
    self.receive_btn = ttk.Button(self.button_frame, text="Receive LSL", command=self.start_receiving_chunks)
    self.stop_receive_btn = ttk.Button(self.button_frame, text="Stop Receiving", command=self.stop_receiving_chunks, state=tk.DISABLED) 
    self.start_ga_btn = ttk.Button(self.root, text="Start GA", command=self.start_ga_process,width=9)  
    
    self.channel_label.grid(row=0, column=0, padx=(10,2), pady=entry_pady)
    self.channel_menu.grid(row=0, column=1, padx=(2,5), pady=entry_pady)
    
    self.arti_amp_var = tk.IntVar(value=Config.arti_amp)
    self.arti_amp_var.trace_add("write", lambda *_: [self.update_threshold_line(),self.update_event_plot()])
    #self.arti_amp_frame = tk.Frame(self.root)
    #self.arti_amp_frame.grid(row=row_n+2, column=0, columnspan=5, pady=entry_pady)
    self.arti_amp_label = ttk.Label(self.button_frame, text="Arti-Threshold")
    self.arti_amp_entry = tk.Spinbox(self.button_frame, from_=10, to=10000, increment=10, textvariable=self.arti_amp_var, width=entry_width2)
    self.arti_amp_apply_btn = ttk.Button(self.button_frame, text="Apply Threshold", command=self.apply_arti_amp)
    self.arti_amp_label.grid(row=0, column=2, padx=(10,2), pady=entry_pady)
    self.arti_amp_entry.grid(row=0, column=3, padx=(2,2), pady=entry_pady)
    self.arti_amp_apply_btn.grid(row=0, column=4, padx=(2,10), pady=entry_pady)
    self.receive_btn.grid(row=0, column=5, padx=(10,5),pady=entry_pady)
    self.stop_receive_btn.grid(row=0, column=6, padx=(5,10),pady=entry_pady)  

    self.pair_interval.set(round(1.0 / self.freq_var.get(), 4))

    
    # frame 4: event_config_frame
    self.event_config_frame = tk.Frame(self.root)
    self.event_config_frame.grid(row=row_n+3, column=0, columnspan=6, pady=entry_pady)
    ttk.Label(self.event_config_frame, text="t (s) ← Trig").grid(row=0, column=0, padx=entry_padx2, pady=entry_pady/2)
    ttk.Label(self.event_config_frame, text="Trig → t (s)").grid(row=0, column=1, padx=entry_padx2, pady=entry_pady/2)
    ttk.Label(self.event_config_frame, text="↓ y min (µA)").grid(row=0, column=2, padx=entry_padx2, pady=entry_pady/2)
    ttk.Label(self.event_config_frame, text="↑ y max (µA)").grid(row=0, column=3, padx=entry_padx2, pady=entry_pady/2)
    ttk.Label(self.event_config_frame, text="ERNA start (s)").grid(row=0, column=4, padx=entry_padx2, pady=entry_pady/2)
    ttk.Label(self.event_config_frame, text="ERNA end (s)").grid(row=0, column=5, padx=entry_padx2, pady=entry_pady/2)
    
    self.ta_var = tk.DoubleVar(value=0.01)
    self.tb_var = tk.DoubleVar(value=0.045)
    self.ya_var = tk.DoubleVar(value=Config.ya_show)
    self.yb_var = tk.DoubleVar(value=Config.yb_show)
    self.ta_var.trace_add("write", lambda *_: self.update_event_plot())
    self.tb_var.trace_add("write", lambda *_: self.update_event_plot())
    self.ya_var.trace_add("write", lambda *_: self.update_event_plot())
    self.yb_var.trace_add("write", lambda *_: self.update_event_plot())
    
    
    ta_box=tk.Spinbox(self.event_config_frame, from_=0.001, to=Config.ta_plot, increment=0.001, textvariable=self.ta_var, width=entry_width2)
    ta_box.grid(row=1, column=0, padx=entry_padx2, pady=entry_pady/2)
    #ta_box.bind("<Key>", lambda e: "break")
    tb_box=tk.Spinbox(self.event_config_frame, from_=0.003, to=Config.tb_plot, increment=0.001, textvariable=self.tb_var, width=entry_width2)
    tb_box.grid(row=1, column=1, padx=entry_padx2, pady=entry_pady/2)
    #tb_box.bind("<Key>", lambda e: "break")
    ya_box=tk.Spinbox(self.event_config_frame, from_=10, to=10000, increment=10, textvariable=self.ya_var, width=entry_width2)
    ya_box.grid(row=1, column=2, padx=entry_padx2, pady=entry_pady/2)
    #ya_box.bind("<Key>", lambda e: "break")
    yb_box=tk.Spinbox(self.event_config_frame, from_=10, to=10000, increment=10, textvariable=self.yb_var, width=entry_width2)
    yb_box.grid(row=1, column=3, padx=entry_padx2, pady=entry_pady/2)
    #yb_box.bind("<Key>", lambda e: "break")
    
    self.ta_erna_box=tk.Spinbox(self.event_config_frame, from_=0.001, to=float(self.tb_erna.get()), increment=0.0005, textvariable=self.ta_erna, width=entry_width2)
    self.ta_erna_box.grid(row=1, column=4, padx=entry_padx2, pady=entry_pady/2)
    self.ta_erna_box.bind("<Key>", lambda e: "break")
    
    self.tb_erna_box=tk.Spinbox(self.event_config_frame, from_=float(self.ta_erna.get()), to=Config.tb_plot, increment=0.0005, textvariable=self.tb_erna, width=entry_width2)
    self.tb_erna_box.grid(row=1, column=5, padx=entry_padx2, pady=entry_pady/2)
    self.tb_erna_box.bind("<Key>", lambda e: "break")
    
    #plot region
    self.plot_raw = tk.LabelFrame(self.root, text="Raw Data [x-axis: t (s)]", width=560, height=120, bd=1.2, relief="solid", font=(self.font_seg,self.font_s))
    self.plot_event = tk.LabelFrame(self.root, text="Detected ERNA events  [x-axis: t (s)]", width=560, height=180, bd=1.2, relief="solid", font=(self.font_seg,self.font_s))
 
    self.plot_raw.grid(row=row_n+4, column=0, columnspan=2, padx=10, pady=entry_pady, sticky="nsew")
    self.plot_raw.grid_propagate(False)
    self.plot_event.grid(row=row_n+5, column=0, columnspan=2, padx=10, pady=entry_pady, sticky="nsew")
    self.plot_event.grid_propagate(False)
            
    #frame 5: filter frame
    entry_width3=6
    self.filter_frame = tk.Frame(self.root)
    self.filter_frame.grid(row=row_n+6, column=0, columnspan=2, pady=Config.ui_pad_y) 
    
    
    
    self.bp_filter_var = tk.BooleanVar(value=False)
    self.bp_filter_checkbox = ttk.Checkbutton(self.filter_frame, text="BP Filter", variable=self.bp_filter_var, command=lambda: [
        self.update_event_plot(),
        self.bp_f1_box.config(state='normal' if self.bp_filter_var.get() else 'disabled'),
        self.bp_f2_box.config(state='normal' if self.bp_filter_var.get() else 'disabled'),
        self.bp_n_box.config(state='normal' if self.bp_filter_var.get() else 'disabled')])
    self.bp_filter_checkbox.grid(row=0, column=0, padx=5, pady=entry_pady, sticky='w') 
    self.bp_f1_label=ttk.Label(self.filter_frame, text="f1 (Hz)").grid(row=0, column=1, padx=entry_padx2, pady=entry_pady/2)
    self.bp_f1 = tk.DoubleVar(value=50)
    self.bp_f1.trace_add("write", lambda *_: self.update_event_plot())
    self.bp_f1_box=tk.Spinbox(self.filter_frame, from_=40, to=60, increment=1, textvariable=self.bp_f1, width=entry_width3)
    self.bp_f1_box.grid(row=0, column=2, padx=entry_padx2, pady=entry_pady/2) 
    self.bp_f1_box.config(state='disabled')
    self.bp_f2_label=ttk.Label(self.filter_frame, text="f2 (Hz)").grid(row=0, column=3, padx=entry_padx2, pady=entry_pady/2)
    self.bp_f2 = tk.DoubleVar(value=600)
    self.bp_f2.trace_add("write", lambda *_: self.update_event_plot())
    self.bp_f2_box=tk.Spinbox(self.filter_frame, from_=550, to=700, increment=10, textvariable=self.bp_f2, width=entry_width3)
    self.bp_f2_box.grid(row=0, column=4, padx=entry_padx2, pady=entry_pady/2)
    self.bp_f2_box.config(state='disabled')
    self.bp_n_label=ttk.Label(self.filter_frame, text="Order").grid(row=0, column=5, padx=entry_padx2, pady=entry_pady/2)
    self.bp_n = tk.DoubleVar(value=3)
    self.bp_n.trace_add("write", lambda *_: self.update_event_plot())
    self.bp_n_box=tk.Spinbox(self.filter_frame, from_=2, to=5, increment=1, textvariable=self.bp_n, width=entry_width3)
    self.bp_n_box.grid(row=0, column=6, padx=entry_padx2, pady=entry_pady/2) 
    self.bp_n_box.config(state='disabled')  
    
    self.DC_remov_var = tk.BooleanVar(value=True)
    self.DC_remov_checkbox = ttk.Checkbutton(self.filter_frame, text="DC Rem", variable=self.DC_remov_var, command=lambda: [
        self.update_event_plot()])
    self.DC_remov_checkbox.grid(row=0, column=7, padx=5, pady=entry_pady, sticky='w') 
    
    self.Rectify_var = tk.BooleanVar(value=True)
    self.Rectify_checkbox = ttk.Checkbutton(self.filter_frame, text="Rectify", variable=self.Rectify_var, command=lambda: [
        self.update_event_plot()])
    self.Rectify_checkbox.grid(row=0, column=8, padx=5, pady=entry_pady, sticky='w') 
    

    #frame 6: status frame
    self.status_frame = tk.Frame(self.root) #,bd=0.5, relief="solid"
    self.status_frame.grid(row=row_n+7, rowspan=20, column=0, columnspan=1, padx=10, pady=Config.ui_pad_y,sticky="w") 
    self.status_var = tk.StringVar(value=" Evolution Progress:\n • Gen: -, Ind: -")
    self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, font=(self.font_seg, self.font_s, 'bold'), foreground="#051ab3")
    self.status_var2 = tk.StringVar(value=" ERNA Monitor:\n • Mean amp: XX.X µA \n • Freq: XXX Hz \n • Event: X")
    self.status_label2 = ttk.Label(self.status_frame, textvariable=self.status_var2, font=(self.font_seg, self.font_s, 'bold'), foreground="#051ab3")
    self.status_label.grid(row=0, column=0, columnspan=1, sticky="w", padx=0, pady=1)
    self.status_label2.grid(row=1, column=0, columnspan=1, sticky="w", padx=0, pady=1)
    self.status_receive_var = tk.StringVar(value=" Received Samples:\n • New chunk: XX \n • Total: XX \n • Duration: XX")
    self.status_receive_label = ttk.Label(self.status_frame,textvariable=self.status_receive_var,font=(self.font_seg, self.font_s, 'bold'),foreground="#051ab3")
    #self.status_receive_label.grid(row=2, column=0, columnspan=1, sticky="w", padx=0, pady=1)
    self.reset_btn = ttk.Button(self.status_frame, text="Reset Plot",command=self.reset_all_plots)
    self.reset_btn.grid(row=2, column=0, pady=entry_pady)
    
    #plot amp region
    self.plot_amp = tk.LabelFrame(self.root, text="Detected ERNA Amplitudes [x-axis: No. of events]", width=415, height=140, bd=1.2, relief="solid", font=(self.font_seg,self.font_s))    
    self.plot_amp.grid(row=row_n+7, column=0, columnspan=2, sticky="se", padx=10, pady=(2,8))
    self.plot_amp.grid_propagate(False) 
    
    self.log_lines = []
    self.log_label = tk.Label(self.root, text="Log area", justify="left", anchor='w', font=(self.font_seg,self.font_s), bd=1, relief="solid", width=60, height=2, padx=10)
    #self.log_label.grid(row=31, column=0, columnspan=2, sticky="se", padx=10, pady=5)
    
    
    
    # === Update Fields Function ===
    def update_ui_fields():
        mode = self.mode_var.get()
        Config.ini_StimOutput = 4 if (mode == "GA" or (mode == "Burst" and self.num_pulses_var.get() != 1)) else 2

        for label, entry in self.fields.values():
            label.grid_remove()
            entry.grid_remove()
    
        # Show relevant fields
        row = 2
        for key in self.mode_fields.get(mode, []):
            label, entry = self.fields[key]
            if mode == "GA" and key in ga_labels:
                label.config(text=ga_labels[key],foreground="red")
            else:
                label.config(text=default_labels[key],foreground="black")
            label.grid(row=row, column=0, padx=entry_padx, pady=entry_pady)
            entry.grid(row=row, column=1, padx=entry_padx, pady=entry_pady)
            entry.config(state='disabled' if mode == "GA" else 'normal')
            entry.bind("<Key>", lambda e: "break")
            
            row += 1
        if mode in ['Single', 'GA'] or (mode in ['Burst'] and not self.cBst_var.get()):
        #if mode in ['Single', 'GA']:
            self.stop_btn.grid_remove()
        else:
            self.stop_btn.grid(row=0, column=2, pady=entry_pady)
        
        if mode in ['Burst']:
            self.cBst_checkbox.grid(row=1, column=1, padx=(0,15), pady=entry_pady, sticky='e')
        else:
            self.cBst_checkbox.grid_remove()
        if mode in ['GA']:
            self.start_ga_btn.grid(row=1, column=1, padx=(5,10),pady=entry_pady, sticky='e')
        else:
            self.start_ga_btn.grid_remove()   
            
        if  not self.cBst_var.get() and mode=='Burst':
            self.fields['ramp_onoff'][1].config(state='disabled')
            self.fields['ramp_time'][1].config(state='disabled')
        else:
            self.fields['ramp_onoff'][1].config(state='normal')
            self.fields['ramp_time'][1].config(state='normal')
            
    
            

            
        
    # Bind function and call once
    self.update_ui_fields = update_ui_fields
    self.update_ui_fields()