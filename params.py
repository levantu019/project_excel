import numpy as np
import math

import base


# name params
PARAM_STATE = 'state'
PARAM_RATIO = 'ratio'

PARAM_COUNT_STATE = 'count_state'
PARAM_D = 'd'
PARAM_T = 't'
PARAM_STEP_D = 'step_d'
PARAM_STEP_T = 'step_t'
PARAM_V = 'v'
PARAM_A = 'a'
PARAM_T_ACC = 't_acc'
PARAM_T_DEC = 't_dec'
PARAM_T_IDLE = 't_idle'
PARAM_T_CRUISE = 't_cruise'
PARAM_V1 = 'v1'
PARAM_V2 = 'v2'
PARAM_C = 'c'
PARAM_M = 'm'
PARAM_A_AVERAGE_ACC = 'a_average_acc'
PARAM_A_AVERAGE_DEC = 'a_average_dec'
PARAM_PKE = 'pke'
PARAM_RMS = 'rms'
PARAM_SQUARE_V = 'square_v'
PARAM_SQUARE_A = 'square_a'

PARAMS_data = [PARAM_STEP_D, PARAM_STEP_T, PARAM_V, PARAM_A, PARAM_T_ACC, PARAM_T_DEC, PARAM_T_IDLE]
PARAMS_data_ = [PARAM_STEP_D, PARAM_STEP_T, PARAM_V, PARAM_A, PARAM_T_ACC, PARAM_T_DEC, PARAM_T_IDLE, PARAM_M, PARAM_SQUARE_V, PARAM_SQUARE_A]
PARAMS_all = [PARAM_T_ACC, PARAM_T_DEC, PARAM_T_IDLE, PARAM_T_CRUISE, PARAM_V1, PARAM_V2, PARAM_C, PARAM_M, PARAM_A_AVERAGE_ACC, PARAM_A_AVERAGE_DEC, PARAM_PKE, PARAM_RMS, PARAM_T, PARAM_D]

# 
def calculate_14_params(data):
    result = {}

    for param in PARAMS_all:
        result[param] = []
    count = 1
    for item in data:
        if len(data) == 1:
            item = base.convert_to_actual(item)

        t_acc = np.sum(item[PARAM_T_ACC])
        t_dec = np.sum(item[PARAM_T_DEC])
        t_idle = np.sum(item[PARAM_T_IDLE])
        t_total = np.sum(item[PARAM_STEP_T])
        t_drive = t_total - t_idle
        # t_cruise = t_drive - t_acc - t_dec
        d_total = np.sum(item[PARAM_STEP_D])
        value_v = item[PARAM_V]
        value_a = item[PARAM_A]

        # 1. Ty le thoi gian tang toc
        p_t_acc = 100 * t_acc / t_total
        result[PARAM_T_ACC].append(p_t_acc)

        # 2. Ty le thoi gian giam toc
        p_t_dec = 100 * t_dec / t_total
        result[PARAM_T_DEC].append(p_t_dec)

        # 3. Ty le thoi gian khong tai
        p_t_idle = 100 * t_idle / t_total
        result[PARAM_T_IDLE].append(p_t_idle)

        # 4. Ty le thoi gian chay on dinh
        result[PARAM_T_CRUISE].append(100 - p_t_acc - p_t_idle - p_t_dec)
        t_cruise=100 - p_t_acc - p_t_idle - p_t_dec

        # 5. Van toc trung binh cua ca hanh trinh lai
        result[PARAM_V1].append(1000 * d_total / t_total)
        v1=1000 * d_total / t_total

        # 6. Van toc trung binh cua ca hanh trinh lai khong tinh thoi gian khong tai
        result[PARAM_V2].append(1000 * d_total / t_drive)
        v2=1000 * d_total / t_drive

        # 7. Do dai trung binh cua mot giai doan lai
        subs_cycle = split_cycle(item)
        # t_cycle = 0
        # for sub_cycle in subs_cycle:
        #     t_cycle += np.sum(sub_cycle[PARAM_STEP_T])
        # result[PARAM_C].append(t_cycle / len(subs_cycle))
        x = np.count_nonzero(item[PARAM_T_IDLE])
        count_idle_nonzero = x if x != 0 else 1
        result[PARAM_C].append(t_drive / count_idle_nonzero)
        c=t_drive / count_idle_nonzero

        # 8. So lan tang giam toc trung binh trong mot giai doan
        # count_acc_dec = 0
        # for sub_cycle in subs_cycle:
        #     va_v = sub_cycle[PARAM_V] > 0
        #     va_a = sub_cycle[PARAM_A] > 0
        #     count_acc_dec += len(sub_cycle[np.add(va_v, va_a)])

        # result[PARAM_M].append(count_acc_dec / len(subs_cycle))
        # if len(data) == 1:
        #     m = np.sum(item[PARAM_M])
        # else:
        m = np.count_nonzero((item[PARAM_T_ACC] > 0) | (item[PARAM_T_DEC] > 0))
        result[PARAM_M].append(m / count_idle_nonzero)
        m_m=m / count_idle_nonzero

        # 9. Gia toc trung binh cua nhung doan tang toc
        result[PARAM_A_AVERAGE_ACC].append(np.average(value_a[value_a > 0.1]))
        A=np.average(value_a[value_a > 0.1])

        # 10. Gia toc trung binh cua nhung doan giam toc
        result[PARAM_A_AVERAGE_DEC].append(np.average(value_a[value_a < -0.1]))
        D=np.average(value_a[value_a < -0.1])

        # 11. Dong nang duong
        # diff_square_va = np.square(np.roll(value_v, -1)) - np.square(value_v)
        # result[PARAM_PKE].append(np.sum(np.delete(diff_square_va, -1)) / d_total)
        # if len(data) == 1:
        #     sum_square_v = np.sum(item[PARAM_SQUARE_V])
        # else:
        shift_arr = np.empty_like(value_v)
        shift_arr[:1] = 0
        shift_arr[1:] = value_v[:-1]
        sum_square_v = np.sum(np.where(value_a > 0, np.square(value_v)-np.square(shift_arr), 0))
        result[PARAM_PKE].append(sum_square_v / (d_total * 1000))
        pke=sum_square_v / (d_total * 1000)

        # 12. Can quan phuong cua gia toc
        # result[PARAM_RMS].append(math.sqrt(np.sum(np.square(value_a)) / len(value_a)))
        # if len(data) == 1:
        #     avg_square_a = np.average(item[PARAM_SQUARE_A])
        # else:
        avg_square_a = np.average(value_a*value_a)
        result[PARAM_RMS].append(math.sqrt(avg_square_a))
        rms=math.sqrt(avg_square_a)

        # 13. Tong thoi gian di
        result[PARAM_T].append(t_total)

        # 14. Tong quang duong
        result[PARAM_D].append(d_total*1000)
        count=count+1
        # T
        # result[PARAM_COUNT_STATE] = len(item)

    # f = open('p.txt', 'w')
    for item in result:
        result[item] = np.median(result[item])
        # f.write('%s: ' %item)
        # f.write('%f\n' %result[item])

    # f.close()

    return result


# 
def split_cycle(data):
    data_v = data[PARAM_V]
    v0 = np.where(data_v == 0)[0]
    data_without_v0 = np.delete(data, v0)

    for i in range(len(v0)):
        v0[i] = v0[i] - i

    subs = np.split(data_without_v0, v0)

    result = []
    for item in subs:
        if len(item) != 0:
            result.append(item)

    return result


