import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from scipy.signal import find_peaks
import Config
from scipy.io import savemat
import os
import datetime
import threading
#from scipy.interpolate import interp1d
from scipy.signal import butter, iirnotch, filtfilt

def rectify_sig(signal):
    signal2=np.abs(signal)
    return signal2

def DC_remove(signal):
    signal2=signal-np.mean(signal)
    return signal2
        
def event_detect_pair(self, signal, fs, min_interval_sec=None):
    if min_interval_sec is None:
        n_samples = int(self.ta_erna.get() * fs)  # default path for legacy callers
    else:
        n_samples = int(float(min_interval_sec) * fs)

    rising_edges = np.where((signal[1:] > Config.arti_amp) & (signal[:-1] <= Config.arti_amp))[0] + 1

    filtered_edges = []
    last_edge = -np.inf

    for edge in rising_edges:
        if edge - last_edge >= n_samples:
            filtered_edges.append(edge)
            last_edge = edge

    return np.array(filtered_edges)

def bp_filter(sig, SR, fa, fb, order_n):
    nyq = 0.5 * SR
    low = fa / nyq
    high = fb / nyq
    b, a = butter(order_n, [low, high], btype='band')
    sig_bp = filtfilt(b, a, sig)
    return sig_bp

def notch_filter(sig, SR, notch_freq, quality_factor):
    w0 = notch_freq / (SR / 2)  # normalized frequency
    b, a = iirnotch(w0, quality_factor)
    sig_notch = filtfilt(b, a, sig)
    return sig_notch


def erna_check(sig, fs, trig, lag_min, lag_max, time_axis):
    
    start = round((trig + lag_min) * fs)
    end = round((trig + lag_max) * fs)
    post_sig = sig[start:end]

    pos_peaks, _ = find_peaks(post_sig)
    neg_peaks, _ = find_peaks(-post_sig)

    if len(pos_peaks) < 1 or len(neg_peaks) < 1:
        #print("$$$ reason1")
        return None

    pos1_idx = pos_peaks[0]
    amp_pos1 = post_sig[pos1_idx]
    time_pos1 = time_axis[start + pos1_idx]

    neg_after_pos1 = neg_peaks[neg_peaks > pos1_idx]
    if len(neg_after_pos1) < 1:
        #print("$$$ reason2")
        return None
    neg1_idx = neg_after_pos1[0]
    amp_neg1 = post_sig[neg1_idx]
    time_neg1 = time_axis[start + neg1_idx]

    pos_after_neg1 = pos_peaks[pos_peaks > neg1_idx]
    if len(pos_after_neg1) < 1:
        #print("$$$ reason3")
        return None
    pos2_idx = pos_after_neg1[0]
    amp_pos2 = post_sig[pos2_idx]
    time_pos2 = time_axis[start + pos2_idx]

    lag = abs(time_pos2 - time_neg1)
    f_erna = 1 / lag
    erna_latency = time_pos1

    return amp_pos1, amp_neg1, amp_pos2, time_pos1, time_neg1, time_pos2, lag, f_erna, erna_latency

def erna_check2(sig, fs, trig, lag_min, lag_max, time_axis):
    # Update for ERNA detection method for first negative peak ERNA type
    
    start = round((trig + lag_min) * fs)
    end = round((trig + lag_max) * fs)
    post_sig = sig[start:end]

    pos_peaks, _ = find_peaks(post_sig)
    neg_peaks, _ = find_peaks(-post_sig)

    if len(pos_peaks) < 1 or len(neg_peaks) < 1:
        return None

    # Step 1: First positive peak
    pos1_idx = pos_peaks[0]
    amp_pos1 = post_sig[pos1_idx]
    time_pos1 = time_axis[start + pos1_idx]

    # Step 2: Find the first negative peak AFTER the first positive
    neg_after_pos1 = neg_peaks[neg_peaks > pos1_idx]
    if len(neg_after_pos1) < 1:
        return None
    neg1_idx = neg_after_pos1[0]
    amp_neg1 = post_sig[neg1_idx]
    time_neg1 = time_axis[start + neg1_idx]

    # Step 3: Find the first negative peak BEFORE the first positive
    neg_before_pos1 = neg_peaks[neg_peaks < pos1_idx]
 

    if len(neg_before_pos1) > 0:
        neg0_idx = neg_before_pos1[-1]  # Take the nearest one before pos1
        amp_neg0 = post_sig[neg0_idx]
        time_neg0 = time_axis[start + neg0_idx]

        amp_diff_before = abs(amp_pos1 - amp_neg0)
        amp_diff_after = abs(amp_pos1 - amp_neg1)

        # Use the negative-before if amplitude difference is larger
        if amp_diff_before > amp_diff_after:
            # Update to use neg0 and pos1 as the first peak pair
            neg1_idx = neg0_idx
            amp_neg1 = amp_neg0
            time_neg1 = time_neg0
             

     
    # Step 5: Compute ERNA features
    lag = abs(time_pos1 - time_neg1)
    f_erna = 1 / lag
    erna_latency = 1#useless
    amp_pos2=1#useless
    time_pos2=1#useless

    return amp_pos1, amp_neg1, amp_pos2, time_pos1, time_neg1, time_pos2, lag, f_erna, erna_latency

def _show_or_save_figure(fig, console_log, save_path=None, suffix="plot"):
    fig.tight_layout()

    if save_path is not None:
        plot_path = f"{save_path}{suffix}.png"
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        plot_path = os.path.join(os.getcwd(), f"{suffix}_{timestamp}.png")

    fig.savefig(plot_path, dpi=150)
    console_log(f"✅ Saved plot image: {plot_path}")

def _set_receive_status(self, message):
    """Update the receive status text in a thread-safe way."""
    if not hasattr(self, 'status_receive_var'):
        return

    if hasattr(self, "root") and threading.current_thread() is not threading.main_thread():
        self.root.after(0, lambda m=message: self.status_receive_var.set(m))
    else:
        self.status_receive_var.set(message)


def _collect_chunks(self, chunk_queue, fs, is_running):
    """Collect chunks until stop is requested, while updating receive status."""
    buffer = []

    while is_running():
        try:
            chunk_data = chunk_queue.get(timeout=1.0)
            buffer.append(chunk_data.T)  # store as (samples, channels)

            if not hasattr(self, '_total_samples'):
                self._total_samples = 0

            n_chunk_samples = chunk_data.shape[0]
            self._total_samples += n_chunk_samples
            total_duration = self._total_samples / fs

            msg = (
                f" Received Samples:\n • New chunk: {n_chunk_samples} \n"
                f" • Total: {self._total_samples} \n • Duration: {total_duration:.2f} s"
            )
            _set_receive_status(self, msg)

        except Exception:
            if not is_running():
                break

    return buffer


def _cfg_value(cfg, key, fallback_fn):
    if key in cfg:
        return cfg[key]
    return fallback_fn()


def _resolve_analysis_cfg(self, analysis_cfg):
    cfg = analysis_cfg or {}
    resolved = {
        "freq": _cfg_value(cfg, "freq", lambda: self.freq_var.get()),
        "pw": _cfg_value(cfg, "pw", lambda: self.pw_var.get()),
        "gap": _cfg_value(cfg, "gap", lambda: self.gap_var.get()),
        "amp": _cfg_value(cfg, "amp", lambda: self.amp_var.get()),
        "burst_interval_default": _cfg_value(cfg, "burst_interval_default", lambda: self.burst_interval_var.get()),
        "burst_interval_stim": _cfg_value(cfg, "burst_interval_stim", lambda: self.BstInter_var.get()),
        "num_pulses": _cfg_value(cfg, "num_pulses", lambda: self.num_pulses_var.get()),
        "mode": _cfg_value(cfg, "mode", lambda: self.mode_var.get()),
        "file_name": _cfg_value(cfg, "file_name", lambda: self.file_name_var.get()),
        "ta_erna": float(_cfg_value(cfg, "ta_erna", lambda: self.ta_erna.get())),
        "tb_erna": float(_cfg_value(cfg, "tb_erna", lambda: self.tb_erna.get())),
        "ta_plot": float(_cfg_value(cfg, "ta_plot", lambda: self.ta_var.get())),
        "tb_plot": float(_cfg_value(cfg, "tb_plot", lambda: self.tb_var.get())),
        "ya_plot": float(_cfg_value(cfg, "ya_plot", lambda: self.ya_var.get())),
        "yb_plot": float(_cfg_value(cfg, "yb_plot", lambda: self.yb_var.get())),
        "selected_channel": _cfg_value(
            cfg,
            "selected_channel",
            lambda: self.selected_channel_name.get() if hasattr(self, "selected_channel_name") else "unknown"
        ),
        "bp_filter_applied": bool(
            _cfg_value(
                cfg,
                "bp_filter_applied",
                lambda: self.bp_filter_var.get() if hasattr(self, "bp_filter_var") else False
            )
        ),
        "bp_low": float(_cfg_value(cfg, "bp_low", lambda: self.bp_f1.get() if hasattr(self, "bp_f1") else 0.0)),
        "bp_high": float(_cfg_value(cfg, "bp_high", lambda: self.bp_f2.get() if hasattr(self, "bp_f2") else 0.0)),
        "bp_order": int(_cfg_value(cfg, "bp_order", lambda: self.bp_n.get() if hasattr(self, "bp_n") else 2)),
        "arti_amp": int(
            _cfg_value(
                cfg,
                "arti_amp",
                lambda: self.arti_amp_var.get() if hasattr(self, "arti_amp_var") else Config.arti_amp
            )
        ),
        "rectify": bool(
            _cfg_value(
                cfg,
                "rectify",
                lambda: self.Rectify_var.get() if hasattr(self, "Rectify_var") else False
            )
        ),
    }
    return resolved


def _get_channel_names(info, n_channels):
    try:
        return info.get_channel_names()
    except Exception:
        return [f"undefined{i+1}" for i in range(n_channels)]


def _build_cell_array(raw_data, ch_names):
    n_channels = raw_data.shape[1]
    cell_array = np.empty((n_channels, 2), dtype=object)
    for i in range(n_channels):
        cell_array[i, 0] = ch_names[i]
        cell_array[i, 1] = raw_data[:, i]
    return cell_array


def _build_save_path_prefix(save_dir, file_name, mode, gen, ind):
    if mode == "GA":
        return os.path.join(save_dir, f"{file_name}_Gen{gen:02d}_Ind{ind:02d}_")
    return os.path.join(save_dir, f"{file_name}_")


def _save_raw_lsl_data(buffer, fs, save_dir, info, cfg, gen, ind, t_before, t_after, dc_rem_start, dc_rem_end, console_log):
    raw_data = np.concatenate(buffer, axis=0)  # (samples, channels)
    ch_names = _get_channel_names(info, raw_data.shape[1])
    save_path = None

    if save_dir is None:
        return raw_data, ch_names, save_path

    os.makedirs(save_dir, exist_ok=True)
    save_path = _build_save_path_prefix(save_dir, cfg["file_name"], cfg["mode"], gen, ind)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cell_array = _build_cell_array(raw_data, ch_names)

    save_dict = {
        "data": cell_array,
        "SR": fs,
        "threshold": cfg["arti_amp"],
        "timestamp": current_time,
        "freq": cfg["freq"],
        "pw": cfg["pw"],
        "gap": cfg["gap"],
        "amp": cfg["amp"],
        "burst_interval_default": cfg["burst_interval_default"],
        "burst_interval_stim": cfg["burst_interval_stim"],
        "num_pulses": cfg["num_pulses"],
        "ta_erna": cfg["ta_erna"],
        "tb_erna": cfg["tb_erna"],
        "ta_plot": cfg["ta_plot"],
        "tb_plot": cfg["tb_plot"],
        "ya_plot": cfg["ya_plot"],
        "yb_plot": cfg["yb_plot"],
        "t_before": float(t_before),
        "t_after": float(t_after),
        "dc_rem_start": float(dc_rem_start),
        "dc_rem_end": float(dc_rem_end),
        "selected_channel": cfg["selected_channel"],
        "bp_filter_applied": cfg["bp_filter_applied"],
    }

    if cfg["mode"] == "GA":
        save_dict["gen"] = gen
        save_dict["ind"] = ind

    if cfg["bp_filter_applied"]:
        save_dict["bp_low"] = cfg["bp_low"]
        save_dict["bp_high"] = cfg["bp_high"]
        save_dict["bp_order"] = cfg["bp_order"]

    savemat(save_path + "full.mat", save_dict)
    console_log("✅ Saved raw LSL data.")
    return raw_data, ch_names, save_path


def _apply_partial_bp(trace: np.ndarray, apply_bp: bool, idx1: int, idx2: int, fs: float, fa: float, fb: float, order: int) -> np.ndarray:
    trace_out = trace.copy()
    if apply_bp and 0 <= idx1 < idx2 <= len(trace_out):
        trace_out[idx1:idx2] = bp_filter(trace_out[idx1:idx2], fs, fa, fb, order)
    return trace_out


def receive_chunks(self, console_log, chunk_queue, fs, is_running, save_dir=None, gen=None, ind=None, info=None, analysis_cfg=None):
    console_log("✅ >>> Start to receive chunks ...")
    buffer = _collect_chunks(self, chunk_queue, fs, is_running)

    if not buffer:
        console_log("No chunks received.")
        return

    cfg = _resolve_analysis_cfg(self, analysis_cfg)
    t_before, t_after = Config.t_before, Config.t_after
    dc_rem_start, dc_rem_end = Config.dc_rem_start, Config.dc_rem_end

    raw_data, ch_names, save_path = _save_raw_lsl_data(
        buffer,
        fs,
        save_dir,
        info,
        cfg,
        gen,
        ind,
        t_before,
        t_after,
        dc_rem_start,
        dc_rem_end,
        console_log,
    )
    self.ch_names = ch_names

    received_data = raw_data.T  # shape: (channels, samples)
    ta_erna_val, tb_erna_val = cfg["ta_erna"], cfg["tb_erna"]
    ta_plot_val, tb_plot_val = cfg["ta_plot"], cfg["tb_plot"]
    bp_applied = cfg["bp_filter_applied"]
    bp_low_val, bp_high_val, bp_order_val = cfg["bp_low"], cfg["bp_high"], cfg["bp_order"]
    arti_amp_val = cfg["arti_amp"]
    rectify_enabled = cfg["rectify"]
    
    if received_data.size == 0:
        console_log("No data received.")
        return # the below will not be conducted

    _, n_samples = received_data.shape
    console_log(f"✅ Total samples: {n_samples} ({n_samples/fs:.2f} s)")
    console_log(f"✅ Summary of ERNA events ... ")

    # Channel & trigger settings
    channel_indices = [ch_names.index(ch) for ch in Config.selected_channels if ch in ch_names]

    #amp_array = [(max(received_data[i]) - min(received_data[i])) / 2 for i in channel_indices]
    #ch_num = np.argmax(amp_array)
 
    signal = DC_remove(received_data[self.selected_channel_index]) 
    if rectify_enabled:
        signal = rectify_sig(signal)

    rising_edges = event_detect_pair(self, signal, fs, min_interval_sec=ta_erna_val)
  
    trigger_times = rising_edges / fs
    n_events = len(trigger_times)
    console_log(f"✅ Detected {n_events} trigger events.")

    
    st_dc_rem = True
    lag_min, lag_max = ta_erna_val, tb_erna_val
    #tx_show1, tx_show2 = -0.01, 0.025
    n_samples_seg = int((t_before + t_after) * fs)
    time_axis = np.linspace(-t_before, t_after, n_samples_seg)
    segments = np.zeros((len(channel_indices), n_events, n_samples_seg))
    
    # === Setup for unified Y-axis across channels ===
    apply_bp = bp_applied
    fa, fb, order = bp_low_val, bp_high_val, bp_order_val
    idx1 = int((t_before + lag_min) * fs)
    idx2 = int((t_before + lag_max) * fs)
    
    if apply_bp:
        filtered_segments = np.zeros_like(segments)

    for i, ch_idx in enumerate(channel_indices):
        for j, t in enumerate(trigger_times):
            center = int(t * fs)
            start = center - int(t_before * fs)
            end = center + (n_samples_seg-int(t_before * fs))
            dc0 = center - int(dc_rem_start * fs)
            dc1 = center - int(dc_rem_end * fs)
            #if the segment length is insufficient, the segment is not extracted,
            #and left as zeros in the segments array since it was initialized with segments = np.zeros((len(channel_indices), n_events, n_samples_seg))
            if min(start, dc0) < 0 or max(end, dc1) >= received_data.shape[1]:
                continue
            seg = received_data[ch_idx, start:end].copy()
            if st_dc_rem and dc1 > dc0:
                seg -= np.mean(received_data[ch_idx, dc0:dc1])
                
            segments[i, j, :] = seg
            
            if apply_bp:
                filtered_segments[i, j, :] = _apply_partial_bp(seg, apply_bp, idx1, idx2, fs, fa, fb, order)

    
    
    if apply_bp and save_path is not None:
        #save_path_filtered = os.path.join(save_dir, Config.f_name + '_segments_filtered.mat')
        savemat(save_path+'segments_filtered.mat', {'seg': filtered_segments})#*******************************************************************
        console_log("✅ Saved filtered segments data.")

    global_min, global_max = None, None
    filtered_avg_traces = []
    
    # Precompute filtered average traces for all channels
    #check ymin, ymax
    for i in range(len(channel_indices)):
        filtered_channel_traces = []
        for ev in range(n_events):
            trace = _apply_partial_bp(segments[i, ev, :], apply_bp, idx1, idx2, fs, fa, fb, order)
            filtered_channel_traces.append(trace)
    
        avg_trace = np.mean(filtered_channel_traces, axis=0)
        filtered_avg_traces.append(avg_trace)
        
        erna_window = avg_trace[idx1:idx2]
        local_min = np.min(erna_window)
        local_max = np.max(erna_window)
    
        if global_min is None or local_min < global_min:
            global_min = local_min
        if global_max is None or local_max > global_max:
            global_max = local_max

    margin = 0.7 * (global_max - global_min) if global_max != global_min else 1
    ymin = global_min - margin
    ymax = global_max + margin

    #plot each channel
    fig = Figure(figsize=(7, 1.6 * len(channel_indices)))
    FigureCanvasAgg(fig)
    axs = fig.subplots(len(channel_indices), 1, sharex=True, sharey=True)
    if len(channel_indices) == 1:
        axs = [axs]
    erna_results = []
    for i, ax in enumerate(axs):
        ax.set_ylabel(ch_names[channel_indices[i]])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        avg_trace = filtered_avg_traces[i]
    
        for ev in range(n_events):
            trace = _apply_partial_bp(segments[i, ev, :], apply_bp, idx1, idx2, fs, fa, fb, order)
            ax.plot(time_axis, trace, 'gray', alpha=0.5)
    
        ax.plot(time_axis, avg_trace, 'r', lw=2)
    
        arti = arti_amp_val
        ax.plot([lag_min, lag_min], [-arti, arti], 'm--', linewidth=1)
        ax.plot([lag_max, lag_max], [-arti, arti], 'm--', linewidth=1)
    
        ax.set_xlim([-ta_plot_val/2, tb_plot_val/3])
        ax.set_ylim([ymin, ymax])
        ax.grid(True)
    
        trace_for_check = _apply_partial_bp(avg_trace, apply_bp, idx1, idx2, fs, fa, fb, order)
    
        result = erna_check2(trace_for_check, fs, t_before, lag_min, lag_max, time_axis)
        if result:
            amp_pos1, amp_neg1, amp_pos2, t1, t2, t3, lag, f_erna, latency = result
            ax.plot(t1, amp_pos1, 'ro')
            ax.plot(t2, amp_neg1, 'bo')
            ax.plot(t3, amp_pos2, 'go')
            ax.text(t1, (amp_pos1 - amp_neg1)*1.1, f"{amp_pos1 - amp_neg1:.1f}", fontsize=16, color='red')
            erna_results.append({
                "channel": ch_names[channel_indices[i]],
                "diff": amp_pos1 - amp_neg1,
                "f_erna": f_erna,
                "amp1": amp_pos1,
                "amp2": amp_neg1
            })

    _show_or_save_figure(
        fig,
        console_log,
        save_path,
        suffix="erna_summary"
    )

    if erna_results:
        sorted_results = sorted(erna_results, key=lambda x: x["diff"], reverse=True)

        best = sorted_results[0]
        console_log(f"✅ Best ERNA: {best['channel']} | Amp: {best['diff']:.1f} µA | Freq: {best['f_erna']:.1f} Hz")
        channel_order_str = " > ".join([f"{r['channel']} (amp: {r['diff']:.1f})" for r in sorted_results])
        console_log(f"✅ ERNA Channel Order: {channel_order_str}")
    else:
        console_log("No ERNA detected.")
    

    fig3 = Figure(figsize=(6, 1.2 * len(channel_indices)))
    FigureCanvasAgg(fig3)
    axs3 = fig3.subplots(len(channel_indices), 1, sharex=True)
    if len(channel_indices) == 1:
        axs3 = [axs3]

    #plot channel erna amplitudes
    all_diffs_per_channel = {}##############
    valid_trigger_times = []
    for i, ax in enumerate(axs3):
        
        ch_idx = channel_indices[i]
        ch_name = ch_names[ch_idx]##############
        diffs = []
        valid_trigger_times = []

        for j in range(n_events):
            trace = segments[i, j, :]

            trace_for_check = _apply_partial_bp(trace, apply_bp, idx1, idx2, fs, fa, fb, order)
            result = erna_check2(trace_for_check, fs, t_before, lag_min, lag_max, time_axis)
            if result:
                amp_pos1, amp_neg1, _, _, _, _, _, _, _ = result
                diffs.append(amp_pos1 - amp_neg1)
                valid_trigger_times.append(trigger_times[j])
                #print(f'$$$$$ {amp_pos1 - amp_neg1:.1f}')
            #else:
                #console_log(f"Channel {Config.selected_channels[channel_indices[i]]}: ⚠️ Skipped trigger {j} at {trigger_times[j]:.3f}s: ERNA not detected.")
        all_diffs_per_channel[ch_name] = np.array(diffs)##############
        if valid_trigger_times:
            ax.plot(valid_trigger_times, diffs, marker='o', linestyle='-', color='b', label='ERNA Diff')
            ax.set_title(f"ERNA Amp over Time - {ch_names[ch_idx]}")
            ax.set_ylabel("Amp (µA)")
            ax.grid(True)
            ax.set_ylim(0, ymax-ymin)

    axs3[-1].set_xlabel("Time (s)")
    _show_or_save_figure(
        fig3,
        console_log,
        save_path,
        suffix="erna_amp_over_time"
    )
    
    #savemat(os.path.join(save_dir, Config.f_name+'_segments.mat'), {'seg': segments})
    #console_log(f"✅ Saved unfiltered segments data.")
    save_dict_segments = {'seg': segments}
    save_dict_segments.update(all_diffs_per_channel) 
    save_dict_segments.update({'event_time': valid_trigger_times})
    if save_path is not None:
        savemat(save_path+'segments.mat', save_dict_segments)#*******************************************************************
        console_log(f"✅ Saved unfiltered segments data and ERNA amps.")

    
    if save_path is not None:
        log_file_path = save_path+'log.txt'
        with open(save_path+'log.txt', 'w', encoding='utf-8') as f:
            for line in list(self.log_history):
                f.write(line + '\n')
        console_log(f"✅ Saved log to: {log_file_path}")
    
