
import Config

class MoStim:
                 
    min_f= 50
    min_pw = 20
    min_gap = 20

    step_f = 5
    step_pw = 5
    step_gap = 5

    def __init__(self):
   
        self.frequency = self.round_to_precision(Config.ini_freq, self.min_f,self.step_f, Config.limit_frequency)
        self.pulsewidth = self.round_to_precision(Config.ini_pw, self.min_pw,self.step_pw, Config.limit_pulsewidth)
        self.gap_width = self.round_to_precision(Config.ini_gap, self.min_gap,self.step_gap, Config.limit_gapwidth)
   
    def get_limit_message(self):
        return f"DB$lim/{Config.limit_amplitude};{Config.limit_pulsewidth};{Config.limit_gapwidth};{Config.limit_frequency};#"
    
    def get_init_message(self, ramp_time, ramp_OnOff):
        
        return f"DB$set/{self.frequency};{self.pulsewidth};{self.gap_width};{Config.ini_StimPolarity_a};{Config.ini_StimPolarity_b};{ramp_time};{ramp_OnOff};{Config.ini_SignalType};{Config.ini_StimOutput};#"
      
    def get_burst_update_message(self, freq, pw, gap, amp, ch1_en, ch2_en, burst_interval, num_pulses):

        return f"DB$upBst/{freq};{pw};{gap};{amp};{amp};{ch1_en};{ch2_en};{burst_interval};{num_pulses};#"
    
    def get_single_update_message(self, pw, gap, amp, ch1_en, ch2_en):

        return f"DB$single/{pw};{gap};{amp};{amp};{ch1_en};{ch2_en};#"

    def get_continuous_update_message(self, freq, pw, gap, amp, ch1_en, ch2_en):

        return f"DB$up/{freq};{pw};{gap};{amp};{amp};{ch1_en};{ch2_en};#"

    @staticmethod
    def shutdown():
        return "DB$stp/4;#"

    @staticmethod
    def heartbeat():
        return "DB$HeartB/2;#"

    @staticmethod
    def round_to_precision(num, num_min, precision, num_max):
        num = max(num_min, min(num_max, num))
        return round(num / precision) * precision