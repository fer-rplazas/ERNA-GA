#%%

import time
from mne_lsl.lsl import StreamInlet, resolve_streams

def receive_and_log(stream_name):

    inlet = StreamInlet(resolve_streams(name=stream_name)[0])
    print(f"✅ Connected to stream '{inlet.name}'")

    while True:
        samples, tstamps = inlet.pull_chunk(timeout=1.0)
        print(samples)
        
        time.sleep(0.1)


receive_and_log("Data Stream")
# %%
