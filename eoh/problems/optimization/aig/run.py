import numpy as np
import importlib
import sys
from .prompts import GetPrompts
# from .legalization.expr_legalize import legalization
from .legalization.abc_append import legalization
# for debug
# from prompts import GetPrompts
# # from .legalization.expr_legalize import legalization
# from legalization.abc_append import legalization

import types
import warnings
import sys
import subprocess
import os 
import re
import ast
import boolean 
import math
import random
class AIGenerator():
    def __init__(self):
        self.prompts = GetPrompts()
    
    def _legalize_(self, raw_code, truth_file_path, cec_check_path, use_fx):
        temp_program_path = self.from_raw_code_to_program(raw_code, self.folder_path, 'temp_before_legalized_program.txt')
        self.refresh(temp_program_path)
        # set optimize as False, That is, only use the sop complementary 
        legalized_code = legalization.legalization(temp_program_path, truth_file_path, self.folder_path, cec_check_path, use_fx=use_fx)
        return legalized_code
       
    def legalize(self, off, output_folder, truth_file_path, cec_check_path, use_fx, local_search=False):
        '''
            function: legalize a program
            ----------------------------
            input: off
            output: off with legalized code
        '''
        raw_code = off['code']
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        if cec_check_path is not None:
            if self.check_cec_for_equivalence(temp_program_path, cec_check_path):
                accuracy_before_legalized_off = 1.0
                fitness_before_legalized_off = off['objective']
                fitness_after_legalized_off = off['objective']
                off['accuracy'] = accuracy_before_legalized_off
                off['legalized_code'] = off['code']
                off['legalized_objective'] = fitness_after_legalized_off
                print('the off is good, no need for legalization')
            else:
                try:
                    # main_acc_list is a list which contains output_number dict
                    temp_eqn_path = os.path.join(output_folder, 'for_conversion', 'for_conversion_eqn.txt')
                    main_acc_list = self.evaluate_local_accuracy(off, truth_file_path, output_folder)
                    if local_search:
                        input_number, output_number = self.get_input_and_output_num(truth_file_path)
                        eqn_list = []
                        for i in range(output_number): 
                            highest_output = 'nothing'
                            highest_acc = 0.0
                            for key in main_acc_list[i].keys():
                                acc = float(main_acc_list[i][key][0])
                                if max(acc, 1 - acc) > highest_acc:
                                    highest_output = key
                                    highest_acc = max(acc, 1 - acc) 
                            print(f'The highest accuracy of the {i}th output of the generated program by local search is {highest_output}: {highest_acc}')
                            acc = float(main_acc_list[i][highest_output][0])
                            if acc < 0.5:
                                expr: str = main_acc_list[i][highest_output][1]
                                if '*' in expr or '+' in expr:
                                    if '*' in expr:
                                        expr = expr.replace('*', '+')
                                        op1 = expr.split('+')[0].strip()
                                        op2 = expr.split('+')[1].strip()
                                        op1 = ('!' + op1).replace('!!', '')
                                        op2 = ('!' + op2).replace('!!', '')
                                        expr = op1 + ' + ' + op2
                                    else:
                                        expr = expr.replace('+', '*')
                                        op1 = expr.split('*')[0].strip()
                                        op2 = expr.split('*')[1].strip()
                                        op1 = ('!' + op1).replace('!!', '')
                                        op2 = ('!' + op2).replace('!!', '')
                                        expr = op1 + ' * ' + op2
                                else:
                                    expr = ('!' + expr).replace('!!', '')
                                eqn_list.append(expr)
                            else:
                                eqn_list.append(main_acc_list[i][highest_output][1])
                        self.write_exprs_in_file(eqn_list, input_number, temp_eqn_path)
                        self.from_eqn_to_program(temp_eqn_path, temp_program_path) 
                        raw_code = self.from_program_to_raw_code(temp_program_path)
                        off['code'] = raw_code                                                                  
                        # if output_number == 1:
                        #     highest_output = 'nothing'
                        #     highest_acc = 0.0
                        #     for key in main_acc_dict.keys():
                        #         if float(main_acc_dict[key]) > highest_acc:
                        #             highest_output = key
                        #             highest_acc = float(main_acc_dict[key])
                        #     print(f'The highest accuracy of the generated program by local search is {highest_output}: {highest_acc}')
                        #     # replace the raw_code by the highest output
                        #     with open(temp_program_path, 'r') as f:
                        #         lines = f.readlines()
                        #     for i in range(len(lines)):
                        #         if lines[i].startswith(f'{highest_output}'):
                        #             lines[i] = lines[i].replace(f'{highest_output}', 'po0')
                        #             break
                        #     new_lines = lines[:i+1]
                        #     with open(temp_program_path, 'w') as f:
                        #         f.writelines(new_lines)
                        #     self.refresh(temp_program_path)
                        #     raw_code = self.from_program_to_raw_code(temp_program_path)
                        #     off['code'] = raw_code
                except Exception as e:
                    print(f"Wrong in evaluate local accuracy. The reason is {e}")
                try:
                    acc = self.evaluate_accuracy(off, truth_file_path, output_folder)
                    off['accuracy'] = acc
                    accuracy_before_legalized_off = acc
                    off['objective'] = self.evaluate(output_folder, raw_code)[1]
                    fitness_before_legalized_off = off['objective']
                    print(f'The before legalized accuracy of off is {acc}, thus it needs legalization')
                    print(f"The before legalized fitness of off is: {off['objective']}")
                    legalized_code = self._legalize_(raw_code, truth_file_path, cec_check_path, use_fx=use_fx)
                    off['legalized_code'] = legalized_code
                    program_nd, eqn_nd = self.evaluate(output_folder, legalized_code)
                    off['legalized_objective'] = eqn_nd
                    fitness_after_legalized_off = eqn_nd
                    print(f"The after legalized fitness of off is: {off['legalized_objective']}\n")
                except Exception as e:
                    print(f'Error in leglization. The reason is {e}')
                    off['code'] = None
                    off['legalized_code'] = None
                    off['accuracy'] = None
                    off['objective'] = None
                    off['legalized_objective'] = None
                    # accuracy_before_legalized_off = 0
                    # fitness_before_legalized_off = 10000000
                    fitness_after_legalized_off = 10000000
            return accuracy_before_legalized_off, fitness_before_legalized_off, fitness_after_legalized_off, off
        else:
            raise ValueError('cec_check_path is None. Program execution halted.')
        
    def generate_output_folder(self, output_folder, name):
        self.folder_path = os.path.join(output_folder, name)
        os.makedirs(self.folder_path, exist_ok=True)
        
    def generate_cecaig_from_truth(self, truth_file_path, label):
        '''
            function: generate for_cec_check.txt
            ------------------------------------
            input: 
                truth_file_path
                the folder path where .txt exists
            output: the .txt path
        '''
        cec_check_path = os.path.join(self.folder_path, f'for_cec_check_{label}.aig')
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; write_aiger {cec_check_path};'"
        try:
            output = subprocess.check_output(command, shell=True)
        except Exception as e:
            print(f'Error in generate cec check aig. The reason is {e}') 
        return cec_check_path

    def generate_cecaig_from_raw_code(self, raw_code, output_folder, label):
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        cec_check_path = os.path.join(self.folder_path, f'for_cec_check_{label}.aig')
        command = f"./abc -c 'read_eqn {temp_program_path}; strash; write_aiger {cec_check_path};'"
        try:
            output = subprocess.check_output(command, shell=True)
        except Exception as e:
            print(f'Error in generate cec check aig. The reason is {e}') 
        return cec_check_path
    
    def evaluate_accuracy(self, off, truth_file_path, output_folder):
        raw_code = off['code']
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        acc_list = legalization.get_accuracy(temp_program_path, truth_file_path, self.folder_path)
        for i in range(len(acc_list)):
            print(f'the {i}th expr accuracy is: {acc_list[i]}')
        average_acc = np.mean(acc_list)
        print(f'The average accuracy is {average_acc}')
        return average_acc

    def evaluate_local_accuracy(self, off, truth_file_path, output_folder):   
        raw_code = off['code']
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        acc_list = legalization.get_local_accuracy(temp_program_path, truth_file_path, self.folder_path)
        for i in range(len(acc_list)):
            for key in acc_list[i].keys():
                print(f'For the {i}th output the accuracy of expr {key} is: {acc_list[i][key][0]}')
        return acc_list
         
    def evaluate(self, output_folder, raw_code, optimize=False):
        # raw_code = self.from_python_to_raw_code(code)
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        temp_eqn_path = os.path.join(output_folder, 'for_conversion', 'for_conversion_eqn.txt')
        self.from_program_to_eqn(temp_program_path, temp_eqn_path)
        if optimize:
            self.boolean_optimize(temp_eqn_path)
        command = f"./abc -c 'read_eqn {temp_program_path}; strash; print_stats'"
        try:
            output = subprocess.check_output(command, shell=True)
            program_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
        except Exception as e:
            print(f'Error in program fitness calculation. The reason is {e}') 
        command = f"./abc -c 'read_eqn {temp_eqn_path}; strash; print_stats'"
        try:
            output = subprocess.check_output(command, shell=True)
            eqn_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1)) 
        except Exception as e:
            print(f'Error in eqn fitness calculation. The reason is {e}') 
        return program_nd, eqn_nd

    def boolean_optimize(self, eqn_path):
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
        optimized_expr_list = lines[:start_index + 1] if start_index is not None else []
        for expr in infix_exprs:
            raw_expr = expr.split('=')[1].strip()
            optimized_expr = algebra.parse(raw_expr, simplify=True)
            optimized_expr = convert_logic_string(str(optimized_expr)) 
            expr.replace(raw_expr, optimized_expr)
            optimized_expr_list.extend(expr)
        with open(eqn_path, 'w') as f:
            f.writelines(optimized_expr_list)
            
    def refresh(self, temp_program_path):
        temp_aig_path = os.path.join(self.folder_path, 'temp_for_refresh.aig')
        command = f"./abc -c 'read_eqn {temp_program_path}; strash; write_aiger {temp_aig_path}; read {temp_aig_path}; \
        write_eqn {temp_program_path}'"
        output = subprocess.check_output(command, shell=True)
        
    def from_truth_to_program(self, truth_file_path, program_path, temp_aig_path, optimize):
        if optimize == True:
            command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; resyn2; \
            write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
        else:
            command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; \
            write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
        output = subprocess.check_output(command, shell=True)
  
    def from_truth_to_function(self, truth_file_path, function_path):
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; write_eqn {function_path}'"
        output = subprocess.check_output(command, shell=True)
              
    def from_raw_code_to_program(self, raw_code, output_folder, name):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        temp_eqn_path = os.path.join(output_folder, name)
        with open(temp_eqn_path, 'w') as f:
            f.write(raw_code)
        return temp_eqn_path

    def from_program_to_raw_code(self, file_path):
        with open(file_path, 'r') as file:
            raw_code = file.read()
        # # extract the main component
        # equations = re.findall(r'([a-zA-Z0-9_]+) = (.*?);', content)
        # raw_code = ''
        # for lhs, rhs in equations:
        #     raw_code += f"{lhs} = {rhs};\n"
        return raw_code
    
    def from_program_to_eqn(self, program_path, synopsys_eqn_path, return_inner=False):
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
        
    def write_exprs_in_file(self, exprs, input_num, eqn_path):
        output_num = len(exprs)
        with open(eqn_path, 'w') as f:
            inorder_row = 'INORDER = ' + ''.join([f'pi{k} ' for k in range(input_num)]) + ';' + '\n'
            f.writelines(inorder_row)
            outorder_row = 'OUTORDER = ' + ''.join([f'po{k} ' for k in range(output_num)]) + ';' + '\n'
            f.writelines(outorder_row)
            for k in range(output_num):
                f.write(f'po{k}' + '=' + exprs[k] + ';' + '\n')
    
    def from_eqn_to_program(self, eqn_path, program_path):
        command = f"./abc -c 'read_eqn {eqn_path}; strash; write_eqn {program_path}'"
        output = subprocess.check_output(command, shell=True)
        
    def check_raw_code(self, raw_code, truth_file_path, output_folder):
        if raw_code == None:
            return False
        temp_program_path = self.from_raw_code_to_program(raw_code, os.path.join(output_folder, 'for_conversion'), 'for_conversion_program.txt')
        self.refresh(temp_program_path)
        if legalization.get_accuracy(temp_program_path, truth_file_path, self.folder_path) == None:
            return False
        return True

    def check_cec_for_equivalence(self, txt_path, aig_path):
        command_cec = f"./abc -c 'read_eqn {txt_path}; cec -n {aig_path}; print_stats'"
        output = subprocess.check_output(command_cec, shell=True)
        if 'Networks are equivalent' in str(output):
            return True
        else:
            return False
        
    def get_input_and_output_num(self, file):
        inputs, labels = self.read_val(file)
        input_number = int(math.log2(len(labels[0])))
        output_number = len(labels)
        return input_number, output_number
    
    # def get_subtruth(self, file):
    #     with open(file) as f:
    #         lines = f.readlines()
    #     return lines
    
    def read_val(self, file):
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

    def run_random_generate(self, output_path, cec_check_path, prune, sample_num, truth_file_path, threshold, threshold_nd, optimize):
        def modify_list_elements(lst, threshold):
            n = len(lst)
            m = len(lst[0])
            max_modifications = int(n * m * threshold)  # Calculate the maximum number of modifications allowed

            modifications = 0
            while modifications < max_modifications:
                row = random.randint(0, n - 1)
                col = random.randint(0, m - 1)

                if lst[row][col] == '0':
                    lst[row] = lst[row][:col] + '1' + lst[row][col + 1:]
                else:
                    lst[row] = lst[row][:col] + '0' + lst[row][col + 1:]

                modifications += 1

            lst = [ls + '\n' for ls in lst]
            return lst
        random_generate_path = os.path.join(output_path, 'random_generate')
        temp_aig_path = os.path.join(random_generate_path, 'temp_aig.aig')
        population = []
        if not os.path.exists(random_generate_path):
            os.makedirs(random_generate_path)
        inputs, labels = self.read_val(truth_file_path)
        for _ in range(sample_num):
            # randomly generate a truth table and the corresponding program
            sample_list = [''.join(list(map(str, label.tolist()))) for label in labels]
            before_legalized_random_str = modify_list_elements(sample_list, threshold)
            # check whether all 0 or all 1 in before_legalized_random_str
            if any(s.replace('\n', '') == '1' * len(s.replace('\n', '')) or s.replace('\n', '') == '0' * len(s.replace('\n', '')) for s in before_legalized_random_str):
                continue
            # before_legalized_random_str = [''.join([random.choice(['0', '1']) for _ in range(2 ** input_number)]) + "\n" for _ in range(output_number)]
            before_legalized_truth_path = os.path.join(random_generate_path, 'before_legalized_truth.truth')
            with open(before_legalized_truth_path, 'w') as f:
                f.writelines(before_legalized_random_str)
            before_legalized_program_path = os.path.join(random_generate_path, 'before_legalized_program.txt')
            self.from_truth_to_program(before_legalized_truth_path, before_legalized_program_path, temp_aig_path, optimize=optimize)
            before_legalized_code = self.from_program_to_raw_code(before_legalized_program_path)
            _, eqn_nd = self.evaluate(random_generate_path, before_legalized_code)
            if prune:
                if eqn_nd > threshold_nd:
                    continue
            print(f'The before legalized eqn node number is {eqn_nd}')
            before_legalized_program_path = self.from_raw_code_to_program(before_legalized_code, random_generate_path, 'before_legalized_program.txt')
            self.refresh(before_legalized_program_path)
            # print('The before legalized code is: \n', before_legalized_code)
            acc_list = legalization.get_accuracy(before_legalized_program_path, truth_file_path, random_generate_path)
            if acc_list == None:
                break
            for k in range(len(acc_list)):
                print(f'The {k}th expr accuracy is: {acc_list[k]}')
            average_acc = np.mean(acc_list)
            alg = {
                'algorithm': None,
                'code': None,
                'legalized_code': None,
                'accuracy': None,
                'objective': None,
                'legalized_objective': None,
                'other_inf': None
            }
            alg['code'] = before_legalized_code
            alg['accuracy'] = average_acc
            alg['objective'] = eqn_nd
            if average_acc == 1:
                print('The acc is 100%, no need for legalization')
                alg['legalized_objective'] = alg['objective']
                alg['legelized_code'] = alg['code']
            else:  
                legalized_code = legalization.legalization(before_legalized_program_path, truth_file_path, random_generate_path, cec_check_path, optimize=optimize, complementary_nd=False)
                # print('The legalized code is', legalized_code)
                # evaluate the legalized codes
                # legalized_program_path = os.path.join(random_generate_path, 'legalized_program.txt')
                self.from_raw_code_to_program(legalized_code, random_generate_path, 'legalized_program.txt')
                # don't optimize the legalized eqn
                _, eqn_nd = self.evaluate(random_generate_path, legalized_code)
                # optimize the legalized eqn
                # boolopt_program_nd, boolopt_eqn_nd, boolopt_eqn_optimized_nd = evaluate(legalized_code, txt_dir, bool_optimize=True)
                print(f'The legalized eqn node number is {eqn_nd}')
                alg['legalized_code'] = legalized_code
                alg['legalized_objective'] = eqn_nd
            population.append(alg)
        return population
                        
    def run_baselines(self, output_path, writer, truth_file_path):
        population = []
        temp_aig_path = os.path.join(output_path, 'temp.aig')
        sop_eqn_path = os.path.join(output_path, 'baseline_sop_eqn.txt')
        sop_program_path = os.path.join(output_path, 'baseline_sop_program.txt')
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; write_eqn {sop_eqn_path}; read_eqn {sop_eqn_path}; \
        strash; print_stats; write_aiger {temp_aig_path}; read {temp_aig_path}; strash; write_eqn {sop_program_path};'"
        output = subprocess.check_output(command, shell=True)
        sop_eqn_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))
        print(f'The baseline sop node number is: {sop_eqn_nd}')
        writer.add_scalar(f"sop_eqn_nd", sop_eqn_nd, 0)
        alg = {
                'algorithm': None,
                'code': None,
                'legalized_code': None,
                'accuracy': None,
                'objective': None,
                'legalized_objective': None,
                'other_inf': None
            }
        alg['accuracy'] = 1.0
        alg['code'] = self.from_program_to_raw_code(sop_program_path)
        alg['legalized_code'] = alg['code']
        alg['objective'] = sop_eqn_nd
        alg['legalized_objective'] = sop_eqn_nd
        alg['algorithm'] = ''
        population.append(alg)
        bdd_eqn_path = os.path.join(output_path, 'baseline_bdd_eqn.txt')
        bdd_program_path = os.path.join(output_path, 'baseline_bdd_progarm.txt')
        command = f"./abc -c 'read_truth -xf {truth_file_path}; bdd; write_eqn {bdd_eqn_path}; read_eqn {bdd_eqn_path}; \
        strash; print_stats; write_aiger {temp_aig_path}; read {temp_aig_path}; strash; write_eqn {bdd_program_path};'"
        output = subprocess.check_output(command, shell=True)
        bdd_eqn_nd = float(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))
        print(f'The baseline bdd node number is: {bdd_eqn_nd}')
        writer.add_scalar(f"bdd_eqn_nd", bdd_eqn_nd, 0)
        alg = {
                'algorithm': None,
                'code': None,
                'legalized_code': None,
                'accuracy': None,
                'objective': None,
                'legalized_objective': None,
                'other_inf': None
            }
        alg['accuracy'] = 1.0
        alg['code'] = self.from_program_to_raw_code(bdd_program_path)
        alg['legalized_code'] = alg['code']
        alg['objective'] = bdd_eqn_nd
        alg['legalized_objective'] = bdd_eqn_nd
        alg['algorithm'] = ''
        population.append(alg)
        threshold_nd = sop_eqn_nd
        return population, sop_eqn_nd
    
#     def from_python_to_raw_code(self, code: str):
#         '''
#             change the python code to a raw code that can be directly converted into a .txt file.
#         '''
#         print('change the python code to raw code')
#         # get input and output number from python code based on [ ]
#         input_match = re.search(r'inputs\s*=\s*\[(.*?)\]', code)
#         output_match = re.search(r'outputs\s*=\s*\[(.*?)\]', code)
#         if input_match:
#             inputs_list = ast.literal_eval('[' + input_match.group(1).strip() + ']') 
#             print("The inputs_list is:", inputs_list)
#         else:
#             print("No input_number found")
#         if output_match:
#             outputs_list = ast.literal_eval('[' + output_match.group(1).strip() + ']') 
#             print("The outputs_list is:", outputs_list)
#         else:
#             print("No output_number found")
#         input_str =  ' '.join(inputs_list).strip()
#         output_str = ' '.join(outputs_list).strip()
#         # extract the main component from the python code
#         pattern = r'\):\s*(.*?)\s*return'
#         match = re.search(pattern, code, re.DOTALL)
#         if match:
#             rest_str = match.group(1)
#             processed_rest_str = '\n'.join([line.strip() + ';' for line in rest_str.split('\n')])
#             # print("Extracted code:")
#             # print(rest_str)
#         else:
#             print("No main component found.")
#         # generate raw code
#         raw_code = f'INORDER = {input_str};\nOUTORDER = {output_str};\n{processed_rest_str}'
#         print('the raw code is:\n\n', raw_code)
#         return raw_code

#     def from_txt_to_python(self, file_path):
#         with open(file_path, 'r') as file:
#             content = file.read()
#         # extract input number and output number from txt file
#         inorder_match = re.search(r'INORDER = (.*?);', content)
#         outorder_match = re.search(r'OUTORDER = (.*?);', content)
#         if not inorder_match or not outorder_match:
#             raise ValueError("INORDER or OUTORDER not found in the file.")
#         inorder = inorder_match.group(1).split()
#         outorder = outorder_match.group(1).split()
#         # inputs = [f'pi{i}' for i in range(input_number)]
#         # outputs = [f'po{i}' for i in range(output_number)]
#         # delete INORDER and OURORDER
#         content = re.sub(r'^(INORDER|OUTORDER)[^;]*;', '', content, flags=re.MULTILINE)
#         # extract the main component
#         equations = re.findall(r'([a-zA-Z0-9_]+) = (.*?);', content)
#         code = self.generate_python_code(inorder, outorder, equations)
#         # for i in range(len(inorder)):
#         #     equations = [
#         #         (re.sub(f'{inorder[i]}', f'inputs[{i}]', lhs), (re.sub(f'{inorder[i]}', f'inputs[{i}]', rhs)))
#         #         for lhs, rhs in equations
#         #     ]
#         # for i in range(len(outorder)):
#         #     equations = [
#         #         (re.sub(f'{outorder[i]}', f'outputs[{i}]', lhs), (re.sub(f'{outorder[i]}', f'outputs[{i}]', rhs)))
#         #         for lhs, rhs in equations
#         #     ]
#         # for equation in equations:
#         #     lhs, rhs = equation
#         #     # 替换 pi 和 po 变量为 inputs 和 outputs
#         #     lhs_new = lhs
#         #     for i in range(input_number):
#         #         rhs = rhs.replace(f'pi{i}', inputs[i])
#         #     for i in range(output_number):
#         #         rhs = rhs.replace(f'po{i}', outputs[i])
#         #     translated_equations.append((lhs_new, rhs))
#         return code

#     def generate_python_code(self, inputs, outputs, equations):
#         # 生成 Python 代码形式
#         program = f"""
# def generate_aig_program(input_variables={inputs}, output_variables={outputs}):
#         """
#         # 添加方程
#         program += '\n'
#         for lhs, rhs in equations:
#             program += f"    {lhs} = {rhs}\n"

#         # 最终输出
#         program += f"\n    return {' '.join([str(outputs[i]) for i in range(len(outputs))])}\n"
#         print('the python code is \n', program)
#         return program
    

        
        
if __name__ == '__main__':
    # 文件路径
    off = {}
    file_path = './outputs/2024-12-24/00-51-55/initial_strash_program.txt'
    truth_file_path = "./benchmark/iwls2022/small_truth/ex01.truth"
    output_folder = './outputs/2024-12-24/00-51-55'
    generator = AIGenerator()
    generator.generate_aig_for_cec(truth_file_path, output_folder)
    off['code'] = generator.from_program_to_raw_code(file_path)
    acc_dict = generator.evaluate_local_accuracy(off, truth_file_path, output_folder)
