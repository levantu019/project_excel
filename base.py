import json
import pandas as pd
import numpy as np
import params


# index column v, a
COL_STEP_D = (1, params.PARAM_STEP_D)
COL_STEP_T = (3, params.PARAM_STEP_T)
COL_V = (5, params.PARAM_V)   
COL_A = (6, params.PARAM_A)
COL_T_ACC = (7, params.PARAM_T_ACC)
COL_T_DEC = (8, params.PARAM_T_DEC)
COL_T_IDLE = (9, params.PARAM_T_IDLE)
COL_T_CRUISE = (10, params.PARAM_T_CRUISE)

COLS = [COL_STEP_D, COL_STEP_T, COL_V, COL_A, COL_T_ACC, COL_T_DEC, COL_T_IDLE]

# 
STEP_V = 1
STEP_A = 0.1

# round
DECIMAL_V = 0
DECIMAL_A = 1

# 
LIM_MIN = 0.125
LIM_MAX = 0.125


# 
DTYPE = [(i, float) for i in params.PARAMS_data]
DTYPE_ = [(i, float) for i in params.PARAMS_data_]
DTYPE_VA = [(params.PARAM_V, float), (params.PARAM_A, float)]
DTYPE_VAT = [(params.PARAM_V, float), (params.PARAM_A, float), (params.PARAM_STEP_T, float)]
DTYPE_RATIO = [(params.PARAM_STATE, DTYPE_VAT), (params.PARAM_RATIO, float)]

# 
ELEMENT_DEFAULT_VAT = np.array([(-1, -1, -1)], dtype=DTYPE_VAT)[0]
ELEMENT_DEFAULT_VA = np.array([(-1, -1)], dtype=DTYPE_VA)[0]
STATE_START = np.array([(0, 0, 0)], dtype=DTYPE_VAT)[0]
STATE_START_ACTUAL = np.array([(0, 0, 0, 0, 0, 0, 0)], dtype=DTYPE)[0]


# round array
# array = array([[a, b], ...])
def round_array(array, decimals):
    colums = []
    for val in decimals:
        colums.append(np.round(array[:,val[1]], decimals=val[0]))
        
    return np.column_stack(colums)


# From excel file (a file with multi sheet), get two column (v and a)
# excel: file name
# Return list
def generate_data_from_excel(excel):
    list_data = []

    f_excel = pd.ExcelFile(excel)
    sheet_names = f_excel.sheet_names

    for item in sheet_names:
        data = f_excel.parse(sheet_name=item).values

        # Remove nan
        isnan = np.isnan(data)
        data = data[~isnan.any(axis=1), :]
        # arr = round_array(arr, [(DECIMAL_V, COL_V), (DECIMAL_A, COL_A)])
        # data[:, COL_V[0]] = np.round(data[:, COL_V[0]], decimals=DECIMAL_V)
        # data[:, COL_A[0]] = np.round(data[:, COL_A[0]], decimals=DECIMAL_A)
        data = data[:, [col[0] for col in COLS]]

        va = []
        for item2 in data:
            if(item2[2] >= 0 and item2[2] <= 16 and np.abs(item2[3]) <= 10):
                va.append(tuple(item2))

        list_data.append(np.array(va, dtype=DTYPE))

    return list_data


# generate data v, a from data-actual
def generate_data_vat_from_actual(data_actual):
    import copy
    data_copy = copy.deepcopy(data_actual)
    data = []
    for item in data_copy:
        new_item = item[:][[COL_V[1], COL_A[1], COL_STEP_T[1]]]
        new_item[:][COL_V[1]] = np.round(new_item[:][COL_V[1]], decimals=DECIMAL_V)
        new_item[:][COL_A[1]] = np.round(new_item[:][COL_A[1]], decimals=DECIMAL_A)
        # shape = item.shape
        # item = np.resize(item, (1, shape[0]*shape[1]))
        data.extend(new_item)
        data.append(ELEMENT_DEFAULT_VAT)

    data = np.array(data, dtype=DTYPE_VAT)

    return data


# files: name excel files (ex: ['file1.xlsx', 'file2.xlsx', ...])
# Return array
def generate_data_from_multi_excel(files):
    all_data = []
    for item_f in files:
        # try:
        item_data = generate_data_from_excel(item_f)
        all_data.extend(item_data)
        # except:
        #     print(item_f)

    return all_data


# max, min v, a from data (a sheet)
# data = array([(v, a), ...], dtype=DTYPE)
def limit_va_global(data):
    sort_by_v = np.sort(data, order='v')
    sort_by_a = np.sort(data, order='a')
    # sort_by_v = np.sort(np.round(data[:, COL_V[0]], decimals=DECIMAL_V), order='v')
    # sort_by_a = np.sort(np.round(data[:, COL_A[0]], decimals=DECIMAL_A), order='a')

    min_v = sort_by_v[0][0]
    max_v = sort_by_v[-1][0]

    min_a = sort_by_a[0][1]
    max_a = sort_by_a[-1][1]

    min_v = 0

    return [np.round(min_v, decimals=DECIMAL_V), np.round(max_v, decimals=DECIMAL_V), np.round(min_a, decimals=DECIMAL_A), np.round(max_a, decimals=DECIMAL_A)]


# 
def get_intersect(data):
    data = np.unique(data[[params.PARAM_V, params.PARAM_A]])
    pos_ele_def = np.where(data == ELEMENT_DEFAULT_VA)

    return np.delete(data, pos_ele_def)


# limit = [min_v, max_v, min_a, max_a]
def shape_TPM(limit):
    [min_v, max_v, min_a, max_a] = limit

    r = 1+ (max_v - min_v) / STEP_V
    c = 1+ (max_a - min_a) / STEP_A

    return (int(r), int(c))

    
# item = (v, a)
# data_actual = [(v1, a1), ...]
# return (v_i, a_i)
def get_next_state(item, data_vat):
    result = []
    position = np.where(data_vat[[params.PARAM_V, params.PARAM_A]] == item)[0]
    for i in position:
        if i < len(data_vat) - 1:
            if data_vat[i+1] != ELEMENT_DEFAULT_VAT:
                result.append(data_vat[i+1])

    return result


# substring = [(v, a), ...]
# return = [((v, a), ratio), ...]
def calculate_ratio(substring):
    result = np.array([], dtype=DTYPE_RATIO)

    values, counts = np.unique(substring, return_counts=True)
    total = np.sum(counts)

    for idx, val in enumerate(counts):
        ratio = val / total
        result = np.append(result, np.array([(values[idx], ratio)], dtype=DTYPE_RATIO))

    return result


# item_v = min_v + k * STEP_V
# item_a = min_a + k * STEP_A
def calculate_postion(item, limit_va):
    [min_v, _, min_a, _] = limit_va

    pos_v = (item[params.PARAM_V] - min_v) / STEP_V
    pos_a = (item[params.PARAM_A] - min_a) / STEP_A

    return (int(pos_v), int(pos_a))


# return = array[[[((v, a), %), ...], ...], ...]
def generate_TPM(limit_va, intersected, data_vat):
    result = np.full(shape_TPM(limit_va), 0, dtype=list)

    for item_s in intersected:
        sub_i = get_next_state(item_s, data_vat)

        sub_i = np.array(sub_i, dtype=DTYPE_VAT)
        sub_i = calculate_ratio(sub_i)

        pos_item_s = calculate_postion(item_s, limit_va)
        result[pos_item_s[0]][pos_item_s[1]] = sub_i

    return result


# return: list time of cycles
def median_cycles(data_actual):
    times = []
    for item in data_actual:
        times.append(item.shape[0])

    return times


# return = {'v': , 'a': , ...}
def median_params_data_actual(data_actual):
    data = params.calculate_14_params(data_actual)

    return data


# choose next state
# all_states_j = array([((v, a), %), ...], dtype=DTYPE_RATIO)
def choose_next_state(all_states_j):
    states = all_states_j[params.PARAM_STATE]
    ratios = all_states_j[params.PARAM_RATIO]

    choice = np.random.choice(states, 1, p=ratios)
    
    return choice[0]


# 
def check_cycle_created(cycle, median_params=None):
    if median_params is None:
        return True
        
    # f = open('params.txt', 'a')
    # median_params = {params.PARAM_T_ACC: 34.23, params.PARAM_T_DEC: 32.26, params.PARAM_T_IDLE: 7.10, params.PARAM_T_CRUISE: 24.39, params.PARAM_V1: 7.75, params.PARAM_V2: 8.75, params.PARAM_C: 133.10, params.PARAM_M: 47.98, params.PARAM_A_AVERAGE_ACC: 0.62, params.PARAM_A_AVERAGE_DEC: -0.55, params.PARAM_PKE: 0.45, params.PARAM_RMS: 0.98, params.PARAM_T: 3004, params.PARAM_D: 23942.29}
    try:
        params_cycle = params.calculate_14_params([cycle])
    except:
        return False
    count = 0

    for param in median_params:
        param_value = median_params[param]
        cycle_value = params_cycle[param]

        # if (param_value - cycle_value) > 0.125*param_value or (param_value - cycle_value) < -0.125*param_value:
        #     count += 1
        if np.abs(param_value - cycle_value) > 0.125*param_value:
            return False

    # if count == 0:
    #     return True
    # return False
    return True

 
# main require
# T: time
# median
def calculate_cycle(TPM, limit_va, median_params, len_median):
    state_i = STATE_START
    cycle = np.array([state_i], dtype=DTYPE_VAT)

    current_time = cycle.shape[0]

    while True:
        while True:
            pos_state_i = calculate_postion(state_i, limit_va)
            state_j = choose_next_state(TPM[pos_state_i[0]][pos_state_i[1]])

            cycle = np.append(cycle, np.array([state_j], dtype=DTYPE_VAT))
            current_time += 1

            state_i = state_j

            if current_time >= 0.5*len_median and state_j[0] == 0 and state_j[1] == 0:
            # if state_j[0] == 0 and state_j[1] == 0:
                break

        cycle_actual = convert_to_actual(cycle)

        if check_cycle_created(cycle_actual, median_params):
            break
        else:
            state_i = STATE_START
            cycle = np.array([state_i], dtype=DTYPE_VAT)
            current_time = cycle.shape[0]
        # break
    return cycle


# 
def SAFD_data(data_vat, cycle):
    data = []
    for item in data_vat:
        if item != ELEMENT_DEFAULT_VAT:
            data.append(item)
    data = np.array(data, dtype=DTYPE_VAT)

    pos = np.isin(data, cycle)

    return calculate_ratio(data[pos])


# calculate SAFD_diff
def SAFD_diff(SAFD_cycle, SAFD_data):
    n = len(SAFD_cycle)

    SAFD_cycle = SAFD_cycle[params.PARAM_RATIO]
    SAFD_data = SAFD_data[params.PARAM_RATIO]

    sum1 = 0
    sum2 = 0

    for i in range(n):
        sum1 += (SAFD_cycle[i] - SAFD_data[i]) ** 2
        sum2 += SAFD_data[i] ** 2

    return 100 * sum1 / sum2


# 
def choose_best_cycle(SAFD_cycles, SAFD_datas, num):
    SAFD_diffs = []

    for i in range(num):
        SAFD_diffs.append(SAFD_diff(SAFD_cycles[i], SAFD_datas[i]))

    index = np.argmin(SAFD_diffs)

    return index, SAFD_diffs[index]


# 
def write_result(file_name, data, statistics):
    df = pd.DataFrame(data, columns =[params.PARAM_V, params.PARAM_A, params.PARAM_STEP_T])
    df.to_excel(file_name)

    stat_file = file_name + '.txt'
    f_stat = open(stat_file, 'w')

    f_stat.write('Number of states: %d\n' %statistics[0])
    f_stat.write('SAFD_diff: %f\n' %statistics[1])
    f_stat.write('Medians: %s\n' %json.dumps(statistics[2]))

    f_stat.close()


# convert dtype from vat to actual
# PARAMS_data = [PARAM_STEP_D, PARAM_STEP_T, PARAM_V, PARAM_A, 
#               PARAM_T_ACC, PARAM_T_DEC, PARAM_T_IDLE, M]
def convert_to_actual(cycle):
    state_i = STATE_START_ACTUAL
    cycle_actual = np.array([state_i], dtype=DTYPE)

    for item in cycle:
        v = item[params.PARAM_V]
        a = item[params.PARAM_A]
        step_t = item[params.PARAM_STEP_T]
        t_total = np.sum(step_t)

        step_d = v * step_t / 1000

        if a > 0.1 and v != 0:
            t_acc = step_t
        else:
            t_acc = 0

        if a < -0.1 and v != 0:
            t_dec = step_t
        else:
            t_dec = 0

        if v == 0:
            t_idle = step_t
        else:
            t_idle = 0
        
        cycle_actual = np.append(cycle_actual, np.array([(step_d, step_t, v, a, t_acc, t_dec, t_idle)], dtype=DTYPE))
    cycle_actual = np.delete(cycle_actual, 0)
    return cycle_actual
