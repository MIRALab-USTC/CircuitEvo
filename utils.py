# hydra folder path
import os
from datetime import datetime
import subprocess
import numpy as np
import math
import json
def create_output_path():
    now = datetime.now()
    day_folder = now.strftime("%Y-%m-%d")
    time_folder = now.strftime("%H-%M-%S")
    base_path = './outputs'
    full_path = os.path.join(base_path, day_folder, time_folder)
    os.makedirs(full_path, exist_ok=True)
    return full_path

def save_config(args, txt_dir):
    args_dict = vars(args)

    # Write the arguments to a config.json file
    config_path = os.path.join(txt_dir, 'config.json')
    with open(config_path, 'w') as config_file:
        json.dump(args_dict, config_file)
        
def check_cec_for_equivalence(txt_path, aig_path):
    command_cec = f"./abc -c 'read_eqn {txt_path}; cec -n {aig_path}; print_stats'"
    output = subprocess.check_output(command_cec, shell=True)
    if 'Networks are equivalent' in str(output):
        return True
    else:
        return False

def get_inout(file):
    '''
    Args:
        file(str): path of file of truth table
    Return:
        inputs_list: X
        labels_list: Y
    '''
    labels = []
    with open(file) as f:
        line = f.readline()
        while line:
            label = np.array([int(x) for x in line if x>='0' and x<='9'])
            labels.append(label)
            line = f.readline()
        input_number = int(math.log2(len(labels[0])))
        output_number = len(labels)
    return input_number, output_number
