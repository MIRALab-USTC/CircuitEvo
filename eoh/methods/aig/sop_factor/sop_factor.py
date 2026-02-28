'''
1. 给定真值表路径得到真值表x,y
2. 遍历输入变量，返回分解后的子真值表，并将每个子真值表的表达式合在一起再送入strash，check是否有比原始sop小的变量
'''
import os
import csv
import subprocess
import re
import numpy as np
import math
import boolean
from .utils_abc import get_accuracy, evaluate, generate_binary_array, check_cec_for_equivalence, \
    get_start_index, get_inorder_and_outorder, refresh

class Sop_factor():
    def __init__(self, truth_file_path, file_name, output_path):
        self.truth_file_path = truth_file_path
        self.file_name = file_name
        self.output_path = output_path
        
    def shannon_decomposition(self):
        eqn_path = os.path.join(self.output_path, 'sop_factor.txt')
        cec_check_path = os.path.join(self.output_path, 'cec_for_check.aig')
        command_truth = f"./abc -c 'read_truth -xf {self.truth_file_path}; collapse; sop; write_eqn {eqn_path}; \
            read_eqn {eqn_path}; strash; write_aiger {cec_check_path}; print_stats'"
        output = subprocess.check_output(command_truth, shell=True)
        inputs, outputs = self.read_val(self.truth_file_path) # inputs是一个array，outputs是一个list           
        input_num = int(math.log2(len(outputs[0])))
        factor_init_nd_list = []
        factor_variable_list = list(range(input_num))
        for factor_variable in factor_variable_list:
            left_infix_exprs = []
            right_infix_exprs = []
            left_infix_exprs_path = os.path.join(self.output_path, 'temp_left_infix_exprs.txt')
            right_infix_exprs_path = os.path.join(self.output_path, 'temp_right_infix_exprs.txt')
            left_program_path = os.path.join(self.output_path, 'temp_left_program.txt')
            right_program_path = os.path.join(self.output_path, 'temp_right_program.txt')
            append_program_path = os.path.join(self.output_path, 'temp_append_program.txt')
            for x, y in zip(inputs, outputs):   
                init_expr_left, init_expr_right = self.sop_factor(x, y, factor_variable)
                init_expr_left = self.correct_shannon_expr(init_expr_left, factor_variable, input_num)
                init_expr_right = self.correct_shannon_expr(init_expr_right, factor_variable, input_num)
                init_expr_left = f'x_{factor_variable}' + '*' + '(' + f'{init_expr_left}' + ')'
                init_expr_right = f'!x_{factor_variable}' + '*' + '(' + f'{init_expr_right}' + ')' 
                left_infix_exprs.append(init_expr_left)
                right_infix_exprs.append(init_expr_right)
            # left_infix_exprs = list(map(lambda x: x[0], init_merge_infix_exprs))
            # right_infix_exprs = list(map(lambda x: x[1], init_merge_infix_exprs))
            self.write_eqn_in_txt(left_infix_exprs, left_infix_exprs_path, input_num)
            self.write_eqn_in_txt(right_infix_exprs, right_infix_exprs_path, input_num)
            self.from_eqn_to_program(left_infix_exprs_path, left_program_path)
            self.from_eqn_to_program(right_infix_exprs_path, right_program_path)
            self.append_program(left_program_path, right_program_path, append_program_path)
            raw_code = self.from_program_to_raw_code(append_program_path)
            assert self.check_cec_for_equivalence(append_program_path, cec_check_path)
            _, eqn_nd = evaluate(raw_code, self.output_path)
            factor_init_nd_list.append(eqn_nd)
        best_factor_variable = factor_variable_list[factor_init_nd_list.index(min(factor_init_nd_list))]
        left_infix_exprs = []
        right_infix_exprs = []
        for x, y in zip(inputs, outputs):   
            init_expr_left, init_expr_right = self.sop_factor(x, y, best_factor_variable)
            left_infix_exprs.append(init_expr_left)
            right_infix_exprs.append(init_expr_right)
        left_sub_truth_path = os.path.join(self.output_path, 'best_left_truth.truth')
        right_sub_truth_path = os.path.join(self.output_path, 'best_right_truth.truth')
        left_infix_exprs_path = os.path.join(self.output_path, 'best_left_sop_eqn.txt')
        right_infix_exprs_path = os.path.join(self.output_path, 'best_right_sop_eqn.txt')
        best_left_program_path = os.path.join(self.output_path, 'best_left_sop_program.txt')
        best_right_program_path = os.path.join(self.output_path, 'best_right_sop_program.txt')
        input = generate_binary_array(input_num - 1)
        self.from_eqn_to_truth(left_infix_exprs, input, left_sub_truth_path)
        self.from_eqn_to_truth(right_infix_exprs, input, right_sub_truth_path)
        self.write_eqn_in_txt(left_infix_exprs, left_infix_exprs_path, input_num - 1)
        self.write_eqn_in_txt(right_infix_exprs, right_infix_exprs_path, input_num - 1)
        self.from_eqn_to_program(left_infix_exprs_path, best_left_program_path)
        self.from_eqn_to_program(right_infix_exprs_path, best_right_program_path)
        sop_alg_left = {
            'algorithm': None,
            'code': self.from_program_to_raw_code(best_left_program_path),
            'legalized_code': self.from_program_to_raw_code(best_left_program_path),
            'accuracy': 1.0,
            'objective': evaluate(self.from_program_to_raw_code(best_left_program_path), self.output_path)[1],
            'legalized_objective': evaluate(self.from_program_to_raw_code(best_left_program_path), self.output_path)[1],
            'other_inf': None
        }
        sop_alg_right = {
            'algorithm': None,
            'code': self.from_program_to_raw_code(best_right_program_path),
            'legalized_code': self.from_program_to_raw_code(best_right_program_path),
            'accuracy': 1.0,
            'objective': evaluate(self.from_program_to_raw_code(best_right_program_path), self.output_path)[1],
            'legalized_objective': evaluate(self.from_program_to_raw_code(best_right_program_path), self.output_path)[1],
            'other_inf': None
        }
        return best_factor_variable, left_sub_truth_path, right_sub_truth_path, sop_alg_left, sop_alg_right
    
    def shannon_fusion(self, select, cec_check_path, population_left, population_right, factor_variable, input_num, output_num, sample_times):
        print('Start Shannon fusion')
        population = []
        for _ in range(sample_times):
            try:
                alg = {
                    'algorithm': None,
                    'code': None,
                    'legalized_code': None,
                    'accuracy': None,
                    'objective': None,
                    'legalized_objective': None,
                    'other_inf': None
                }   
                selected_left_pop = select.parent_selection(population_left, 1)
                selected_right_pop = select.parent_selection(population_right, 1)

                # fusion the raw codes 
                left_program_path = os.path.join(self.output_path, 'temp_left_program_fusion.txt')
                raw_code = selected_left_pop[0]['code']
                self.correct_shannon_raw_code(raw_code, left_program_path, factor_variable, input_num, output_num, label='left')
                refresh(left_program_path, self.output_path)
                
                right_program_path = os.path.join(self.output_path, 'temp_right_program_fusion.txt')
                raw_code = selected_right_pop[0]['code']
                self.correct_shannon_raw_code(raw_code, right_program_path, factor_variable, input_num, output_num, label='right')
                refresh(right_program_path, self.output_path)
                
                append_program_path = os.path.join(self.output_path, 'temp_append_program_fusion.txt')
                self.append_program(left_program_path, right_program_path, append_program_path)
                refresh(append_program_path, self.output_path)
                raw_code = self.from_program_to_raw_code(append_program_path)
                
                # acc_list = get_accuracy(append_program_path, self.truth_file_path, self.output_path)
                # for i in range(len(acc_list)):
                #     print(f'The accuracy of {i}th expr is: {acc_list[i]}')
                accuracy = np.average(get_accuracy(append_program_path, self.truth_file_path, self.output_path))
                alg['code'] = raw_code
                alg['accuracy'] = accuracy
                _, eqn_nd = evaluate(raw_code, self.output_path)
                alg['objective'] = eqn_nd
                
                # fusion the legalized code
                left_program_path = os.path.join(self.output_path, 'temp_left_program_fusion.txt')
                legalized_code = selected_left_pop[0]['legalized_code']
                self.correct_shannon_raw_code(legalized_code, left_program_path, factor_variable, input_num, output_num, label='left')
                refresh(left_program_path, self.output_path)
                
                right_program_path = os.path.join(self.output_path, 'temp_right_program_fusion.txt')
                legalized_code = selected_right_pop[0]['legalized_code']
                self.correct_shannon_raw_code(legalized_code, right_program_path, factor_variable, input_num, output_num, label='right')
                refresh(right_program_path, self.output_path)
                
                append_program_path = os.path.join(self.output_path, 'temp_append_program_fusion.txt')
                self.append_program(left_program_path, right_program_path, append_program_path)
                refresh(append_program_path, self.output_path)
                legalized_code = self.from_program_to_raw_code(append_program_path)
                
                alg['legalized_code'] = legalized_code
                _, eqn_nd = evaluate(legalized_code, self.output_path)
                alg['legalized_objective'] = eqn_nd
                assert check_cec_for_equivalence(append_program_path, cec_check_path)
                population.append(alg)
            except Exception as e:
                print(f'Wrong in shannon_fusion. The reason is {e}')
        return population
                   
    def from_program_to_raw_code(self, program_path):
        with open(program_path, 'r') as f:
            raw_code = f.read() 
        return raw_code
                               
    def from_raw_code_to_program(self, raw_code, program_path):
        with open(program_path, 'w') as f:
            f.write(raw_code)    

    def get_output_of_eq(self, eq, input):
        """
        """
        input = input.astype(bool)
        eq = eq.replace('*', '&').replace('+', '|').replace('!', '~')
        ## define independent variables and dependent variable
        num_var = input.shape[1]
        # added by yqbai 20240418
        if 'pi' in eq:
            for i in range(num_var):
                globals()[f'pi{i}'] = input[:, i]
        elif 'x_' in eq:
            for i in range(num_var):
                globals()[f'x_{i}'] = input[:, i]
        else:
            raise ValueError('Wrong expr form. No pi or x_')
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
                   
    def from_eqn_to_truth(self, exprs, input, truth_path):
        output_str_list = []
        for expr in exprs:
            if expr == '1':
                output = ''.join(['1' for _ in range(input.shape[0])]) + '\n'
                output_str_list.append(output)
            elif expr == '0':
                output = ''.join(['0' for _ in range(input.shape[0])]) + '\n'
                output_str_list.append(output)
            else:
                output = self.get_output_of_eq(expr, input)
                output_str_list.append(''.join([str(int((out))) for out in output]) + '\n')
        with open(truth_path, 'w') as f:
            f.writelines(output_str_list)
            
    def write_eqn_in_txt(self, infix_exprs, infix_exprs_path, input_num):
        with open(infix_exprs_path, 'w') as f:
            inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
            f.writelines(inorder_row)
            outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(infix_exprs))]) + ';' + '\n'
            f.writelines(outorder_row)
            for k in range(len(infix_exprs)):
                f.write(f'F_{k}' + '=' + infix_exprs[k] + ';' + '\n')
                
    def from_eqn_to_program(self, infix_exprs_path, program_path):
        temp_aig_path = os.path.join(self.output_path, 'temp.aig')
        command = f"./abc -c 'read_eqn {infix_exprs_path}; strash; write_aiger {temp_aig_path}; read_aiger {temp_aig_path}; write_eqn {program_path}'"
        output = subprocess.check_output(command, shell=True)
        
    def append_program(self, left_program_path, right_program_path, append_program_path):
        '''
            append_program = left_program + right_program
        '''
        new_outorder_left, new_outorder_right = self.process_program_for_cmd_append(left_program_path, right_program_path)
    
        right_program_aig_path = right_program_path.replace('.txt', '.aig')
        command = f"./abc -c 'read_eqn {right_program_path}; strash; write_aiger {right_program_aig_path}'"
        output = subprocess.check_output(command, shell=True)
        command = f"./abc -c 'read_eqn {left_program_path}; strash; append {right_program_aig_path}; write_eqn {append_program_path}'"
        output = subprocess.check_output(command, shell=True)
        self.legal(append_program_path, new_outorder_left, new_outorder_right)
        
    def legal(self, append_program_path, new_outorder_left, new_outorder_right):
        with open(append_program_path, 'r') as f:
            lines = f.readlines()
        start_index = get_start_index(append_program_path)
            
        n = len(new_outorder_left)  # 这是order的长度
        for i in range(n):
            new_line = f"F{i} = {new_outorder_left[i]} + {new_outorder_right[i]};\n"
            lines.append(new_line)
        num = len(lines)
        for i in range(num):
            if 'OUTORDER' in lines[i]:
                new_line = ' '.join([f"F{i}" for i in range(n)])
                insert_line = f"OUTORDER = {new_line};\n"
                del lines[i:start_index]
                lines.insert(i, insert_line)
                break
                
        if '\n' in lines:
            lines.remove('\n')
        with open(append_program_path, 'w') as f:
            f.writelines(lines)
        temp_aig_path = os.path.join(self.output_path, 'temp.aig')
        # if optimize:
        #     command = f"./abc -c 'read_eqn {legalized_program_path}; strash; resyn2; write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {legalized_program_path}'"
        # else:
        command = f"./abc -c 'read_eqn {append_program_path}; strash; write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {append_program_path}'"
        output = subprocess.check_output(command, shell=True)
        
    def process_program_for_cmd_append(self, left_program_path, right_program_path):
        left_inorder, left_outorder = get_inorder_and_outorder(left_program_path)
        right_inorder, right_outorder = get_inorder_and_outorder(right_program_path)
        assert left_inorder == right_inorder, f"different inorder for the three programs"
        # change the output of left_outorder
        new_outorder_left = [f"left{i}" for i in range(len(left_outorder))]
        # create the mapping dict
        replacement_dict = dict(zip(left_outorder, new_outorder_left))
        with open(left_program_path, 'r') as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            for old_str, new_str in replacement_dict.items():
                line = line.replace(old_str, new_str)
            new_lines.append(line)
        with open(left_program_path, 'w') as f:
            f.writelines(new_lines)     
        # change the output of right_outorder
        new_outorder_right = right_outorder

        # new_outorder_right = [f"right{i}" for i in range(len(right_outorder))]
        # # create the mapping dict
        # replacement_dict = dict(zip(right_outorder, new_outorder_right))
        # with open(right_program_path, 'r') as f:
        #     lines = f.readlines()
        # new_lines = []
        # for line in lines:
        #     for old_str, new_str in replacement_dict.items():
        #         line = line.replace(old_str, new_str)
        #     new_lines.append(line)
        # with open(right_program_path, 'w') as f:
        #     f.writelines(new_lines)s
        return new_outorder_left, new_outorder_right
        
    def check_cec_for_equivalence(self, program_path, aig_path):
        command_cec = f"./abc -c 'read_eqn {program_path}; cec -n {aig_path}; print_stats'"
        output = subprocess.check_output(command_cec, shell=True)
        if 'Networks are equivalent' in str(output):
            return True
        else:
            return False
        
    def evaluate(self, program_path):
        command = f"./abc -c 'read_eqn {program_path}; strash; print_stats'"
        output = subprocess.check_output(command, shell=True)
        nd = int(re.search(r'and\s+=\s+(\d+)', output.decode('utf-8')).group(1))
        return nd

    def correct_shannon_raw_code(self, raw_code, program_path, factor_variable, input_num, output_num, label):     
        current_input_num = input_num - 1
        if current_input_num > 10:
            variable_list = [f"{i:02}" for i in range(input_num)]  # 格式化为两位数
            factor_variable = f"{factor_variable:02}"
        else:
            variable_list = [f"{i}" for i in range(input_num)]  # 格式化为两位数
            factor_variable = f"{factor_variable}"  
        if output_num > 10:
            output_variable_list = [f"{i:02}" for i in range(output_num)]
        else:
            output_variable_list = [f"{i}" for i in range(output_num)]
        # else:
            # variable_list = list(range(input_num))  # 小于 10 的情况直接使用数字
        unselected_variable_list = variable_list.copy()
        unselected_variable_list.remove(factor_variable)
        for j in range(len(unselected_variable_list) - 1, -1, -1):
            if current_input_num > 10:
                raw_code = raw_code.replace('pi' + f"{j:02}", 'pi'+ unselected_variable_list[j])
            else:
                raw_code = raw_code.replace('pi' + f"{j}", 'piPI'+ unselected_variable_list[j])
        raw_code = raw_code.replace('piPI', 'pi')
        with open(program_path, 'w') as f:
            f.write(raw_code)
        with open(program_path, 'r') as f:
            lines = f.readlines()
        # for i in range(len(lines)):
        #     if lines[i].startswith('INORDER'):
        #         lines[i] = 'INORDER = ' + ''.join([f'pi{k} ' for k in range(input_num)]) + ';' + '\n'
        #     if lines[i].startswith('OUTORDER'):
        #         lines[i] = lines[i].replace('po', 'F')
        start_index = get_start_index(program_path)
        del lines[:start_index]
        new_inorder_line = 'INORDER = ' + ''.join(['pi' + k + ' ' for k in variable_list]) + ';' + '\n'
        new_outorder_line = 'OUTORDER = ' + ''.join(['F' + k + ' ' for k in output_variable_list]) + ';' + '\n'
        lines.insert(0, new_outorder_line)
        lines.insert(0, new_inorder_line)
        added_lines = []
        if label == 'left':
            for output_variable in output_variable_list:
                added_line = 'F' + output_variable + '=' + 'pi' + factor_variable + ' * ' + 'po' + output_variable + ';\n'
                added_lines.append(added_line)
        elif label == 'right':
            for output_variable in output_variable_list:
                added_line = 'F' + output_variable + '=' + '!pi' + factor_variable + ' * ' + 'po' + output_variable + ';\n'
                added_lines.append(added_line)
        else:
            raise ValueError
        lines.extend(added_lines)
        with open(program_path, 'w') as f:
            f.writelines(lines)
    
    def correct_shannon_expr(self, init_expr, factor_variable, input_num):
        init_expr = init_expr.replace('x', 's')
        variable_list = list(range(input_num))
        unselected_variable_list = variable_list.copy()
        unselected_variable_list.remove(factor_variable)
        for j in range(len(unselected_variable_list) - 1, -1, -1):
            init_expr = init_expr.replace(f's_{j}', f'x_{unselected_variable_list[j]}')
        return init_expr
    
    def sop_factor(self, x, y, factor_variable):
        def convert_logic_string(s):
            s = s.replace("~", "!")
            s = s.replace("&", "*")
            s = s.replace("|", "+")
            return s
        init_expr_list = []
        optimized_expr_list = []
        sub_truth_xs, sub_truth_ys =  self.get_sub_truth(x, y, factor_variable)
        for sub_truth_x, sub_truth_y in zip(sub_truth_xs, sub_truth_ys):
            init_expr = self.get_expr_from_truth(sub_truth_x, sub_truth_y)
            # init_expr = init_expr.replace('x', 's')
            # input_num = int(math.log2(len(x)))
            # variable_list = list(range(input_num))
            # unselected_variable_list = variable_list.copy()
            # unselected_variable_list.remove(factor_variable)
            # for j in range(len(unselected_variable_list) - 1, -1, -1):
            #     init_expr = init_expr.replace(f's_{j}', f'x_{unselected_variable_list[j]}')
            # algebra = boolean.BooleanAlgebra()
            # # first optimize the eqn 
            # optimized_expr = algebra.parse(init_expr, simplify=True)
            # optimized_expr = convert_logic_string(str(optimized_expr)) 
            init_expr_list.append(init_expr)
            # optimized_expr_list.append(optimized_expr)
        # init_expr = (f'x_{factor_variable} ' + '*' + '(' + init_expr_list[0] + ')', f'!x_{factor_variable} ' + '*' + '(' + init_expr_list[1] + ')') 
        return init_expr_list[0], init_expr_list[1]

    def boolean_optimize(self, infix_expr):
        def convert_logic_string(s):
            s = s.replace("~", "!")
            s = s.replace("&", "*")
            s = s.replace("|", "+")
            return s
        algebra = boolean.BooleanAlgebra()
        # first optimize the eqn 
        optimized_expr = algebra.parse(infix_expr, simplify=True)
        optimized_expr = convert_logic_string(str(optimized_expr)) 
        return optimized_expr   
      
    def get_sub_truth(self, x, y, factor_variable):
        # input_num = int(math.log2(len(x)))
        # variable_list = list(range(input_num))
        # unselected_variable_list = [variable for variable in variable_list if str(variable) not in factor_variable_list and ('!'+str(variable)) not in factor_variable_list]
        truth_left_x = []
        truth_left_y = []
        truth_right_x = []
        truth_right_y = []
        input_num = int(math.log2(len(x)))
        # print('factor_variable', factor_variable)
        variable_list = list(range(input_num))
        unselected_variable_list = variable_list.copy()
        unselected_variable_list.remove(factor_variable)
        for i in range(len(x)):
            if x[i][factor_variable] == 1:
                truth_left_x.append(x[i][unselected_variable_list])
                truth_left_y.append(y[i])
            else:
                truth_right_x.append(x[i][unselected_variable_list])
                truth_right_y.append(y[i])

        return [np.array(truth_left_x), np.array(truth_right_x)], [np.array(truth_left_y), np.array(truth_right_y)]  
    
    def get_expr_from_truth(self, truth_x, truth_y):
        def get_truth_str(truth_x, truth_y):
            return ''.join([str(y) for y in truth_y])
        truth_str = get_truth_str(truth_x, truth_y)
        if truth_str.count('1') == len(truth_str):
            expr = '1'
        elif truth_str.count('0') == len(truth_str):
            expr = '0'
        else:
            truth_file = os.path.join(self.output_path, 'temp_truth.truth')
            eqn_file = os.path.join(self.output_path, 'temp_eqn.txt')
            with open(truth_file, 'w') as f:
                f.write(truth_str)
            command_truth = f"./abc -c 'read_truth -xf {truth_file}; collapse; sop; write_eqn {eqn_file}'"
            output = subprocess.check_output(command_truth, shell=True)
            with open(eqn_file, 'r') as f:
                lines = f.readlines()
            #     start_index = next(i for i, line in enumerate(lines) if line.startswith('F0') or line.startswith('F_0'))
            start_index = get_start_index(eqn_file)
            expr = lines[start_index].split("=")[1].strip().replace(';', '')
            expr = re.sub(r'[a-w]', lambda x: 'x_' + str(ord(x.group()) - ord('a')), expr)
        return expr
        
        # print(output)
        # with open(eqn_file, 'r') as f:
        #     lines = f.readlines()
        #     start_index = next(i for i, line in enumerate(lines) if line.startswith('F0') or line.startswith('F_0'))
        # line = re.sub(r'[a-w]', lambda x: 'x_' + str(ord(x.group()) - ord('a')), lines[start_index])
        # length = line.count('*') + line.count('!') + line.count('+') + line.count('x') 
    def write_expr_in_txt(self, txt_dir, merge_init_infix_exprs, simplification_merge_init_exprs, symbol, input_num):
        '''
            将原始表达式和化简表达式写入txt_dir
        '''
        if symbol == 'init':
            best_txt_file_path = os.path.join(txt_dir, 'best_init_expr.txt')
            best_simplification_txt_file_path = os.path.join(txt_dir, 'best_init_simplification_expr.txt')
        elif symbol == 'optimized':
            best_txt_file_path = os.path.join(txt_dir, 'best_optimzied_expr.txt')
            best_simplification_txt_file_path = os.path.join(txt_dir, 'best_optimzied_simplification_expr.txt')
        with open(best_txt_file_path, 'w') as f:
            inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
            f.writelines(inorder_row)
            outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(merge_init_infix_exprs))]) + ';' + '\n'
            f.writelines(outorder_row)
            for k in range(len(merge_init_infix_exprs)):
                f.write(f'F_{k}' + '=' + merge_init_infix_exprs[k] + ';' + '\n')
            command_truth = f"./abc -c 'read_eqn {best_txt_file_path}; strash; print_stats'"
            output = subprocess.check_output(command_truth, shell=True)
        with open(best_simplification_txt_file_path, 'w') as f:
            inorder_row = 'INORDER = ' + ''.join([f'x_{k} ' for k in range(input_num)]) + ';' + '\n'
            f.writelines(inorder_row)
            outorder_row = 'OUTORDER = ' + ''.join([f'F_{k} ' for k in range(len(simplification_merge_init_exprs))]) + ';' + '\n'
            f.writelines(outorder_row)
            for k in range(len(simplification_merge_init_exprs)):
                f.write(f'F_{k}' + '=' + simplification_merge_init_exprs[k] + ';' + '\n')
            command_truth = f"./abc -c 'read_eqn {best_txt_file_path}; strash; print_stats'"
            output = subprocess.check_output(command_truth, shell=True)
    
    def get_nd_from_exprs_for_sop_factor(self, init_merge_infix_exprs, simplification_merge_infix_exprs, input_num, file_name):
        # temp_txt_dir_path = './sop_factor'
        # if not os.path.exists(temp_txt_dir_path):
        #     os.makedirs(temp_txt_dir_path)   
        temp_txt_file_path = os.path.join(self.output_path, f'./temp_sop_{file_name}_init.txt')
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
        temp_txt_file_path = os.path.join(self.output_path, f'./temp_sop_{file_name}_simplification.txt')
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
           
    def get_nd_from_exprs(self, init_merge_infix_exprs, simplification_merge_infix_exprs, input_num):
        temp_txt_file_path = os.path.join(self.output_path, f'./temp_sop_{self.file_name}_init.txt')
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
        temp_txt_file_path = os.path.join(self.output_path,  f'./temp_sop_{self.file_name}_simplification.txt')
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
    
    def read_val(self, file):
        '''
        Args:
            file(str): path of file of truth table
        Return:
            inputs: inputs
            labels: outputs
        '''
        def _generate_binary_array(labels, truth_flip=True): #对于n＜16
            result = []
            length = len(labels)
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

if __name__ == "__main__":
    iwls2022_truth_file_path = './benchmark/iwls2022/all'
    csv_save_path = './iwls2022_all_sop_factor.csv'
    with open(csv_save_path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['file_name', 'input', 'output', 'init_sop_nd', 'factor_variables', 'factor_init_nds', 'best_factor_init_nd', 'improvement(%)'])
    for file in os.listdir(iwls2022_truth_file_path):
        if file.endswith('.truth'):
            print(file)
            file_name = file.split('.')[0]
            file_path = os.path.join(iwls2022_truth_file_path, file)
            sop_factor = Sop_factor(file_path, file_name)
            init_sop_nd, factor_variables, factor_init_nds, best_factor_init_nd, improvment, input_num, output_num = sop_factor.shannon_decomposition()
            with open(csv_save_path, 'a') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([file_name, input_num, output_num, init_sop_nd, factor_variables, factor_init_nds, best_factor_init_nd, improvment])
        