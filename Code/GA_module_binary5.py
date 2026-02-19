# rev:binary: change to binary mode
# rev: binary2: add track info
# rev: binary3: update crossover, mutation
# rev: binary4: update binary_crossover
# rev: binary5: limit individual int range

import os
import random
from deap import base, creator, tools
import openpyxl
from openpyxl.styles import Font
from datetime import datetime
import Config

# === Parameter Ranges ===
freq_range = list(range(90, 146, 5))
pw_range = list(range(20, 101, 5))

# GA Settings
no_gen = 10
first_gen_size = 12
other_gen_size = 8


# Fixed parameters
gap = 20
burst_interval = 100
num_pulses = 2
ampli = 4500
# Binary lengths
freq_bits = (len(bin(len(freq_range) - 1)) - 2)
pw_bits = (len(bin(len(pw_range) - 1)) - 2)
total_bits = freq_bits + pw_bits

# DEAP setup
if "FitnessMax" not in creator.__dict__:
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if "Individual" not in creator.__dict__:
    creator.create("Individual", list, fitness=creator.FitnessMax, origin=None, details=None)

toolbox = base.Toolbox()

# === Binary Utility Functions ===
def int_to_bin(n, bits):
    return format(n, f'0{bits}b')

def bin_to_int(b):
    return int(b, 2)

def binary_to_individual(bin_str):
    freq_bin = bin_str[:freq_bits]
    pw_bin = bin_str[freq_bits:]
    freq_idx = min(bin_to_int(freq_bin), len(freq_range) - 1)
    pw_idx = min(bin_to_int(pw_bin), len(pw_range) - 1)
    return creator.Individual([freq_idx, pw_idx])

def print_individuals_verbose(individuals, title=""):
    if title:
        print(f"\n--- {title} ---")
    for i, ind in enumerate(individuals):
        freq_idx, pw_idx = ind[0], ind[1]
        freq_val = freq_range[freq_idx]
        pw_val = pw_range[pw_idx]
        freq_bin = int_to_bin(freq_idx, freq_bits)
        pw_bin = int_to_bin(pw_idx, pw_bits)
        print(f"Individual {i+1}: Freq={freq_val} Hz (bin: {freq_bin}) | PW={pw_val} µs (bin: {pw_bin}) | Origin={getattr(ind, 'origin', '')}")
        
# === Initialization ===
toolbox.register("attr_bin", lambda: ''.join(random.choice('01') for _ in range(total_bits)))

def generate_valid_individual():
    while True:
        try:
            return binary_to_individual(toolbox.attr_bin())
        except ValueError:
            continue

toolbox.register("individual", generate_valid_individual)
#toolbox.register("individual", lambda: binary_to_individual(toolbox.attr_bin()))
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# === Crossover and Mutation ===
def binary_crossover(ind1, ind2):
    b1 = int_to_bin(ind1[0], freq_bits) + int_to_bin(ind1[1], pw_bits)
    b2 = int_to_bin(ind2[0], freq_bits) + int_to_bin(ind2[1], pw_bits)

    max_cros_len = total_bits - 2
    for _ in range(50):
        cros_len = random.randint(2, max_cros_len)
        point = random.randint(0, total_bits - cros_len)

        new_b1 = b1[:point] + b2[point:point + cros_len] + b1[point + cros_len:]
        new_b2 = b2[:point] + b1[point:point + cros_len] + b2[point + cros_len:]

        try:
            c1 = binary_to_individual(new_b1)
            c2 = binary_to_individual(new_b2)
            c1.origin = "crossover"
            c2.origin = "crossover"
            c1.details = f"point={point}, cros_len={cros_len}, {b1}→{new_b1}"
            c2.details = f"point={point}, cros_len={cros_len}, {b2}→{new_b2}"
            return c1, c2
        except ValueError:
            continue

    # If all retries fail, fallback to random
    fallback1 = toolbox.individual()
    fallback1.origin = "random"
    fallback1.details = "fallback after crossover retries"

    fallback2 = toolbox.individual()
    fallback2.origin = "random"
    fallback2.details = "fallback after crossover retries"

    return fallback1, fallback2

def binary_mutation(ind, indpb=0.2):
    b = int_to_bin(ind[0], freq_bits) + int_to_bin(ind[1], pw_bits)

    for _ in range(50):
        mutated = []
        flips = []
        for i, bit in enumerate(b):
            if random.random() < indpb:
                mutated.append('1' if bit == '0' else '0')
                flips.append(i)
            else:
                mutated.append(bit)
        new_bin = ''.join(mutated)
        try:
            new_ind = binary_to_individual(new_bin)
            new_ind.origin = "mutation"
            new_ind.details = f"flipped bits: {flips}" if flips else "no flip"
            return (new_ind,)
        except ValueError:
            continue

    # Fallback if mutation fails
    fallback = toolbox.individual()
    fallback.origin = "random"
    fallback.details = "fallback after mutation retries"
    return (fallback,)

toolbox.register("mate", binary_crossover)
toolbox.register("mutate", binary_mutation)
toolbox.register("select", tools.selTournament, tournsize=7)#this line is not useful

# === Export to Excel ===
def export_to_excel(generator_output, generation_number, save_folder, prefix="GA_output"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Gen {generation_number}"

    headers = [
        "Generation", "Individual", "Freq (Hz)", "Pulse Width (Âµs)",
        "Gap", "Amplitude", "Burst Interval", "Num Pulses",
        "Fitness", "Origin", "Details"
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for data in generator_output:
        fitness = data["ind_obj"].fitness.values[0] if data["ind_obj"].fitness.valid else None
        ws.append([
            data["generation"],
            data["individual"],
            data["freq"],
            data["pw"],
            data["gap"],
            data["amp"],
            data["burst_interval"],
            data["num_pulses"],
            fitness,
            data.get("origin", ""),
            data.get("details", "")
        ])

    for col in ws.columns:
        max_len = max((len(str(cell.value)) for cell in col if cell.value is not None), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    excel_filename = f"{prefix}_gen{generation_number:02d}.xlsx"
    excel_path = os.path.join(save_folder, excel_filename)
    wb.save(excel_path)
    print(f"--------version: 5; Exported Gen {generation_number}: { excel_filename}----------")


# === Generator with export after each generation ===
def ga_generator(manual_individuals_text=None):
    pop = []
    seen_individuals = set()

    # === Preset Individuals ===
    for line in Config.preset_seen_individuals_text.strip().splitlines():
        freq, pw = map(int, line.strip().split())
        freq_idx = freq_range.index(freq)
        pw_idx = pw_range.index(pw)
        ind = creator.Individual([freq_idx, pw_idx])
        ind.origin = "preset"
        ind.details = f"preset: Freq={freq}, PW={pw}"
        seen_individuals.add((freq_idx, pw_idx))
        pop.append(ind)

    # === Manual Individuals ===
    if manual_individuals_text:
        for line in manual_individuals_text.strip().splitlines():
            freq, pw = map(int, line.strip().split())
            freq_idx = freq_range.index(freq)
            pw_idx = pw_range.index(pw)
            ind = creator.Individual([freq_idx, pw_idx])
            ind.origin = "manual"
            ind.details = f"manual input: Freq={freq}, PW={pw}"
            pop.append(ind)
            seen_individuals.add((freq_idx, pw_idx))

    while len(pop) < first_gen_size:
        ind = toolbox.individual()
        while tuple(ind) in seen_individuals:
            ind = toolbox.individual()
        ind.origin = "random"
        ind.details = "random init"
        seen_individuals.add(tuple(ind))
        pop.append(ind)
    
    random.shuffle(pop)
    
    # === Generation Loop ===
    for gen in range(no_gen):
        if gen > 0:
            hof = tools.HallOfFame(Config.eli)
            hof.update(pop)
            for elite in hof:
                elite.origin = "elite"
                elite.details = "top performer from previous gen"
            
            sorted_pop = sorted(pop, key=lambda ind: ind.fitness.values[0], reverse=True)
            selected = [sorted_pop[0], sorted_pop[1], sorted_pop[2], sorted_pop[3]] 
            print_individuals_verbose(selected, title=f"Generation {gen+1} - Top 4 Selected Individuals")
            id_cro = random.sample(range(4), 2)#pick 2 out of top 4 for crossover
            
            offspring = list(map(toolbox.clone, selected))

            new_offspring = []
            for i in range(0, other_gen_size - len(hof), 2):
                if random.random() < 0.7:
                    trial = 0
                    c1, c2 = None, None
                    while trial < 50:
                        trial += 1
                        temp_c1, temp_c2 = toolbox.mate(offspring[id_cro[0]], offspring[id_cro[1]])
                        temp_c1_key = tuple(temp_c1)
                        temp_c2_key = tuple(temp_c2)
            
                        # Check if at least one of the children is new
                        if temp_c1_key not in seen_individuals or temp_c2_key not in seen_individuals:
                            c1 = temp_c1 if temp_c1_key not in seen_individuals else None
                            c2 = temp_c2 if temp_c2_key not in seen_individuals else None
                            break
            
                    # If failed to find new individuals, default to random
                    if c1 is None:
                        c1 = toolbox.individual()
                        c1.origin = "random"
                        c1.details = "fallback after crossover retries"
                    if c2 is None and (i + 1 < other_gen_size - len(hof)):
                        c2 = toolbox.individual()
                        c2.origin = "random"
                        c2.details = "fallback after crossover retries"
            
                    new_offspring.append(c1)
                    if i + 1 < other_gen_size - len(hof):
                        new_offspring.append(c2)
                else:
                    new_offspring.append(offspring[id_cro[0]])
                    if i + 1 < other_gen_size - len(hof):
                        new_offspring.append(offspring[id_cro[1]])
            

            mutated_offspring = []
            for ind in new_offspring:
                if random.random() < 0.3:
                    ind, = toolbox.mutate(ind)
                mutated_offspring.append(ind)

            unique_offspring = []
            for ind in mutated_offspring:
                while tuple(ind) in seen_individuals:
                    ind = toolbox.individual()
                    ind.origin = "random"
                    ind.details = "replaced duplicate"
                seen_individuals.add(tuple(ind))
                unique_offspring.append(ind)

            pop = list(hof) + unique_offspring

        # === Yield and Export This Generation ===
        current_generation_data = []
        for j, ind in enumerate(pop):
            record = {
                "generation": gen + 1,
                "individual": j + 1,
                "freq": freq_range[ind[0]],
                "pw": pw_range[ind[1]],
                "gap": gap,
                "amp": ampli,
                "burst_interval": burst_interval,
                "num_pulses": num_pulses,
                "ind_obj": ind,
                "origin": getattr(ind, "origin", "unknown"),
                "details": getattr(ind, "details", "")
            }
            current_generation_data.append(record)

        # Export current generation
        export_to_excel(current_generation_data, generation_number=gen + 1, save_folder=os.path.join(os.getcwd(), "GA_LSL_Chunks"))

        # Yield results one by one if needed
        for record in current_generation_data:
            yield record