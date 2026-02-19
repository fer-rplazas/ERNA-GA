clear; clc; close all;

addpath(genpath('C:\GeneticAlgorithm_files\liblsl-Matlab'));   % <- Update this

% Load SMR file
FullFileName = 'C:\GeneticAlgorithm_files\TestData\KS23_ERNA_sleep1_Cln_100_1100s.smr';
addpath(genpath('C:\GeneticAlgorithm_files'));  % Add your code/toolbox folders

% Load CEDS64 library
cedpath = getenv('CEDS64ML');
addpath(cedpath);
CEDS64LoadLib(cedpath);

ChsTts = {'L1'; 'L2'; 'L3'; 'L4'; 'L5'; 'L6'; 'L7'; 'L8'};

% Open SMR
RW_Mode = 1;  % Read only
[fsmr, WaveChans, ~] = Smr64_FileOpen(FullFileName, RW_Mode);
WvChsTts = WaveChans.WvTits;
%%
% Match desired channels
nChs = length(ChsTts);%8
ChsNms = [];
for ich = 1:nChs
    chName = ChsTts{ich};
    idx = find(strcmp(chName, [WvChsTts{:}]));
    if ~isempty(idx)
        ChsNms(end+1) = idx;
    else
        warning("Channel %s not found", chName);
    end
end

if length(ChsNms) ~= nChs
    error("Not all desired channels found.");
end

% Read selected channels
SelAllChsDta = [];
for i = 1:nChs
    waveNum = WaveChans.WvNums(ChsNms(i));
    [waveData, SR] = Smr64_ReadWaveChan(fsmr, waveNum);
    SelAllChsDta(i, :) = double(waveData(:)');
end

CEDS64Close(fsmr);  % Close SMR file

fprintf('Loaded %d channels at %.2f Hz, total %d samples\n', ...
    nChs, SR, size(SelAllChsDta,2));

% ==== LSL SETUP ====
disp('Setting up LSL stream...');
lib = lsl_loadlib();

streamName = 'botest20000002';
streamType = 'test_Bo2';

info = lsl_streaminfo(lib, streamName, streamType, nChs, SR, 'cf_float32', 'myuid1234');

% Add channel names
channels = info.desc().append_child('channels');
for i = 1:nChs
    channel = channels.append_child('channel');
    channel.append_child_value('label', ChsTts{i});
    channel.append_child_value('unit', 'uV');
    channel.append_child_value('type', 'EEG');
end

outlet = lsl_outlet(info);
disp('LSL outlet created.');

% ==== STREAMING ====
chunk_duration = 0.5;  % seconds
samples_per_chunk = round(SR * chunk_duration);
samples_per_chunk=1000;
% samples_per_chunk=40;
total_samples = size(SelAllChsDta, 2);
nChunks = floor(total_samples / samples_per_chunk);

disp(['Broadcasting ' num2str(nChunks) ' chunks of ' num2str(samples_per_chunk) ' samples each...']);

for k = 1:nChunks
    idx_start = (k-1)*samples_per_chunk + 1;
    idx_end = k*samples_per_chunk;
    chunk = SelAllChsDta(:, idx_start:idx_end);  % [channels x samples]
    outlet.push_chunk(chunk);
    fprintf('Sent chunk %d/%d\n', k, nChunks);
    pause(1);  % simulate real-time
end

disp('Streaming complete.');
% clear outlet;
% clear all;