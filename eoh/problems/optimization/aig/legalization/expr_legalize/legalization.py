'''
input: the unlegal txt expr file; the truth file; the file_dir of the legal txt expr file
output: the legal txt expr file
    step1: read the txt expr file and the truth file
    step2: calculate the wrong bits for every output
    step3: correct every wrong expr and return the emerged exprs
'''
import math
import os
import csv
import numpy as np
import sys
import subprocess
import argparse
import re 
from .utils_exprs import read_val, write_expr_in_txt, convert_expr_for_abc, check_cec_for_equivalence, \
get_length_from_txt, get_expr_from_txt, get_output_of_eq,\
get_nd_from_exprs, get_file_name_and_path, get_supplementary_expr, boolean_optimize,\
get_sharing_from_txt, convert_synopsys_to_aig_eqn, convert_aig_eqn_to_synopsys, from_txt_to_raw_code

def legalization(program_path, truth_file_path, txt_dir, cec_check_path):
    inputs, labels = read_val(truth_file_path)
    input_num = int(math.log2(len(labels[0])))
    output_num = len(labels)
    expr_file_path = os.path.join(txt_dir, 'temp_before_legalized_synopsys_eqn.txt')
    convert_aig_eqn_to_synopsys(program_path, expr_file_path)
    exprs = get_expr_from_txt(expr_file_path)
    exprs_legal = []
    simplification_exprs_legal = []
    for i, (expr, input, label) in enumerate(zip(exprs, inputs, labels)):
        print(f'{output_num} outputs in total \n')
        print(f'the {i}th expr is: {expr} \n')
        expr_legal = legal(expr, input, label)
        output_legal = get_output_of_eq(expr_legal, input)
        assert ((output_legal == label) == True).all()
        print(f'the {i}th legal expr is: {expr_legal} \n')
        simplification_expr_legal = boolean_optimize(expr_legal)
        expr_legal = convert_expr_for_abc(expr_legal)
        simplification_expr_legal = convert_expr_for_abc(simplification_expr_legal)
        simplification_exprs_legal.append(simplification_expr_legal)
        exprs_legal.append(expr_legal)
    expr_legal_path, simplification_expr_legal_path = write_expr_in_txt(txt_dir, exprs_legal, simplification_exprs_legal, 'init', input_num)
    assert check_cec_for_equivalence(simplification_expr_legal_path, cec_check_path)
    simplification_aig_eqn_legal_path = os.path.join(txt_dir, 'temp_legalized_program.txt')
    convert_synopsys_to_aig_eqn(simplification_expr_legal_path, simplification_aig_eqn_legal_path)
    legalized_raw_code = from_txt_to_raw_code(simplification_aig_eqn_legal_path)
    return legalized_raw_code

def legal(expr, input, label):
    prediction = get_output_of_eq(expr, input)
    # find the indicies with prediction=1 and label=0
    indices_prediction_1_label_0 = np.where((prediction == True) & (label == False))[0]
    inputs_prediction_1_label_0 = input[indices_prediction_1_label_0]
    supplementary_exprs_prediction_1_label_0 = get_supplementary_expr(inputs_prediction_1_label_0, control='1->0')
    # find the indicies with prediction=0 and label=1
    indices_prediction_0_label_1 = np.where((prediction == False) & (label == True))[0]
    inputs_prediction_0_label_1 = input[indices_prediction_0_label_1]
    supplementary_exprs_prediction_0_label_1 = get_supplementary_expr(inputs_prediction_0_label_1, control='0->1')
    for supplementary_expr in supplementary_exprs_prediction_1_label_0:
        expr = '(' + expr + ')' + '*' + supplementary_expr
        # expr = boolean_optimize(expr)
    for supplementary_expr in supplementary_exprs_prediction_0_label_1:
        expr = '(' + expr + ')' + '+' + supplementary_expr
        # expr = boolean_optimize(expr)
    return expr

def get_accuracy(program_path, truth_file_path, txt_dir):
    try:
        inputs, labels = read_val(truth_file_path)
        output_num = len(labels)
        expr_file_path = os.path.join(txt_dir, 'temp_for_accuracy_synopsys_eqn.txt')
        convert_aig_eqn_to_synopsys(program_path, expr_file_path)
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
# def check_if_exists(word, words_list):
#     return any(word in other_word for other_word in words_list if other_word != word)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--expr_file_path', type=str, default='/yqbai/boolfuncgen/main/final_baseline_exprs/iwls2022_small_truth_ex97_10_num_run_100_max_len_baseline_DT_beam_sampling_baseline_DT.txt')
    parser.add_argument('--truth_file_path', type=str, default='/yqbai/boolfuncgen/benchmark/final_truth/ex97/ex97.truth')
    args = parser.parse_args()
    txt_dir = '/yqbai/boolfuncgen/txt_for_conversion'
    legalization(args.expr_file_path, args.truth_file_path, txt_dir)