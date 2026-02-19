clear; clc; close all;
addpath(genpath('C:\GeneticAlgorithm_files'));  % Add your code/toolbox folders

addpath(genpath('C:\GeneticAlgorithm_files\TestData'));   % <- Update this
addpath(genpath('C:\GeneticAlgorithm_files\liblsl-Matlab'));   % <- Update this

file_full=load('S_MorningMedOFF_ERNA_PairedPulsesAtSetting_full.mat');

cedpath = getenv('CEDS64ML');
addpath(cedpath);
CEDS64LoadLib(cedpath);

% ==== LOAD DATA ====
% Assumes 'file_full.mat' contains:
% file_full.data: 8x2 cell array {channel_name, channel_data}
% file_full.SR: sampling rate

disp('Loading .mat file...');

nChs = size(file_full.data, 1);  % Number of channels
SR = double(file_full.SR);               % Sampling rate

% Extract channel names
ChsTts = cell(nChs, 1);
for i = 1:nChs
    ChsTts{i} = file_full.data{i, 1};
end

% Extract data into matrix [channels x samples]
numSamples = length(file_full.data{1, 2});  % assume same length for all channels
SelAllChsDta = zeros(nChs, numSamples);
for i = 1:nChs
    SelAllChsDta(i, :) = file_full.data{i, 2};
end

% ==== LSL SETUP ====
disp('Setting up LSL stream...');
lib = lsl_loadlib();

streamName = 'botest2500';
streamType = 'test_Bo';

info = lsl_streaminfo(lib, streamName, streamType, nChs, SR, 'cf_float32', 'myuid1234');

% Add channel metadata
channels = info.desc().append_child('channels');
for i = 1:nChs
    channel = channels.append_child('channel');
    channel.append_child_value('label', ChsTts{i});
    channel.append_child_value('unit', 'uV');
    channel.append_child_value('type', 'EEG');
end

% Create outlet
outlet = lsl_outlet(info);
disp('LSL outlet created.');

% ==== STREAMING ====
chunk_duration_sec = 0.5;  % seconds (for pause simulation)
samples_per_chunk = 1000;  % samples per chunk
total_samples = size(SelAllChsDta, 2);
nChunks = floor(total_samples / samples_per_chunk);

disp(['Broadcasting ' num2str(nChunks) ' chunks of ' num2str(samples_per_chunk) ' samples each...']);

startChunk = 1;  % or 120 if you want to start later

for k = startChunk:nChunks
    idx_start = (k - 1) * samples_per_chunk + 1;
    idx_end = k * samples_per_chunk;

    % Extract chunk: [channels x samples]
    chunk = SelAllChsDta(:, idx_start:idx_end);

    % Push chunk to LSL (convert to float32)
    outlet.push_chunk(chunk);

    fprintf('Sent chunk %d/%d\n', k, nChunks);

    % Simulate real-time delay for the chunk
    pause(samples_per_chunk / SR);
end

disp('Streaming complete.');