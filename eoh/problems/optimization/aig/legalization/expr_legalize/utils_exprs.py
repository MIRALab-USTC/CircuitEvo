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

def boolean_optimize(infix_expr):
    def convert_logic_string(s):
        s = s.replace("~", "!")
        s = s.replace("&", "*")
        s = s.replace("|", "+")
        return s
    algebra = boolean.BooleanAlgebra()
    # first optimize the eqn 
    if isinstance(infix_expr, list):
        optimized_expr_list = []
        for expr in infix_expr:
            optimized_expr = algebra.parse(expr, simplify=True)
            optimized_expr = convert_logic_string(str(optimized_expr)) 
            optimized_expr_list.append(optimized_expr)
        return optimized_expr_list
    else:
        optimized_expr = algebra.parse(infix_expr, simplify=True)
        optimized_expr = convert_logic_string(str(optimized_expr)) 
        return optimized_expr   

def get_file_name_and_path(file_dir):
    for file in os.listdir(file_dir):
        file_path = os.path.join(file_dir, file)
        file_name = file.split('truth')[0]
    return file_name, file_path

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
            start_index = next(i for i, line in enumerate(lines) if line.startswith('F0') or line.startswith('F_0'))
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
    temp_txt_dir_path = '/yqbai/boolfuncgen/txt_for_conversion'
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
        globals()[f'x_{i}'] = input[:, i]
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
            start_index = next(i for i, line in enumerate(lines) if line.startswith('F0') or line.startswith('F_0'))
        expr_list = []
        for i in range(start_index, len(lines)):
            if lines[i] == '\n':
                pass
            else:
                line = re.sub(r'[a-w]', lambda x: 'x_' + str(ord(x.group()) - ord('a')), lines[i])
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
    
def convert_aig_eqn_to_synopsys(aig_file_path, synopsys_eqn_path):
    with open(aig_file_path, 'r') as file:
        lines = file.readlines()
    # Parse the file to extract pi, po, and intermediate expressions
    PI_list = []
    PO_list = []
    PI_dict = {}
    PO_dict = {}
    PO_temp_dict = {}
    inner_node_dict = {}
    start_index = None
    cnt = 0
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
    #         print('error_file', aig_file_path) 
    #     else:
    #         pass
    # for po in PO_list:
    #     if check_if_exists(po, PO_list):
    #         print('error_file', aig_file)                     
    #     else:
    #         pass
    for i in range(len(PI_list)):
        PI_dict[PI_list[i]] = chr(i+97)
    for i in range(len(PO_list)):
        PO_dict[PO_list[i]] = f'F_{i}'
        PO_temp_dict[PO_list[i]] = f'F_{i}'
    output_lines = []
    inter_lines = []
    for i in range(start_index, len(lines)):
        if lines[i].startswith('F'):
            output_lines.append(lines[i])
        elif lines[i] == '\n':
            pass
        else:
            inter_lines.append(lines[i])
    lines = lines[:start_index]
    lines.extend(inter_lines)
    lines.extend(output_lines)
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
                    expr = expr.replace(f'{inner_node}', inner_node_dict[inner_node])
            if node in PO_dict.keys():
                PO_dict[node] = PO_dict[node] + ' ' + '=' + ' ' + expr
            inner_node_dict[node] = expr
    with open(synopsys_eqn_path, 'w') as output_file:
        header = lines
        header[1] = ''.join([str(PI_dict[x]) + ' ' for x in PI_dict.keys()])
        header[1] = ('INORDER' + ' ' + '=' + ' ' + header[1]).strip() + ';' + '\n'
        header[2] = ''.join([str(PO_temp_dict[x]) + ' ' for x in PO_temp_dict.keys()])
        header[2] = ('OUTORDER' + ' ' + '=' + ' ' + header[2]).strip() + ';' + '\n'
        # for pi_node in PI_dict.keys():
        #     if lines[1].find(pi_node) != -1:
        #         lines[1] = lines[1].replace(f'{pi_node}', PI_dict[pi_node])
        # for po_node in PO_dict.keys():
        #     if lines[2].find(po_node) != -1:
        #         lines[2] = lines[2].replace(f'{po_node}', PI_dict[po_node])
        output_file.writelines(header[:3])
        for node in PO_dict.keys():
            output_file.write(PO_dict[node] + ';' + '\n')

def from_txt_to_raw_code(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    # extract the main component
    equations = re.findall(r'([a-zA-Z0-9_]+) = (.*?);', content)
    raw_code = ''
    for lhs, rhs in equations:
        raw_code += f"{lhs} = {rhs};\n"
    return raw_code
    
def get_aig_from_truth(truth_file_path):
    temp_aig_path = './temp.aig'
    command = f"/yqbai/boolfuncgen/motivations/abc -c 'read_truth -xf {truth_file_path}; strash; write_aiger {temp_aig_path}'"
    output = subprocess.check_output(command, shell=True)
    return temp_aig_path

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

if __name__ == '__main__':
    aig_file_path = '/yqbai/LLM4Boolean/LLM4AIG/outputs/2024-12-11/22-27-08/temp_aig_path.txt'
    synopsys_eqn_path = '/yqbai/LLM4Boolean/LLM4AIG/outputs/2024-12-11/22-27-40/legalization/temp_synopsys_eqn.txt'
    convert_aig_eqn_to_synopsys(aig_file_path, synopsys_eqn_path)