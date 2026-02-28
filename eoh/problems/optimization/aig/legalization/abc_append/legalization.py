import math
import os
import numpy as np
import subprocess
import re
from .utils_abc import read_val, from_program_to_eqn, get_expr_from_txt, \
    get_output_of_eq, from_truth_to_program, write_str_in_truth, from_program_to_raw_code, \
    get_inorder_and_outorder, check_constant, fix_program, check_cec_for_equivalence, evaluate, refresh, get_start_index\
    
def legalization(program_path, truth_file_path, txt_dir, cec_check_path, use_fx, complementary_nd=False):
    '''
        function: legalize the raw code using the abc command 'append'
        input: 
            program_path: The raw code path
            truth_file_path: The truth file used to get the complementary code 
            txt_dir: The directory path where the corresponding output file is located.
            cec_check_path: .aig file for cec check
        output:
            legalized code
    '''
    inputs, labels = read_val(truth_file_path)
    input_num = int(math.log2(len(labels[0])))
    output_num = len(labels)
    temp_aig_path = os.path.join(txt_dir, 'temp_aig.aig')
    expr_file_path = os.path.join(txt_dir, 'temp_before_legalized_eqn.txt')
    from_program_to_eqn(program_path, expr_file_path)
    
    # step 1: get the complementary program file, i.e., from 1 to 0 and from 0 to 1.
    exprs = get_expr_from_txt(expr_file_path)
    complementary_str_pre_1_lab_0 = []
    complementary_str_pre_0_lab_1 = []
    for i, (expr, input, label) in enumerate(zip(exprs, inputs, labels)):
        # print(f'{output_num} outputs in total.')
        print(f'the {i}th expr is: {expr}.')
        prediction = get_output_of_eq(expr, input)
        # find the indices with prediction=1 and label=0
        indices_pre_1_lab_0 = np.where((prediction == True) & (label == False))[0]
        complementary_input = np.ones_like(input[:,0])  # Initialize an array of ones with the same shape as 'input'
        complementary_input[indices_pre_1_lab_0] = 0
        complementary_str_pre_1_lab_0.append(''.join([str(input) for input in complementary_input]))
        # find the indices with prediction=0 and label=1
        indices_pre_0_lab_1 = np.where((prediction == False) & (label == True))[0]
        complementary_input = np.zeros_like(input[:,0])  # Initialize an array of ones with the same shape as 'input'
        complementary_input[indices_pre_0_lab_1] = 1
        complementary_str_pre_0_lab_1.append(''.join([str(input) for input in complementary_input]))

    # get the complementary program path
    complementary_pre_1_lab_0_truth_path = os.path.join(txt_dir, 'temp_complementary_pre_1_lab_0_program.truth')
    complementary_pre_1_lab_0_program_path = os.path.join(txt_dir, 'temp_complementary_pre_1_lab_0_program.txt')
    # check whether the complementary str includes constant function
    complementary_str_pre_1_lab_0, constant_indices, nonconstant_indices = check_constant(complementary_str_pre_1_lab_0, '1')
    indices = nonconstant_indices + constant_indices
    indices_mapping = {i: f'{v}' for i, v in enumerate(indices)} if len(nonconstant_indices) <=10 else {i: f'{v:02}' for i, v in enumerate(indices)}
    # check whether the str is empty
    if complementary_str_pre_1_lab_0 == []:
        inorder = ' '.join([f'pi{input}' for input in range(input_num)]) if input_num <= 10 else ' '.join([f'pi{input:02}' for input in range(input_num)])
        outorder = ' '.join([f'po{input}' for input in range(output_num)]) if output_num <= 10 else ' '.join([f'po{output:02}' for output in range(output_num)])
        lines_init = [f'INORDER = {inorder};\n', f'OUTORDER = {outorder};\n']
        lines_content = [f'po{output} = 1;\n' for output in range(output_num)] if output_num <= 10 else ' '.join([f'po{output:02} = 1' for output in range(output_num)])
        lines = lines_init + lines_content
        with open(complementary_pre_1_lab_0_program_path, 'w') as f:
            f.writelines(lines)
    else:
        write_str_in_truth(complementary_str_pre_1_lab_0, complementary_pre_1_lab_0_truth_path)
        from_truth_to_program(complementary_pre_1_lab_0_truth_path, complementary_pre_1_lab_0_program_path, temp_aig_path, use_fx=use_fx)
        fix_program(complementary_pre_1_lab_0_program_path, indices_mapping, '1')
    
    complementary_pre_0_lab_1_truth_path = os.path.join(txt_dir, 'temp_complementary_pre_0_lab_1_program.truth')
    complementary_pre_0_lab_1_program_path = os.path.join(txt_dir, 'temp_complementary_pre_0_lab_1_program.txt')
    complementary_str_pre_0_lab_1, constant_indices, nonconstant_indices = check_constant(complementary_str_pre_0_lab_1, '0')
    indices = nonconstant_indices + constant_indices
    indices_mapping = {i: f'{v}' for i, v in enumerate(indices)} if len(nonconstant_indices) <=10 else {i: f'{v:02}' for i, v in enumerate(indices)}
    
    if complementary_str_pre_0_lab_1 == []:
        inorder = ' '.join([f'pi{input}' for input in range(input_num)]) if input_num <= 10 else ' '.join([f'pi{input:02}' for input in range(input_num)])
        outorder = ' '.join([f'po{input}' for input in range(output_num)]) if output_num <= 10 else ' '.join([f'po{output:02}' for output in range(output_num)])
        lines_init = [f'INORDER = {inorder};\n', f'OUTORDER = {outorder};\n']
        lines_content = [f'po{output} = 0;\n' for output in range(output_num)] if output_num <= 10 else ' '.join([f'po{output:02} = 0' for output in range(output_num)])
        lines = lines_init + lines_content
        with open(complementary_pre_0_lab_1_program_path, 'w') as f:
            f.writelines(lines)
    else:
        write_str_in_truth(complementary_str_pre_0_lab_1, complementary_pre_0_lab_1_truth_path)
        from_truth_to_program(complementary_pre_0_lab_1_truth_path, complementary_pre_0_lab_1_program_path, temp_aig_path, use_fx=use_fx)
        fix_program(complementary_pre_0_lab_1_program_path, indices_mapping, '0')

    # step 2: make sure that the three program files have the same input names and different output names.
    refresh(program_path, txt_dir)
    refresh(complementary_pre_1_lab_0_program_path, txt_dir)
    refresh(complementary_pre_0_lab_1_program_path, txt_dir)
    outorder, outorder_pre_0_lab_1, outorder_pre_1_lab_0 = process_program_for_cmd_append(program_path, txt_dir, complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path)
    
    # step 3: use abc command 'abc' to get the combined program file.
    appended_program_path = os.path.join(txt_dir, 'temp_append_program.txt')
    append_programs(complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path, appended_program_path)
    _, eqn_nd = evaluate(from_program_to_raw_code(appended_program_path), txt_dir)
    print(f'The complementary eqn node number is {eqn_nd}')
    with open(appended_program_path, 'r') as f:
        lines = f.readlines()
    mapping = {f'po{i}': outorder_pre_0_lab_1[i] for i in range(len(outorder_pre_0_lab_1))} if len(outorder_pre_0_lab_1) <= 10 else {f'po{i:02}': outorder_pre_0_lab_1[i] for i in range(len(outorder_pre_0_lab_1))}
    for i in range(len(lines)):
        for key in mapping.keys():
            if key in lines[i]:
                lines[i] = lines[i].replace(key, mapping[key])
    with open(appended_program_path, 'w') as f:
        f.writelines(lines)
    append_programs(appended_program_path, program_path, appended_program_path)
    # step 4: process the combined program file and return the final legalized program file.        
    legalized_program_path = os.path.join(txt_dir, 'temp_legalized_program.txt')
    legalized_eqn_path = os.path.join(txt_dir, 'temp_legalized_eqn.txt')
    legal(appended_program_path, legalized_program_path, outorder, outorder_pre_0_lab_1, outorder_pre_1_lab_0, txt_dir)
    from_program_to_eqn(legalized_program_path, legalized_eqn_path)
    legalized_code = from_program_to_raw_code(legalized_program_path)
    # print('The legalized code is:', legalized_code)
    print('Start cec check!')
    assert check_cec_for_equivalence(legalized_program_path, cec_check_path)
    print('cec check successful!')
    if complementary_nd:
        return legalized_code, eqn_nd
    return legalized_code

def process_program_for_cmd_append(program_path, txt_dir, complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path):
    inorder, outorder = get_inorder_and_outorder(program_path)
    inorder_pre_1_lab_0, outorder_pre_1_lab_0 = get_inorder_and_outorder(complementary_pre_1_lab_0_program_path)
    inorder_pre_0_lab_1, outorder_pre_0_lab_1 = get_inorder_and_outorder(complementary_pre_0_lab_1_program_path)
    assert inorder == inorder_pre_1_lab_0 == inorder_pre_0_lab_1, f"different inorder for the three programs"
    
    # change the output of outorder_pre_1_lab_0
    new_outorder_pre_1_lab_0 = [f"out_1_0_{i}" for i in range(len(outorder_pre_1_lab_0))] if len(outorder_pre_1_lab_0) <= 10 else [f"out_1_0_{i:02}" for i in range(len(outorder_pre_1_lab_0))]
    # create the mapping dict
    replacement_dict = dict(zip(outorder_pre_1_lab_0, new_outorder_pre_1_lab_0))
    with open(complementary_pre_1_lab_0_program_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        for old_str, new_str in replacement_dict.items():
            line = line.replace(old_str, new_str)
        new_lines.append(line)
    with open(complementary_pre_1_lab_0_program_path, 'w') as f:
        f.writelines(new_lines)
        
    # change the output of outorder_pre_1_lab_0
    new_outorder_pre_0_lab_1 = [f"out_0_1_{i}" for i in range(len(outorder_pre_0_lab_1))] if len(outorder_pre_0_lab_1) <= 10 else [f"out_0_1_{i:02}" for i in range(len(outorder_pre_0_lab_1))]
    # create the mapping dict
    replacement_dict = dict(zip(outorder_pre_0_lab_1, new_outorder_pre_0_lab_1))
    with open(complementary_pre_0_lab_1_program_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        for old_str, new_str in replacement_dict.items():
            line = line.replace(old_str, new_str)
        new_lines.append(line)
    with open(complementary_pre_0_lab_1_program_path, 'w') as f:
        f.writelines(new_lines)
    return outorder, new_outorder_pre_0_lab_1, new_outorder_pre_1_lab_0      

def append_programs(base_program_path, appended_program_path, output_program_path):
    appended_program_aig_path = appended_program_path.replace('.txt', '.aig')
    command = f"./abc -c 'read_eqn {appended_program_path}; strash; write_aiger {appended_program_aig_path}'"
    output = subprocess.check_output(command, shell=True)
    # if optimize == True:
    #     command = f"./abc -c 'read_eqn {base_program_path}; strash; append {appended_program_aig_path}; resyn2; write_eqn {output_program_path}'"
    # else:
    command = f"./abc -c 'read_eqn {base_program_path}; strash; append {appended_program_aig_path}; write_eqn {output_program_path}'"
    output = subprocess.check_output(command, shell=True)

# def append_programs(program_path, complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path, append_program_path):
#     program_aig_path = program_path.replace('.txt', '.aig')
#     complementary_pre_1_lab_0_aig_path = complementary_pre_1_lab_0_program_path.replace('.txt', '.aig')
#     complementary_pre_0_lab_1_aig_path = complementary_pre_0_lab_1_program_path.replace('.txt', '.aig')
#     command = f"./abc -c 'read_eqn {program_path}; write_aiger {program_aig_path}'"
#     output = subprocess.check_output(command, shell=True)
#     command = f"./abc -c 'read_eqn {complementary_pre_1_lab_0_program_path}; write_aiger {complementary_pre_1_lab_0_aig_path}'"
#     output = subprocess.check_output(command, shell=True)
#     command = f"./abc -c 'read_eqn {complementary_pre_0_lab_1_program_path}; write_aiger {complementary_pre_0_lab_1_aig_path}'"
#     output = subprocess.check_output(command, shell=True)
#     command = f"./abc -c 'read {program_aig_path}; append {complementary_pre_1_lab_0_aig_path}; append {complementary_pre_0_lab_1_aig_path}; wirte_eqn {append_program_path}'"
#     output = subprocess.check_output(command, shell=True)

def legal(appended_program_path, legalized_program_path, outorder, outorder_pre_0_lab_1, outorder_pre_1_lab_0, txt_dir):
    with open(appended_program_path, 'r') as f:
        lines = f.readlines()
        # start_index = next(i for i, line in enumerate(lines) if line.startswith('new') or line.startswith('_new'))
    start_index = get_start_index(appended_program_path)
    # replacement_program_dict = {}
    # replacement_pre_0_lab_1_program_dict = {}
    # replacement_pre_1_lab_0_program_dict = {}
    # for element in outorder:
    #     for j in range(start_index, len(lines)):  # 从第二行开始检查
    #         if element in lines[j]:  # 如果该元素出现在当前行
    #             # 查找上一行等式的左边部分的数字
    #             prev_line = lines[j - 1]
    #             left_part = prev_line.split('=')[0]  # 获取等式左边部分
    #             num = int(''.join(filter(str.isdigit, left_part)))  # 提取数字部分
    #             if num:
    #                 replaced_name = left_part.replace(f'{num}', f'{num+1}')
    #                 replacement_program_dict[element] = replaced_name
    #             break
    # for element in outorder_pre_0_lab_1:
    #     for j in range(start_index, len(lines)):  # 从第二行开始检查
    #         if element in lines[j]:  # 如果该元素出现在当前行
    #             # 查找上一行等式的左边部分的数字
    #             prev_line = lines[j - 1]
    #             left_part = prev_line.split('=')[0]  # 获取等式左边部分
    #             num = ''.join(filter(str.isdigit, left_part))  # 提取数字部分
    #             if num:
    #                 replaced_name = left_part.replace(f'{num}', f'{num+1}')
    #                 replacement_pre_0_lab_1_program_dict[element] = replaced_name
    #             break
    # for element in outorder_pre_1_lab_0:
    #     for j in range(start_index, len(lines)):  # 从第二行开始检查
    #         if element in lines[j]:  # 如果该元素出现在当前行
    #             # 查找上一行等式的左边部分的数字
    #             prev_line = lines[j - 1]
    #             left_part = prev_line.split('=')[0]  # 获取等式左边部分
    #             num = ''.join(filter(str.isdigit, left_part))  # 提取数字部分
    #             if num:
    #                 replaced_name = left_part.replace(f'{num}', f'{num+1}')
    #                 replacement_pre_1_lab_0_program_dict[element] = replaced_name
    #             break

    # # 处理lines中的每一行，替换其中的元素
    # new_lines = []
    # for line in lines:
    #     for old_str, new_str in replacement_program_dict.items():
    #         if old_str in line:
    #             line = line.replace(old_str, new_str)
    #     for old_str, new_str in replacement_pre_0_lab_1_program_dict.items():
    #         if old_str in line:
    #             line = line.replace(old_str, new_str)
    #     for old_str, new_str in replacement_pre_1_lab_0_program_dict.items():
    #         if old_str in line:
    #             line = line.replace(old_str, new_str)
    #     new_lines.append(line)

    # 添加新的n行，内容是Z{i} = (F{i} + S{i}) * P{i}
    n = len(outorder)  # 这是order的长度
    for i in range(n):
        new_line = f"F{i} = ({outorder[i]} + {outorder_pre_0_lab_1[i]}) * {outorder_pre_1_lab_0[i]};\n"
        lines.append(new_line)
    for i in range(len(lines)):
        if 'OUTORDER' in lines[i]:
            new_line = ' '.join([f"F{i}" for i in range(n)])
            insert_line = f"OUTORDER = {new_line};\n"
            del lines[i:start_index]
            lines.insert(i, insert_line)
            break
            
    # 将修改后的lines写入新的文件
    if '\n' in lines:
        lines.remove('\n')
    with open(legalized_program_path, 'w') as f:
        f.writelines(lines)
    temp_aig_path = os.path.join(txt_dir, 'temp_aig.aig')
    # if optimize:
    #     command = f"./abc -c 'read_eqn {legalized_program_path}; strash; resyn2; write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {legalized_program_path}'"
    # else:
    command = f"./abc -c 'read_eqn {legalized_program_path}; strash; write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {legalized_program_path}'"
    output = subprocess.check_output(command, shell=True)
    
def get_accuracy(program_path, truth_file_path, txt_dir):
    try:
        inputs, labels = read_val(truth_file_path)
        output_num = len(labels)
        expr_file_path = os.path.join(txt_dir, 'temp_for_accuracy_eqn.txt')
        from_program_to_eqn(program_path, expr_file_path)
        exprs = get_expr_from_txt(expr_file_path)
        acc_list = []
        for i, (expr, input, label) in enumerate(zip(exprs, inputs, labels)):
            # print(f'{output_num} outputs in total \n')
            # print(f'the {i}th expr accuracy is: {expr} \n')
            prediction = get_output_of_eq(expr, input)
            wrong_number = len(np.where((prediction!=label))[0])
            all_number = len(prediction)
            acc = (all_number - wrong_number) / all_number
            acc_list.append(acc)
        return acc_list
    except Exception as e:
        print(f'Wrong raw code! No accuracy. The reason is {e}')
        return None      

def get_local_accuracy(program_path, truth_file_path, txt_dir): # only for 1 output function
    try:
        inputs, labels = read_val(truth_file_path)
        output_num = len(labels)
        expr_file_path = os.path.join(txt_dir, 'temp_for_accuracy_synopsys_eqn.txt')
        main_node_dict = from_program_to_eqn(program_path, expr_file_path, return_inner=True)
        acc_list = []
        for i in range(output_num):
            acc_dict = {}
            for key in main_node_dict.keys():
                prediction = get_output_of_eq(main_node_dict[key], inputs[0])
                wrong_number = len(np.where((prediction!=labels[i]))[0])
                all_number = len(prediction)
                acc = (all_number - wrong_number) / all_number   
                acc_dict[key] = (acc, main_node_dict[key])
            acc_list.append(acc_dict)
        return acc_list
    except Exception as e:
        print(f'Wrong raw code! No local accuracy. The reason is {e}')
        return None 
          
if __name__ == '__main__':
    print(os.getcwd())
    program_path = './outputs/2024-12-23/20-18-01/legalization/temp_before_legalized_program.txt'
    truth_file_path = './benchmark/iwls2022/small_truth/ex01.truth'
    txt_dir = './outputs/2024-12-23/20-18-01/legalization'
    cec_check_path = './outputs/2024-12-23/20-18-01/legalization/for_cec_check.aig'
    legalized_code = legalization(program_path, truth_file_path, txt_dir, cec_check_path, optimize=True)
    print('The leaglized code is', legalized_code)
    legalized_program_path = os.path.join(txt_dir, 'temp_legalized_program.txt')
    command = f"./abc -c 'read_eqn {legalized_program_path}; strash; print_stats'"
    output = subprocess.check_output(command, shell=True)
    nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
    print('The fitness is', nd)
