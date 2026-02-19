# %%
import time
import numpy as np
from pathlib import Path

from mne_lsl.lsl import StreamInfo, StreamOutlet
from neo.io import Spike2IO

# %%

class SmrImporter:
    """Reads signals and metadata (sampling frequency ``fs``, channel names ``ch_names``) from SMR file"""

    def __init__(self, fname: Path | str):
        analog_signal = (
            Spike2IO(filename=str(fname)).read()[0].segments[0].analogsignals[0]
        )

        self.ch_names = analog_signal.array_annotations["channel_names"].tolist()

        self.ch_dict = {name: i for i, name in enumerate(self.ch_names)}

        self.fs = analog_signal.sampling_rate.magnitude

        self.data = analog_signal.magnitude.T

    def t(self):
        return np.linspace(
            0, (self.data.shape[-1] - 1.0) / self.fs, self.data.shape[-1]
        )

    def free(self):
        if hasattr(self, "data"):
            del self.data

    def __getitem__(self, key):
        return self.data[self.ch_dict[key]]



def stream_from_array(data: np.ndarray, fs: float, chunk_size: int = 1024, y:np.ndarray = None):
    """Send array as real-time LSL stream in infinite loop

    Args:
        data (np.ndarray): LFPs of shape [n_chan x n_samples]
        y (np.ndarray): Related data to send out in another stream (e.g. labels)
        fs (float): Sampling rate of the data
        chunk_size (int): number of samples to be sent out at once to stream (LSL sending frequency will be adjusted accordingly)
    """
    name = "Data Stream"
    type_ = "LFPs"
    n_chan = data.shape[0]

    info = StreamInfo(name, type_, n_chan, fs, "float64", "myUID111")
    info.set_channel_names([f"L{i+1}" for i in range(n_chan)])
    outlet = StreamOutlet(info, chunk_size=chunk_size, max_buffered=4096*4)

    if y is not None:
        info2 = StreamInfo('y_stream', '', 1, fs, "float64", "myUID112")
        outlet2 = StreamOutlet(info2, chunk_size=chunk_size, max_buffered=4096*4)

    print("sending data now ...")

    while True:
        
        for n in range(data.shape[-1]//chunk_size):
            
            samples = data[:,int(n*chunk_size):int((n+1)*chunk_size)].T

            outlet.push_chunk(samples)

            if y is not None:
                outlet2.push_chunk(y[int(n*chunk_size):int((n+1)*chunk_size)].tolist())

            time.sleep(chunk_size / fs)

# %%

if __name__ == "__main__":
    F_PATH = Path(__file__).parent.parent / "TestData" / "KS23_ERNA_sleep1_Cln_100_1100s.smr"
    importer = SmrImporter(F_PATH)
    data = importer.data[:8,:]

    stream_from_array(data, fs=float(importer.fs), chunk_size=1024//16)

# %%

# %%
