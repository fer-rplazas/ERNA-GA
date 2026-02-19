clear; clc; close all;
%narrow width for full view of all stim contact in one slide
addpath(genpath('C:\GeneticAlgorithm_files\Code\GA_LSL_Chunks'));
addpath(genpath('C:\GeneticAlgorithm_files'))
% addpath(genpath("e:\GeneticAlgorithm_files"))
% addpath(genpath("u:\Recordings_2026\King's\KS41_PD_2026_02_15\ERNA - Contact Selection\Bo algorithm output"))


filt=0;%set as 1 if filter data is recorded
s=1;%scale y value

fileName='KS41_R8';

file_full=load([fileName,'_full.mat']);
file_seg=load([fileName,'_segments.mat']);
if filt==1
    file_seg_filt=load([fileName,'_segments_filtered.mat']);
end
disp(['freq: ',num2str(file_full.freq),'; pw: ',num2str(file_full.pw)])


xlim_a=-2;
xlim_b=15;
ylim_a=-200;
ylim_b=300;

data_cell=file_full.data;
len=size(data_cell,1);

fs=double(file_full.SR);
n = length(file_full.data{1, 2});

t = (0:n-1) / fs;

% figure (1)

% for i=1:len
%     subplot(len,1,i)
%     plot(t,data_cell{i, 2}-mean(data_cell{i, 2}))
%     max_y(i)=max(data_cell{i, 2}-mean(data_cell{i, 2}));
%     min_y(i)=min(data_cell{i, 2}-mean(data_cell{i, 2}));
%     ylim(1.2*[min(min_y) max(max_y)])
%     ylabel(data_cell{i,1})
% end

% for i=1:len
%     subplot(len,1,i)
%     plot(t,data_cell{i, 2})
%     ylabel(data_cell{i,1})
% end

% sgtitle 'Raw data'
% xlabel('t (s)')
% set(gcf,'position',[10 50 500 800])

figure (2)
ha=tight_subplot(8,1,[.03 .1],[.05 .08],[.24 .05]); 

[a, b, c] = size(file_seg.seg);
% t_seg = (0:c-1) / fs;
t1=-file_full.t_before;
t2=file_full.t_after;
t_seg = t1 : 1/fs : t2*2;
t_seg=t_seg(2:c+1)*1000;

for i = 1:len
    axes(ha(i))
    hold on
    valid_traces = [];  % to store valid (non-zero) traces
    for j = 1:b
        trace = squeeze(file_seg.seg(i, j, :));
        if any(trace)  % Skip segment if all zeros
            plot(t_seg, trace, 'color', [0.5 0.5 0.5]);
            valid_traces = [valid_traces; trace'];
        end
    end
    if ~isempty(valid_traces)
        avg_trace = mean(valid_traces, 1);
        plot(t_seg, avg_trace, 'color', 'red');
        plot([file_full.ta_erna file_full.ta_erna]*1000,[-file_full.ya_plot file_full.yb_plot]*10,'m:')
        plot([file_full.tb_erna file_full.tb_erna]*1000,[-file_full.ya_plot file_full.yb_plot]*10,'m:')
    end
    hold off
    set(gca, 'XTickLabelMode', 'auto');
    set(gca, 'YTickLabelMode', 'auto');
    ylim([ylim_a ylim_b])
    xlim([xlim_a xlim_b])
    ylabel(data_cell{i,1})
    
    box on
end
xlabel('t (ms)')
sgtitle 'Raw events'
set(gcf,'position',[400 50 170 800])


if filt==1
    figure (3)
    ha=tight_subplot(8,1,[.03 .1],[.05 .08],[.24 .05]); 
    for i = 1:len
        axes(ha(i))
        hold on
        valid_traces = [];  % to store valid (non-zero) traces
        for j = 1:b
            trace = squeeze(file_seg_filt.seg(i, j, :));
            if any(trace)  % Skip segment if all zeros
                plot(t_seg, trace, 'color', [0.5 0.5 0.5]);
                
                valid_traces = [valid_traces; trace'];
            end
        end
        if ~isempty(valid_traces)
            avg_trace = mean(valid_traces, 1);
            plot(t_seg, avg_trace, 'color', 'red');
            plot([file_full.ta_erna file_full.ta_erna]*1000,[-file_full.ya_plot file_full.yb_plot]*10,'m:')
            plot([file_full.tb_erna file_full.tb_erna]*1000,[-file_full.ya_plot file_full.yb_plot]*10,'m:')
        end
        hold off
        set(gca, 'XTickLabelMode', 'auto');
        set(gca, 'YTickLabelMode', 'auto');
        ylim([ylim_a ylim_b])
        xlim([xlim_a xlim_b])
        ylabel(data_cell{i,1})
        
        box on
    end
    xlabel('t (ms)')
    sgtitle 'Filtered events'
    set(gcf,'position',[700 50 170 800])
end

% figure (4)
% for i = 1:len
%     if length(file_seg.event_time)==length(file_seg.(file_full.data{i,1}))
%         yy(i)=max(file_seg.(file_full.data{i,1}));
%     end
% 
% end

% for i = 1:len
%     subplot(len,1,i)
%     box on
%     if length(file_seg.event_time)==length(file_seg.(file_full.data{i,1}))
%         plot(file_seg.event_time,file_seg.(file_full.data{i,1}),'.-')
%         ylabel(file_full.data{i,1})
%         ylim([0 max(yy)*1.2])
%     end
% 
% end
% sgtitle('Event amplitudes');
% set(gcf,'position',[1000 50 500 800])




