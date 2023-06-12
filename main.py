import os
import base
import params
import numpy as np
import time


# main function
def run(files_in, file_out, check):
    data_actual = base.generate_data_from_multi_excel(files_in)
    data_vat = base.generate_data_vat_from_actual(data_actual)

    limit_va = base.limit_va_global(data_vat)

    intersect = base.get_intersect(data_vat)
    TPM = base.generate_TPM(limit_va, intersect, data_vat)

    if check:
        median_params = base.median_params_data_actual(data_actual)
    else:
        median_params = None

    len_items = []
    for item in data_actual:
        len_items.append(len(item))
    len_median = np.median(len_items)

    cycles = []
    epochs = 1
    for _ in range(epochs):
        cycle = base.calculate_cycle(TPM, limit_va, median_params, len_median)
        # if not cycle in cycles:
        cycles.append(cycle)

    # SAFD_diff
    SAFD_cycles = []
    SAFD_datas = []
    num = len(cycles)

    for i in range(num):
        SAFD_cycles.append(base.calculate_ratio(cycles[i]))
        SAFD_datas.append(base.SAFD_data(data_vat, cycles[i]))

    idx_result, safd_diff = base.choose_best_cycle(SAFD_cycles, SAFD_datas, num)

    final_result = cycles[idx_result]

    base.write_result(file_out, final_result, [final_result.shape[0], safd_diff, 'median_params'])
    


# run
if __name__ == "__main__":
    check = True
    num_results = 1
    FOLDER_DATA = 'data/'
    files_in = []
    # for item in sorted(os.listdir(FOLDER_DATA), key=lambda x: int(os.path.splitext(x)[0])):
    #     files_in.append(FOLDER_DATA + item)
    for item in os.listdir(FOLDER_DATA):
        files_in.append(FOLDER_DATA + item)

    tic = time.perf_counter()
    print('Running...')
    for i in range(num_results):
        file_name = 'result{}.xlsx'.format(i)
        run(files_in, file_name, check)
        print('Done ', i)
    toc = time.perf_counter()

    print(f"Run in {toc - tic:0.4f} seconds")