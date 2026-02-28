from legalization import legalization, get_accuracy
from utils_abc import from_program_to_raw_code, read_val, from_program_to_aig, from_raw_code_to_program, evaluate
from motivation_test.interface_LLM import InterfaceLLM
import os
import argparse
import math
import subprocess
import re
import json
import numpy as np
import random
from datetime import datetime
import shutil
from torch.utils.tensorboard import SummaryWriter
def create_output_path(truth_file_path):
    now = datetime.now()
    day_folder = now.strftime("%Y-%m-%d")
    time_folder = now.strftime("%H-%M-%S")
    base_path = './eoh/src/eoh/problems/optimization/aig/legalization/abc_append/outputs'
    full_path = os.path.join(base_path, day_folder, time_folder)
    os.makedirs(full_path, exist_ok=True)
    truth_file_json = {'truth_file_path': truth_file_path}
    with open(os.path.join(full_path, 'config.json'), 'w') as f:
        json.dump(truth_file_json, f, indent=4)
    return full_path

def from_truth_to_program(truth_file_path, program_path, temp_aig_path, optimize):
    if optimize == True:
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; resyn2; \
        write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
    else:
        command = f"./abc -c 'read_truth -xf {truth_file_path}; collapse; sop; strash; \
        write_aiger {temp_aig_path}; read {temp_aig_path}; write_eqn {program_path}'"
    output = subprocess.check_output(command, shell=True)

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

def save_config(args, txt_dir):
    args_dict = vars(args)

    # Write the arguments to a config.json file
    config_path = os.path.join(txt_dir, 'config.json')
    with open(config_path, 'w') as config_file:
        json.dump(args_dict, config_file)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser('legalization motivation test')
    parser.add_argument('--truth_file_path', default='./benchmark/iwls2022/all/ex00.truth', type=str)
    parser.add_argument('--num', default=1000, type=int)
    parser.add_argument('--threshold', default=0.05, type=float)
    parser.add_argument('--before_legalized_optimize', action='store_true')
    parser.add_argument('--legalized_optimize', action='store_true')
    args = parser.parse_args()
    txt_dir = create_output_path(args.truth_file_path)
    print(txt_dir)
    print('before_legalized_optimize', args.before_legalized_optimize)
    print('legalized_optimize', args.legalized_optimize)
    save_config(args, txt_dir)
    # initial
    writer = SummaryWriter(os.path.join(txt_dir, 'runs'))
    program_path = os.path.join(txt_dir, 'initial_program.txt')
    temp_aig_path = os.path.join(txt_dir, 'temp_aig.aig')
    cec_check_path = os.path.join(txt_dir, 'for_cec_check.aig')
    print('The truth file is', re.search(r'ex\d+', args.truth_file_path).group())
    inputs, labels = read_val(args.truth_file_path)
    input_number = int(math.log2(len(inputs[0])))
    output_number = int(len(labels))
    print(f'The input number is {input_number}, output number is {output_number}')
    # if args.num > 2 ** input_number:
    #     num = args.num
    # else:
    #     num = 2 ** input_number
    print(f'The eposides are {args.num}')
    
    from_truth_to_program(args.truth_file_path, program_path, temp_aig_path, optimize=False)
    example_program = from_program_to_raw_code(program_path)
    _, sop_eqn_nd = evaluate(example_program, txt_dir)
    print(f'The sop eqn node number is {sop_eqn_nd}')
    from_truth_to_program(args.truth_file_path, program_path, temp_aig_path, optimize=True)
    example_program = from_program_to_raw_code(program_path)
    _, resyn2_eqn_nd = evaluate(example_program, txt_dir)
    print(f'The sop&resyn2 node number is {resyn2_eqn_nd}')
    from_program_to_aig(program_path, cec_check_path)
    writer.add_scalar('The initial nd', sop_eqn_nd, 0)
    # writer.add_scalar('The initial nd', resyn2_nd, 1)
    # random.seed(42)
    successful_num = 0
    best_nd = sop_eqn_nd
    best_optimized_nd = resyn2_eqn_nd
    for i in range(args.num):
        # # use LLM to get response and legalization results
        # interface_llm = InterfaceLLM(
        #     api_endpoint="provide_your_endpoint_here", 
        #     api_key="provide_your_key_here",
        #     model_LLM="gpt-3.5-turbo",
        #     llm_use_local=False, 
        #     llm_local_url=None, 
        #     debug_mode=False)
        # inputs, labels = read_val(args.truth_file_path)
        # program_inputs = [f'pi{i}' for i in range(int(math.log2(len(labels[0]))))]
        # program_outputs = [f'po{i}' for i in range(len(labels))]
        # prompt_content = f"Given {len(program_inputs)} inputs {' '.join(program_inputs)} and \
        #     {len(program_outputs)} inputs {' '.join(program_outputs)}, please randomly generate \
        #     a program which has the similar form but different structure to the following program. \n" + f"{example_program}\n" \
        #     + f"The generated program should be simpler than the given program. Just output the program including the INORDER and OUTORDER. No additional explanations."
        # response = interface_llm.get_response(prompt_content)
        # before_legalized_code = re.findall(r"^.*=.*$", response, flags=re.MULTILINE)
        # before_legalized_code = '\n'.join([raw for raw in before_legalized_code]) 
        
        # randomly generate a truth table and the corresponding program
        sample_list = [''.join(list(map(str, label.tolist()))) for label in labels]
        before_legalized_random_str = modify_list_elements(sample_list, args.threshold)
        # before_legalized_random_str = [''.join([random.choice(['0', '1']) for _ in range(2 ** input_number)]) + "\n" for _ in range(output_number)]
        before_legalized_truth_path = os.path.join(txt_dir, 'before_legalized_truth.truth')
        with open(before_legalized_truth_path, 'w') as f:
            f.writelines(before_legalized_random_str)
        before_legalized_program_path = os.path.join(txt_dir, 'before_legalized_program.txt')
        from_truth_to_program(before_legalized_truth_path, before_legalized_program_path, temp_aig_path, optimize=args.before_legalized_optimize)
        before_legalized_code = from_program_to_raw_code(before_legalized_program_path)
        _, eqn_nd = evaluate(before_legalized_code, txt_dir)
        print(f'The before legalized eqn node number is {eqn_nd}')
        writer.add_scalar('The before legalized eqn nd', eqn_nd, i)
        from_raw_code_to_program(before_legalized_code, before_legalized_program_path)
        # print('The before legalized code is: \n', before_legalized_code)
        acc_list = get_accuracy(before_legalized_program_path, args.truth_file_path, txt_dir)
        if acc_list == None:
            break
        for k in range(len(acc_list)):
            print(f'The {k}th expr accuracy is: {acc_list[k]}')
            writer.add_scalar(f'The {k}th expr accuracy', acc_list[k], i)
        average_acc = np.mean(acc_list)
        if average_acc == 1:
            print('The acc is 100%, no need for legalization')
            writer.add_scalar('The complementary_nd', 0, i)
            writer.add_scalar('The legalized_nd', eqn_nd, i) 
        else:  
            legalized_code, complementary_nd = legalization(before_legalized_program_path, args.truth_file_path, txt_dir, cec_check_path, optimize=args.legalized_optimize, complementary_nd=True)
            writer.add_scalar('The complementary_nd', complementary_nd, i)
            # print('The legalized code is', legalized_code)
            # evaluate the legalized codes
            legalized_program_path = os.path.join(txt_dir, 'legalized_program.txt')
            from_raw_code_to_program(legalized_code, legalized_program_path)
            # don't optimize the legalized eqn
            program_nd, eqn_nd, eqn_optimized_nd= evaluate(legalized_code, txt_dir, optimize_operator='resyn2')
            # optimize the legalized eqn
            # boolopt_program_nd, boolopt_eqn_nd, boolopt_eqn_optimized_nd = evaluate(legalized_code, txt_dir, bool_optimize=True)
            print(f'The legalized eqn node number is {eqn_nd}')
            print(f'The legalized resyn2 optimized eqn node number is {eqn_optimized_nd}')
            writer.add_scalar('The legalized eqn nd', eqn_nd, i)
            writer.add_scalar('The legalized resyn2 optimized eqn nd', eqn_optimized_nd, i)
            if eqn_nd < int(sop_eqn_nd):
                successful_num += 1
                if eqn_nd < best_nd:
                    best_nd = eqn_nd
                    best_optimized_nd = eqn_optimized_nd
                    best_program_path = os.path.join(txt_dir, 'best_legalized_program.txt')
                    shutil.copy(legalized_program_path, best_program_path)
    if successful_num == 0:
        print(f"Can't find a smaller program after {args.num} exploritions! The best node number is {best_nd}")
    else:
        improvement = (sop_eqn_nd - best_nd)/sop_eqn_nd * 100
        print(f'successfully find better programs! The finding time is {successful_num}. The best node number is {best_nd}. The best optimized node number is {best_optimized_nd}.The improvement is {improvement}%')
