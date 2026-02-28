import os
import re
import subprocess
import numpy as np
import math
import csv
import boolean
from collections import Counter
def convert_expr_for_abc(expr):
    return expr.replace('&', '*').replace('|', '+').replace('~', '!')
    
def read_val(file):
    '''
    Args:
        file(str): path of file of truth table
    Return:
        inputs_list: X
        labels_list: Y
    '''
    def _generate_binary_array(label, truth_flip=True): #对于n＜16
        result = []
        length = len(label)
        bit_size = int(math.log2(length))
        for i in range(length):
            row = [int(x) for x in bin(i)[2:].zfill(bit_size)]
            result.append(row)
            
        if truth_flip:
            a = np.flip(np.array(result),axis=(0,1))
            # return np.flip(a,axis=1)
            return a.copy()

        return np.array(result)
    labels = []
    with open(file) as f:
        line = f.readline()
        while line:
            label = np.array([int(x) for x in line if x>='0' and x<='9'])
            labels.append(label)
            line = f.readline()
        input = _generate_binary_array(labels[0])
    inputs = [input for _ in range(len(labels))]
    return inputs, labels

def get_file_name_and_path(file_dir):
    for file in os.listdir(file_dir):
        file_path = os.path.join(file_dir, file)
        file_name = file.split('truth')[0]
    return file_name, file_path

def write_str_in_truth(str_list, truth_file):
    with open(truth_file, 'w') as f:
        for str in str_list:
            f.write(str + '\n')
            
def write_in_txt_from_exprs(txt_dir, txt_file, exprs, input_num):
    txt_file_path = os.path.join(txt_dir, txt_file + '.txt')
    output_num = len(exprs)
    with open(txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(output_num)]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(output_num):
            f.write(f'F_{k}' + '=' + exprs[k] + ';' + '\n')
    return txt_file_path

def get_start_index(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('OUTORDER'):
            for j in range(i, len(lines)):
                if lines[j].strip().endswith(';'):
                    start_index = j+1
                    break   
    return start_index
    
def get_sharing_from_txt(file_path):
    '''
        input: file_path
        output: two int——inner_sharing and inter_sharing
    '''
    if not os.path.exists(f'{file_path}'):
        return 0, 0, 0
    else:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        start_index = get_start_index(file_path)
        expr_dict = {}
        inner_sharing = {}
        inter_sharing = {}
        for i in range(start_index, len(lines)):
            if lines[i] == '\n':
                pass
            else:
                expr_dict[f'F_{i - start_index}'] = re.findall(r'\([^()]+\)', lines[i]) 
                if expr_dict[f'F_{i - start_index}'] != None:
                    inner_sharing[f'F_{i - start_index}'] = sum(map(lambda x: x - 1, list(Counter(expr_dict[f'F_{i - start_index}']).values()))) 
                else:
                    inner_sharing[f'F_{i - start_index}'] = 0
                for j in range(start_index, i):
                    if expr_dict[f'F_{i - start_index}'] != None and expr_dict[f'F_{j - start_index}'] != None:
                        inter_expr = []
                        # print(inter_expr)
                        inter_expr.extend(expr_dict[f'F_{i - start_index}'])
                        inter_expr.extend(expr_dict[f'F_{j - start_index}'])
                        inter_sharing[f'F_{j - start_index}_{i - start_index}'] = sum(map(lambda x: x - 1, list(Counter(inter_expr).values()))) - inner_sharing[f'F_{i - start_index}'] - inner_sharing[f'F_{j - start_index}']
                    else:
                        inter_sharing[f'F_{j - start_index}_{i - start_index}'] = 0
        all_expr_dict = []
        inner_expr_dict = {}
        for i in range(start_index, len(lines)):
            if lines[i] == '\n':
                pass
            else:
                inner_expr_dict[f'F_{i - start_index}'] = re.findall(r'\([^()]+\)', lines[i]) 
                all_expr_dict.extend(inner_expr_dict[f'F_{i - start_index}'])
        all_sharing_complexity = sum([(key.count('*') + key.count('+') + key.count('!') + key.count('x')) * (frequency-1) for key, frequency in Counter(all_expr_dict).items()])
        return sum(inner_sharing.values()), sum(inter_sharing.values()), all_sharing_complexity

def get_length_from_txt(file_path):
    '''
        Args:
        txt_file_path(str): the txt file path of expr
    Return:
        prefix_length[list]
        operator_num_length[list]
    '''
    if not os.path.exists(f'{file_path}'):
        return 0, 0
    else:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            start_index = next(i for i, line in enumerate(lines) if line.startswith('F0') or line.startswith('F_0'))
        prefix_length = []
        operator_num = []
        for i in range(start_index, len(lines)):
            if lines[i] == '\n':
                pass
            else:
                line = re.sub(r'[a-w]', lambda x: 'x_' + str(ord(x.group()) - ord('a')), lines[i])
                line = line[5:]
                line = re.sub(r';$', '', line)
                prefix_length.append(line.count('*') + line.count('+') + line.count('!') + line.count('x'))
                operator_num.append(line.count('*') + line.count('+') + line.count('!')) 
        # return sum(prefix_length), sum(operator_num)
        return prefix_length, operator_num

def get_input_num_from_txt(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            input_num = lines[0].count('x')
        return input_num
    else:
        return None

def get_nd_from_txt(file_path, input_num):
    exprs = get_expr_from_txt(file_path)
    temp_txt_dir_path = './txt_for_conversion'
    temp_txt_file_path = os.path.join(temp_txt_dir_path, f'./temp_sop_init.txt')
    with open(temp_txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(exprs))]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(len(exprs)):
            f.write(f'F_{k}' + '=' + exprs[k] + ';' + '\n')
    command_truth = f"./abc -c 'read_eqn {temp_txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))  
    return nd
    
def get_nd_from_txt_with_fx(txt_file_path):
    command_truth = f"./abc -c 'read_eqn {txt_file_path}; sop; fx; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))  
    return nd

def get_nd_from_txt_directly(txt_file_path):
    command_truth = f"./abc -c 'read_eqn {txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))  
    return nd

def get_nd_from_exprs(init_merge_infix_exprs, simplification_merge_infix_exprs, input_num, file_name):
    temp_txt_dir_path = './sop_factor'
    if not os.path.exists(temp_txt_dir_path):
        os.makedirs(temp_txt_dir_path)   
    temp_txt_file_path = os.path.join(temp_txt_dir_path, f'./temp_sop_{file_name}_init.txt')
    with open(temp_txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(init_merge_infix_exprs))]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(len(init_merge_infix_exprs)):
            f.write(f'F_{k}' + '=' + init_merge_infix_exprs[k] + ';' + '\n')
    command_truth = f"./abc -c 'read_eqn {temp_txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    factor_nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))  
    temp_txt_file_path = os.path.join(temp_txt_dir_path, f'./temp_sop_{file_name}_simplification.txt')
    with open(temp_txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(simplification_merge_infix_exprs))]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(len(simplification_merge_infix_exprs)):
            f.write(f'F_{k}' + '=' + simplification_merge_infix_exprs[k] + ';' + '\n')
    command_truth = f"./abc -c 'read_eqn {temp_txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    factor_simplification_nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
    return factor_nd, factor_simplification_nd

def write_expr_in_txt(txt_dir, merge_init_infix_exprs, simplification_merge_init_exprs, symbol, input_num):
    '''
        将原始表达式和化简表达式写入txt_dir
    '''
    temp_txt_file_path = os.path.join(txt_dir, 'temp_legalized_init_synopsys_eqn.txt')
    with open(temp_txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(merge_init_infix_exprs))]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(len(merge_init_infix_exprs)):
            f.write(f'F_{k}' + '=' + merge_init_infix_exprs[k] + ';' + '\n')
    command_truth = f"./abc -c 'read_eqn {temp_txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    temp_simplification_txt_file_path = os.path.join(txt_dir, 'temp_legalized_simplification_synopsys_eqn.txt')
    with open(temp_simplification_txt_file_path, 'w') as f:
        inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
        f.writelines(inorder_row)
        outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(simplification_merge_init_exprs))]) + ';' + '\n'
        f.writelines(outorder_row)
        for k in range(len(simplification_merge_init_exprs)):
            f.write(f'F_{k}' + '=' + simplification_merge_init_exprs[k] + ';' + '\n')
    command_truth = f"./abc -c 'read_eqn {temp_txt_file_path}; strash; print_stats'"
    output = subprocess.check_output(command_truth, shell=True)
    return temp_txt_file_path, temp_simplification_txt_file_path

def get_output_of_eq(eq, input):
    """
    """
    input = input.astype(bool)
    eq = eq.replace('*', '&').replace('+', '|').replace('!', '~')
    ## define independent variables and dependent variable
    num_var = input.shape[1]
    # added by yqbai 20240418
    for i in range(num_var):
        globals()[f'pi{i}'] = input[:, i]
    f_pred = eval(eq)
    f_pred = np.array(f_pred)
    if (f_pred == True).all() :
        f_pred = [True] * input.shape[0]
        # print('f_pred is', f_pred)
        return np.array(f_pred).squeeze()
    elif (f_pred == False).all():
        f_pred = [False] * input.shape[0]
        # print('f_pred is', f_pred)
        return np.array(f_pred).squeeze()
    else:
        # print('f_pred is', f_pred)
        return f_pred.squeeze()

def get_expr_from_txt(file_path):
    '''
        Args:
        txt_file_path(str): the txt file path of expr
    Return:
        expr_list[list]
    '''
    
    if not os.path.exists(f'{file_path}'):
        return None
    else:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('OUTORDER'):
                for j in range(i, len(lines)):
                    if lines[j].strip().endswith(';'):
                        start_index = j+1
                        break  
        expr_list = []
        for i in range(start_index, len(lines)):
            if lines[i] == '\n':
                pass
            else:
                line = lines[i]
                # line = re.sub(r'[a-w]', lambda x: 'pi' + str(ord(x.group()) - ord('a')), lines[i])
                line = line.split('=')[1]
                line = line.split(';')[0]
                line = line.strip()
                expr_list.append(line)
        return expr_list

def get_supplementary_expr(truth_table, control):
    expr_list = []
    
    for row in truth_table:
        literals = []
        for i, val in enumerate(row):
            var = f'x_{i}'
            if val == 1:
                if control == '0->1':
                    literals.append(var)  # True in product term
                elif control == '1->0':
                    literals.append(f'!{var}')  # False in sum term
            else:
                if control == '0->1':
                    literals.append(f'!{var}')  # False in product term
                elif control == '1->0':
                    literals.append(var)  # True in sum term
        
        if control == '0->1':
            # For control=True, return the product term (AND) expression
            expr = '(' + '*'.join(literals) + ')'
        elif control == '1->0':
            # For control=False, return the sum term (OR) expression
            expr = '(' + '+'.join(literals) + ')'
        
        expr_list.append(expr)
    
    return expr_list

def check_cec_for_equivalence(txt_path, aig_path):
    command_cec = f"./abc -c 'read_eqn {txt_path}; cec -n {aig_path}; print_stats'"
    output = subprocess.check_output(command_cec, shell=True)
    if 'Networks are equivalent' in str(output):
        return True
    else:
        return False
    
def convert_synopsys_to_aig_eqn(synopsys_eqn_path, aig_file_path):
    command_truth = f"./abc -c 'read_eqn {synopsys_eqn_path}; strash; write_eqn {aig_file_path}'"
    output = subprocess.check_output(command_truth, shell=True)
    
def refresh(temp_program_path, output_path):
    temp_aig_path = os.path.join(output_path, './temp_aig.aig')
    command = f"./abc -c 'read_eqn {temp_program_path}; strash; write_aiger {temp_aig_path}; read_aiger {temp_aig_path}; write_eqn {temp_program_path}'"
    output = subprocess.check_output(command, shell=True)
    
def get_inorder_and_outorder(program_path):
    with open(program_path, 'r') as file:
        lines = file.readlines()
    PI_list = []
    PO_list = []
    for i, line in enumerate(lines):
        if line.strip().startswith('INORDER'):
            for j in range(i, len(lines)):
                PI_list.extend(lines[j].replace(';', ' ').split())
                if lines[j].strip().endswith(';'):
                    PI_list.remove('INORDER')
                    PI_list.remove('=')
                    break
        elif line.strip().startswith('OUTORDER'):
            for j in range(i, len(lines)):
                PO_list.extend(lines[j].replace(';', ' ').split())
                if lines[j].strip().endswith(';'):
                    PO_list.remove('OUTORDER')
                    PO_list.remove('=')
                    break  
    return PI_list, PO_list

def from_program_to_eqn(program_path, synopsys_eqn_path, return_inner=False):
    with open(program_path, 'r') as file:
        lines = file.readlines()
    # Parse the file to extract pi, po, and intermediate expressions
    PI_list = []
    PO_list = []
    PI_dict = {}
    PO_dict = {}
    PO_temp_dict = {}
    inner_node_dict = {}
    start_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith('INORDER'):
            for j in range(i, len(lines)):
                PI_list.extend(lines[j].replace(';', ' ').split())
                if lines[j].strip().endswith(';'):
                    PI_list.remove('INORDER')
                    PI_list.remove('=')
                    break
        elif line.strip().startswith('OUTORDER'):
            for j in range(i, len(lines)):
                PO_list.extend(lines[j].replace(';', ' ').split())
                if lines[j].strip().endswith(';'):
                    PO_list.remove('OUTORDER')
                    PO_list.remove('=')
                    start_index = j+1
                    break  
    # check the format of aig file
    # for pi in PI_list:
    #     if check_if_exists(pi, PI_list):
    #         print('error_file', program_path) 
    #     else:
    #         pass
    # for po in PO_list:
    #     if check_if_exists(po, PO_list):
    #         print('error_file', aig_file)                     
    #     else:
    #         pass
    for i in range(len(PI_list)):
        PI_dict[PI_list[i]] = f'pi{i}'
    for i in range(len(PO_list)):
        PO_dict[PO_list[i]] = f'po{i}'
        PO_temp_dict[PO_list[i]] = f'po{i}'
    # output_lines = []
    # inter_lines = []
    # for i in range(start_index, len(lines)):
    #     if lines[i].startswith('po'):
    #         output_lines.append(lines[i])
    #     elif lines[i] == '\n':
    #         pass
    #     else:
    #         inter_lines.append(lines[i])
    # lines = lines[:start_index]
    # lines.extend(inter_lines)
    # lines.extend(output_lines)
    for i in range(start_index, len(lines)):            
        if lines[i] != '\n':
            node, expr = lines[i].strip().split('=')
            node = node.strip()
            expr = expr.strip().replace(';', '')
            for pi_node in PI_dict.keys():
                if expr.find(pi_node) != -1:
                    expr = expr.replace(f'{pi_node}', PI_dict[pi_node])
            for inner_node in inner_node_dict.keys():
                if expr.find(inner_node) != -1 and expr[expr.find(inner_node)-1] == '!':
                    expr = expr.replace(f'{inner_node}', '(' + inner_node_dict[inner_node] + ')')
                elif expr.find(inner_node) != -1 and expr[expr.find(inner_node)-1] != '!':
                    expr = expr.replace(f'{inner_node}', '(' + inner_node_dict[inner_node] + ')')
            if node in PO_dict.keys():
                PO_dict[node] = PO_dict[node] + ' ' + '=' + ' ' + expr
            inner_node_dict[node] = expr
    with open(synopsys_eqn_path, 'w') as output_file:
        # for i in range(len(lines)):
        #     if 'INORDER' in lines[i]:
        line = ''.join([str(PI_dict[x]) + ' ' for x in PI_dict.keys()])
        line = ('INORDER' + ' ' + '=' + ' ' + line).strip() + ';' + '\n'
        output_file.write(line)
        line = ''.join([str(PO_temp_dict[x]) + ' ' for x in PO_temp_dict.keys()])
        line = ('OUTORDER' + ' ' + '=' + ' ' + line).strip() + ';' + '\n'
        output_file.write(line)
        for node in PO_dict.keys():
            output_file.write(PO_dict[node] + ';' + '\n')
    if return_inner == True:
        for node in PO_dict.keys():
            PO_dict[node] = PO_dict[node].split('=')[1].strip()
        inner_node_dict.update(PO_dict)
        return inner_node_dict
            # if 'OUTORDER' in lines[i]:
            #     line = ''.join([str(PO_temp_dict[x]) + ' ' for x in PO_temp_dict.keys()])
            #     lines[i] = line
                
        # header = lines
        # header[1] = ''.join([str(PI_dict[x]) + ' ' for x in PI_dict.keys()])
        # header[1] = ('INORDER' + ' ' + '=' + ' ' + header[1]).strip() + ';' + '\n'
        # header[2] = ''.join([str(PO_temp_dict[x]) + ' ' for x in PO_temp_dict.keys()])
        # header[2] = ('OUTORDER' + ' ' + '=' + ' ' + header[2]).strip() + ';' + '\n'
        # for pi_node in PI_dict.keys():
        #     if lines[1].find(pi_node) != -1:
        #         lines[1] = lines[1].replace(f'{pi_node}', PI_dict[pi_node])
        # for po_node in PO_dict.keys():
        #     if lines[2].find(po_node) != -1:
        #         lines[2] = lines[2].replace(f'{po_node}', PI_dict[po_node])
        # output_file.writelines(header[:3])
        # for node in PO_dict.keys():
        #     output_file.write(PO_dict[node] + ';' + '\n')
    
# def evaluate(raw_code, txt_dir):
#     program_path = os.path.join(txt_dir, 'temp_program.txt')
#     with open(program_path, 'w') as f:
#         f.write(raw_code)
#     command = f"./abc -c 'read_eqn {program_path}; strash; print_stats'"
#     output = subprocess.check_output(command, shell=True)
#     nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
#     return nd
def generate_binary_array(input_number, truth_flip=True): #对于n＜16
    result = []
    length = 2 ** input_number
    for i in range(length):
        row = [int(x) for x in bin(i)[2:].zfill(input_number)]
        result.append(row)
        
    if truth_flip:
        a = np.flip(np.array(result),axis=(0,1))
        # return np.flip(a,axis=1)
        return a.copy()

    return np.array(result)

def evaluate(raw_code, output_folder, bool_optimize=False, optimize_operator=None):
    # raw_code = self.from_python_to_raw_code(code)
    temp_folder = os.path.join(output_folder, 'for_conversion')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    temp_program_path = os.path.join(temp_folder, 'for_conversion_program.txt')
    from_raw_code_to_program(raw_code, temp_program_path)
    temp_eqn_path = os.path.join(temp_folder, 'for_conversion_eqn.txt')
    from_program_to_eqn(temp_program_path, temp_eqn_path)
    if bool_optimize:
        boolean_optimize(temp_eqn_path)
    # program
    command = f"./abc -c 'read_eqn {temp_program_path}; strash; print_stats'"
    try:
        output = subprocess.check_output(command, shell=True)
        program_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
    except Exception as e:
        print(f'Error in read_eqn {temp_program_path}. The reason is {e}') 
    # eqn
    command = f"./abc -c 'read_eqn {temp_eqn_path}; strash; print_stats'"
    try:
        output = subprocess.check_output(command, shell=True)
        eqn_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
    except Exception as e:
        print(f'Error in read_eqn {temp_eqn_path}. The reason is {e}') 
        
    if optimize_operator == 'resyn2':
        command = f"./abc -c 'read_eqn {temp_eqn_path}; strash; resyn2; print_stats'"
        try:
            output = subprocess.check_output(command, shell=True)
            optimize_eqn_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
        except Exception as e:
            print(f'Error in read_eqn {temp_eqn_path}; resyn2. The reason is {e}') 
        return program_nd, eqn_nd, optimize_eqn_nd       
    return program_nd, eqn_nd

def boolean_optimize(eqn_path):
    def convert_logic_string(s):
        s = s.replace("~", "!")
        s = s.replace("&", "*")
        s = s.replace("|", "+")
        return s
    with open(eqn_path, 'r') as f:
        lines = f.readlines()
    infix_exprs = []
    start_index = None
    for i in range(len(lines)):
        if lines[i].startswith('po'):
            if start_index == None:
                start_index = i
            infix_exprs.append(lines[i])
    algebra = boolean.BooleanAlgebra()
    # first optimize the eqn 
    optimized_expr_list = lines[:start_index] if start_index is not None else []
    for expr in infix_exprs:
        raw_expr = expr.split('=')[1].replace(';', '').strip()
        optimized_expr = algebra.parse(raw_expr, simplify=True)
        optimized_expr = convert_logic_string(str(optimized_expr)) 
        new_expr = expr.replace(raw_expr, optimized_expr)
        optimized_expr_list.append(new_expr)
    with open(eqn_path, 'w') as f:
        f.writelines(optimized_expr_list)
        
def from_program_to_raw_code(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content
    # extract the main component
    # equations = re.findall(r'([a-zA-Z0-9_]+) = (.*?);', content)
    # raw_code = ''
    # for lhs, rhs in equations:
    #     raw_code += f"{lhs} = {rhs};\n"
    # return raw_code

def from_raw_code_to_program(raw_code, program_path):
    with open(program_path, 'w') as f:
        f.write(raw_code)
        
def from_program_to_aig(program_path, aig_path):
    command =  f"./abc -c 'read_eqn {program_path}; strash; write_aiger {aig_path}'"
    output = subprocess.check_output(command, shell=True)

def from_truth_to_aig(truth_file_path):
    temp_aig_path = './temp.aig'
    command = f"./abc -c 'read_truth -xf {truth_file_path}; strash; write_aiger {temp_aig_path}'"
    output = subprocess.check_output(command, shell=True)
    return temp_aig_path

def from_truth_to_program(truth_file_path, program_path, temp_aig_path, use_fx):
    if use_fx == True:
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; fx; strash; \
        write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
    else:
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; \
        write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
    output = subprocess.check_output(command, shell=True)

def write_in_legal_csv(truth_file_path, expr_file_path, input_num, output_num, init_nd, simplification_nd, init_length, sum_init_length, init_sharing, simplification_length, sum_simplification_length, simplification_sharing):
    legal_csv_dir = './legal_csv_results'
    if not os.path.exists(legal_csv_dir):
        os.makedirs(legal_csv_dir)
    
    csv_file_path = os.path.join(legal_csv_dir, 'legal_results.csv')
    
    file_exists = os.path.isfile(csv_file_path)
    
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header only if the file does not exist
        if not file_exists:
            writer.writerow(['Truth File Path', 'expr_file_path', 'Input Num', 'Output Num', 'Init ND', 'Simplification ND', 'Init Length', 'Sum Init Length', 'Init Sharing', 'Simplification Length', 'Sum Simplification Length', 'Simplification Sharing', ])
        
        # Write the data
        writer.writerow([truth_file_path, expr_file_path, input_num, output_num, init_nd, simplification_nd, init_length, sum_init_length, init_sharing, simplification_length, sum_simplification_length, simplification_sharing])

def check_constant(complementary_str, signal):
    constant_indices = []
    nonconstant_indices = []
    new_complementary_str = []
    if signal == '1':
        for i in range(len(complementary_str)):
            if complementary_str[i].count('1') == len(complementary_str[i]):
                constant_indices.append(i)
            else:
                nonconstant_indices.append(i)
                new_complementary_str.append(complementary_str[i])
    if signal == '0':
        for i in range(len(complementary_str)):
            if complementary_str[i].count('0') == len(complementary_str[i]):
                constant_indices.append(i)
            else:
                nonconstant_indices.append(i)
                new_complementary_str.append(complementary_str[i])
    return new_complementary_str, constant_indices, nonconstant_indices

def get_accuracy(program_path, truth_file_path, txt_dir):
    try:
        inputs, labels = read_val(truth_file_path)
        output_num = len(labels)
        expr_file_path = os.path.join(txt_dir, 'temp_for_accuracy_synopsys_eqn.txt')
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
        print('Wrong raw code! No accuracy')
        return None    

def get_local_accuracy(program_path, truth_file_path, txt_dir): # only for 1 output function
    try:
        inputs, labels = read_val(truth_file_path)
        output_num = len(labels)
        expr_file_path = os.path.join(txt_dir, 'temp_for_accuracy_synopsys_eqn.txt')
        inner_node_dict = from_program_to_eqn(program_path, expr_file_path, return_inner=True)
        acc_dict = {}
        for key in inner_node_dict.keys():
            prediction = get_output_of_eq(inner_node_dict[key], inputs[0])
            wrong_number = len(np.where((prediction!=labels[0]))[0])
            all_number = len(prediction)
            acc = (all_number - wrong_number) / all_number   
            acc_dict[key] = acc
        return acc_dict
    except Exception as e:
        print('Wrong raw code! No accuracy')
        return None 
        
def fix_program(program_path, indices_mapping, signal): 
    def replace_number_in_po(po_item, mapping_value):
        po_number = re.search(r'\d+', po_item).group()
        mapped_number = re.search(r'\d+', mapping_value).group()
        return po_item.replace(po_number, mapped_number)

    with open(program_path, 'r') as f:
        lines = f.readlines()
    start_index = get_start_index(program_path)
    _, PO_list = get_inorder_and_outorder(program_path)

    existing_numbers = [int(re.search(r'\d+', item).group()) for item in PO_list]
    max_number = max(existing_numbers) if existing_numbers else 0

    while len(PO_list) < len(indices_mapping):
        max_number += 1
        new_PO = f'po{max_number}'
        PO_list.append(new_PO)

    result_dict = {po_item: replace_number_in_po(str(po_item), str(indices_mapping[i])) for i, po_item in enumerate(PO_list)}

    new_lines = []
    # only replace once in one line
    for line in lines:
        line_list = line.split(' ')
        for i in range(len(line_list)):
            for key, value in result_dict.items():
                if key in line_list[i] and key != value:
                    line_list[i] = line_list[i].replace(key, value)
                    break
        line = ' '.join(line_list)
        new_lines.append(line)
    if '\n' in new_lines:
        new_lines.remove('\n')
    if signal == '1':
        for i in range(len(existing_numbers), len(PO_list)):
            new_line = f"{list(result_dict.values())[i]} = 1;\n"
            new_lines.append(new_line)
    elif signal == '0':
        for i in range(len(existing_numbers), len(PO_list)):
            new_line = f"{list(result_dict.values())[i]} = 0;\n"
            new_lines.append(new_line)        
    else:
        raise ValueError("Invalid signal value. Expected '0' or '1'.")
    
    for i in range(len(new_lines)):
        if new_lines[i].strip().startswith('OUTORDER'):
            del new_lines[i:start_index]
            outorder_row = ' '.join([str(po) for po in PO_list])
            new_lines.insert(i, f"OUTORDER = {outorder_row};\n")
            break
    with open(program_path, 'w') as f:
        f.writelines(new_lines)
            
if __name__ == '__main__':
    aig_file_path = './outputs/2024-12-11/22-27-08/temp_aig_path.txt'
    synopsys_eqn_path = './outputs/2024-12-11/22-27-40/legalization/temp_synopsys_eqn.txt'
    from_program_to_eqn(aig_file_path, synopsys_eqn_path)
