clear; clc; close all;
addpath(genpath('C:\GeneticAlgorithm_files\Code\GA_LSL_Chunks'));
addpath(genpath('C:\GeneticAlgorithm_files'))

fonts=12;
%plot scatter for settings, check max, min ERNA, check GA convergence
%>>>>>>>>>>>>>>>>>>>>>>colormap
color=[
% [50,205,50]
[70,130,180]
 [152,251,152]
[255,255,0]
[255,140,0]
[220,20,60]
[100,0,0]
]/255;
num=ones(length(color)-1)*80;
% num=[50 100 50];
col  = colormap_bo(color,num );
%<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
% Load data
data = readmatrix('KS41_GA_summary_Gen10.xlsx');
% gg_Gen04
% KCL_summary_Gen04
 
% Extract columns
gen = data(:,1);
eval_num = data(:,2);
freq = data(:,4);
pw = data(:,5);
erna = data(:,7);
fitness = data(:,7);

sorted_order = zeros(size(gen));
unique_gens = unique(gen);
erna_sorted_all = cell(length(unique_gens),1);

% sort by J
for i = 1:length(unique_gens)
    g = unique_gens(i);
    idx = gen == g;
    
    fitness_gen = fitness(idx);

    [~, sort_idx] = sort(fitness_gen, 'descend');

    order = 1:sum(idx);
    sorted_order_gen = zeros(sum(idx),1);
    sorted_order_gen(sort_idx) = order;
    sorted_order(idx) = sorted_order_gen;
    
    % Store for convergence plot
    erna_sorted_all{i} = erna(idx);
    erna_sorted_all{i} = erna_sorted_all{i}(sort_idx);
end
data(:,8) = sorted_order;

data_sorted = [];  % Initialize new sorted matrix
for i = 1:length(unique_gens)
    % Extract rows for this generation
    gen_rows = data(gen == unique_gens(i), :);
    % Sort by fitness descending (column 7)
    gen_sorted = sortrows(gen_rows, -7);%minus means descending order
    % Append to final sorted data
    data_sorted = [data_sorted; gen_sorted];
end

% === Find min/max ERNA overall ===
[max_erna, idx_max] = max(erna);

fprintf('Max ERNA - global (huge ^)- [gen: %d, ind: %d] freq: %d Hz, pw: %d µs, amp: %.3f \n', data(idx_max,1), data(idx_max,2), freq(idx_max), pw(idx_max), max_erna);

% === Max ERNA in final generation ===
final_gen = max(unique_gens);
idx_final = gen == final_gen;
erna_final = erna(idx_final);
freq_final = freq(idx_final);
pw_final = pw(idx_final);

[max_erna_final, idx_max_final] = max(erna_final);
fprintf('Max ERNA - final gen (^)  - [gen: %d, ind: %d] freq: %d Hz, pw: %d µs, amp: %.3f \n', final_gen,idx_max_final, freq_final(idx_max_final), pw_final(idx_max_final),max_erna_final);

target_freq = 130;
target_pw = 60;
idx_target = (freq == target_freq) & (pw == target_pw);
erna_target = erna(idx_target);
gen_target = gen(idx_target);
eval_target = eval_num(idx_target);
fprintf('Standard settings (o)     - [gen: %d, ind: %d] freq: %d Hz, pw: %d µs, amp: %.3f \n', gen_target(1), eval_target(1), target_freq, target_pw,erna_target(1) );



% === Figure 1: 2D scatter plot freq vs pw colored by erna ===
figure(1);
scatter(freq, pw, 40, erna, 'filled');
hold on
plot(freq(idx_max), pw(idx_max), 'r^', 'MarkerSize', 20, 'LineWidth', 2);
hold on
plot(130, 60, 'ko', 'MarkerSize', 10, 'LineWidth', 2);
hold on
plot(freq_final(idx_max_final), pw_final(idx_max_final), 'r^', 'MarkerSize', 10, 'LineWidth', 2);
hold on

x_teed=[90:1:145];
y_teed=freq(idx_max)*pw(idx_max)./x_teed;
% y_teed=130*60./x_teed;
% y_teed=100*90./x_teed;
plot(x_teed,y_teed,'m--','linew',1.5)

colormap(gca,col);
xlabel('Frequency');
ylabel('Pulse Width');
title('Freq vs PW colored by ERNA amplitude');
colorbar;
xlim([90 145])
ylim([20 100])
xticks(90:5:145);
yticks(20:5:100);
grid on;
set(gcf,'Position', [50, 100, 500, 300]);
%%
% === Figure 2: Convergence plot ===
%>>>>>>>>>>>>>>>>>>>>>>colormap
color=[
    [0,0,255]
[0,255,0]
[128,0,0]

]/255;
num=length(unique_gens)-1;
 
col2  = colormap_bo(color,num );
%<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

figure(2); 
hold on;
for i = 1:length(unique_gens)
    plot(erna_sorted_all{i}, '-o','color',col2(i,:), 'DisplayName', ['Gen ' num2str(unique_gens(i))]);
end
xlabel('Sorted Order (Descending Fitness)');
ylabel('ERNA Amplitude');
legend show;
title('Convergence Plot per Generation');
grid on;
set(gcf,'Position', [600, 100, 400, 300]);

% === Figure 3: Convergence trend ===
figure (3)
plot (unique_gens, cellfun(@(x) mean(x(1:min(2,end))), erna_sorted_all),'ro-')
xlabel('Gen');
ylabel('Mean ERNA');
set(gcf,'Position', [50, 500, 500, 300]);

figure (4);
[~, uniqueIdx] = unique(data(:, 4:5), 'rows', 'first');
uniqueIdx = sort(uniqueIdx);
data2 = data(uniqueIdx, :);%unique individuals

x = data2(:,4);%freq
y = data2(:,5);%pw
z = data2(:,7);%erna mean amp

F = scatteredInterpolant(x, y, z, 'natural');
[xq, yq] = meshgrid(linspace(min(x), max(x), 60), linspace(min(y), max(y), 60));
zq = F(xq, yq);
s=surf(xq, yq, zq);
shading interp;
hold on
plot3(x_teed,y_teed,1000*ones(1,length(x_teed)),'w--','linew',1.5)
xlim([90 145])
ylim([20 100])
view(2)
colormap(col);
box on
xlabel ('Frequency (Hz)','Interpreter','latex','FontSize',fonts);
ylabel ('Pulse Width ($\mu$s)','Interpreter','latex','FontSize',fonts);
set(gca,'FontSize',fonts,'TickLabelInterpreter','latex')
set(gca,'xlim',[90 145],'ylim',[20 100],'xtick',[90:5:145],'ytick',[20:5:100])

c2=colorbar;
% caxis([50 364])
c2.TickLabelInterpreter='latex';
c2.FontSize=fonts;
% c2.Ticks=[50 200 360];
% c.TickLabels={'0','0.5'};
cPos2=get(c2,'position');
cPos2=cPos2+[+0.084 0 -0.02 0]; 
set(c2,'Position',cPos2);
grid on;
set(gcf,'Position', [600, 500, 500, 300]);


