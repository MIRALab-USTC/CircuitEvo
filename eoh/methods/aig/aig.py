import numpy as np
import json
import random
import time
import re
import os 
import subprocess
from .aig_interface_EC import InterfaceEC
from .sop_factor import sop_factor
from ...llm.api_general import InterfaceAPI
# main class for eoh
class AIG:

    # initilization
    def __init__(self, paras, problem, select, manage, **kwargs):

        self.prob = problem
        self.select = select
        self.manage = manage
        # reflection
        try:
            self.reflection = problem.reflection
        except:
            self.reflection = None
        
        # LLM settings
        self.use_local_llm = paras.llm_use_local
        self.llm_local_url = paras.llm_local_url
        self.api_endpoint = paras.llm_api_endpoint  # currently only API2D + GPT
        self.api_key = paras.llm_api_key
        self.llm_model = paras.llm_model

        # ------------------ RZ: use local LLM ------------------
        # self.use_local_llm = kwargs.get('use_local_llm', False)
        # assert isinstance(self.use_local_llm, bool)
        # if self.use_local_llm:
        #     assert 'url' in kwargs, 'The keyword "url" should be provided when use_local_llm is True.'
        #     assert isinstance(kwargs.get('url'), str)
        #     self.url = kwargs.get('url')
        # -------------------------------------------------------

        # Experimental settings       
        self.pop_size = paras.ec_pop_size  # popopulation size, i.e., the number of algorithms in population
        self.n_pop = paras.ec_n_pop  # number of populations

        self.operators = paras.ec_operators
        self.operator_weights = paras.ec_operator_weights
        if paras.ec_m > self.pop_size or paras.ec_m == 1:
            print("m should not be larger than pop size or smaller than 2, adjust it to m=2")
            paras.ec_m = 2
        self.m = paras.ec_m

        self.debug_mode = paras.exp_debug_mode  # if debug
        self.ndelay = 1  # default

        self.use_seed = paras.exp_use_seed
        self.seed_path = paras.exp_seed_path
        self.load_pop = paras.exp_use_continue
        self.load_pop_path = paras.exp_continue_path
        self.load_pop_id = paras.exp_continue_id

        self.output_path = paras.exp_output_path

        self.exp_n_proc = paras.exp_n_proc
        
        self.timeout = paras.eva_timeout

        self.use_numba = paras.eva_numba_decorator
        
        # AIG settings
        self.truth_file_path = paras.truth_file_path
        self.input_number = int(paras.input_number)
        self.output_number = int(paras.output_number)
        self.writer = paras.writer
        self.use_fx = paras.use_fx
        self.local_search = paras.local_search
        self.random_generated = paras.random_generated
        self.sample_num = paras.sample_num
        self.shannon_decomposition = paras.shannon_decomposition
        self.prune = paras.prune
        self.reflect = paras.reflect
        self.LLM_generation_initial = paras.LLM_generation_initial
        self.legalized_parent = paras.legalized_parent
        print("- EoH parameters loaded -")
        print(f"local_search: {self.local_search}")
        print(f"shannon_decomposition: {self.shannon_decomposition}")
        print(f"legalized_parent: {self.legalized_parent}")

        # Set a random seed
        random.seed(2024)

    # add new individual to population
    def add2pop(self, population, offspring):
        for off in offspring:
            for ind in population:
                if ind['objective'] == off['objective']:
                    if (self.debug_mode):
                        print("duplicated result, retrying ... ")
            population.append(off)

    def pipeline(self):
        print("- Evolution Start -")
        if self.shannon_decomposition:
            self.run_decomposition()
        else:
            self.run_single()
            
    # run eoh 
    def run_decomposition(self):
        # 在run_single基础上修改，将原来的一个all列表改为三个列表，分别存储left，right，all
        # 1. 根据sop结果选择分解变量，并获得sub_truth_i和sub_truth_!i的真实.truth文件
        # 2. 对每个truth应用现有演化流程，每个operator得到n个left，n个right
        # 3. 根据概率组合两边的n个最优progarm（sample 2n次)，筛选得到最优的n个all并存储
        # 4. 最终最优结果和原始分解+sop比较，选择最小的作为最终输出program  
        truth_file_name = re.search(r'(ex\d+)', self.truth_file_path).group(1)
        output_path = os.path.join(self.output_path, 'sop_factor')
        os.makedirs(output_path, exist_ok=True)
        factor_agent = sop_factor.Sop_factor(self.truth_file_path, truth_file_name, output_path)
        factor_variable, left_sub_truth_path, right_sub_truth_path, left_sop_pop, right_sop_pop = factor_agent.shannon_decomposition()

        time_start = time.time()

        # interface for evaluation
        interface_prob = self.prob
        # generate initial output folder and aig path for cec check
        interface_prob.generate_output_folder(self.output_path, 'legalization')
        
        cec_check_all_path = interface_prob.generate_cecaig_from_truth(self.truth_file_path, label='all')
        cec_check_left_path = interface_prob.generate_cecaig_from_raw_code(left_sop_pop['legalized_code'], output_path, label='left')
        cec_check_right_path = interface_prob.generate_cecaig_from_raw_code(right_sop_pop['legalized_code'], output_path, label='right')

        _, threshold_nd = interface_prob.run_baselines(self.output_path, self.writer, self.truth_file_path)
        # baseline_pops_left = interface_prob.run_baselines(self.output_path, self.writer, left_sub_truth_path)
        # baseline_pops_right = interface_prob.run_baselines(self.output_path, self.writer, right_sub_truth_path)
        # baseline_pops_left = [left_sop_pop]
        # baseline_pops_right = [right_sop_pop]      
        # interface for ec operators
        constraints = self.get_output_constraints()
        interface_ec_left = InterfaceEC(left_sub_truth_path, self.writer, self.output_path, self.input_number, self.output_number, cec_check_left_path, self.use_fx, self.local_search, self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model, self.use_local_llm, self.llm_local_url,
                                self.debug_mode, interface_prob, self.legalized_parent, constraints, select=self.select,n_p=self.exp_n_proc,
                                timeout = self.timeout, use_numba=self.use_numba
                                )
        interface_ec_right = InterfaceEC(right_sub_truth_path, self.writer, self.output_path, self.input_number, self.output_number, cec_check_right_path, self.use_fx, self.local_search, self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model, self.use_local_llm, self.llm_local_url,
                                self.debug_mode, interface_prob, self.legalized_parent, constraints, select=self.select,n_p=self.exp_n_proc,
                                timeout = self.timeout, use_numba=self.use_numba
                                )
        # run baselines operators
        random_pops_left = []
        random_pops_right = []
        if self.random_generated:
            # left
            # random generate 1000, threshold = 0.01, set optimize as False, i.e., only use the sop
            pops = interface_prob.run_random_generate(self.output_path, cec_check_left_path, self.prune, sample_num=self.sample_num, truth_file_path=left_sub_truth_path, threshold=0.01, threshold_nd=threshold_nd, optimize=False)
            random_pops_left.extend(pops)
            # random generate 1000, threshold = 0.05, set optimize as False, i.e., only use the sop
            pops = interface_prob.run_random_generate(self.output_path, cec_check_left_path, self.prune, sample_num=self.sample_num, truth_file_path=left_sub_truth_path, threshold=0.05, threshold_nd=threshold_nd, optimize=False)
            random_pops_left.extend(pops)

            # right
            # random generate 1000, threshold = 0.01, set optimize as False, i.e., only use the sop
            pops = interface_prob.run_random_generate(self.output_path, cec_check_right_path, self.prune, sample_num=self.sample_num, truth_file_path=right_sub_truth_path, threshold=0.01, threshold_nd=threshold_nd, optimize=False)
            random_pops_right.extend(pops)
            # random generate 1000, threshold = 0.05, set optimize as False, i.e., only use the sop
            pops = interface_prob.run_random_generate(self.output_path, cec_check_right_path, self.prune, sample_num=self.sample_num, truth_file_path=right_sub_truth_path, threshold=0.05, threshold_nd=threshold_nd, optimize=False)
            random_pops_right.extend(pops)
        # initialization
        # population_left = []
        # population_right = []
        if self.use_seed: # the initial pop is provided by user
            with open(self.seed_path) as file:
                data = json.load(file)
            # population = interface_ec.population_generation_seed(data,self.exp_n_proc)
            filename = self.output_path + "/results/pops/population_generation_0.json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)
            n_start = 0
        else:
            if self.load_pop:  # load population from files
                print("load initial population from " + self.load_pop_path)
                with open(self.load_pop_path) as file:
                    data = json.load(file)
                for individual in data:
                    population.append(individual)
                print("initial population has been loaded!")
                n_start = self.load_pop_id
            else:  # create new population
                print("creating initial population:")
                if self.LLM_generation_initial:
                    population_left = interface_ec_left.population_generation_llm()
                    population_right = interface_ec_right.population_generation_llm()
                else:
                    population_left = [left_sop_pop]
                    population_right = [right_sop_pop] 
                population_left.extend(random_pops_left)
                print(population_left)     
                population_left = self.manage.population_management(population_left, self.pop_size, self.local_search)
                population_right.extend(random_pops_right)
                population_right = self.manage.population_management(population_right, self.pop_size, self.local_search)
                population = factor_agent.shannon_fusion(self.select, cec_check_all_path, population_left, population_right, factor_variable, self.input_number, self.output_number, sample_times = 2*self.pop_size)
                population = self.manage.population_management(population, self.pop_size, self.local_search)

                print(f"Pop initial: ")
                for i, off in enumerate(population):
                    print(" Acc: ", off['accuracy'], end="|")
                    print(" Obj: ", off['objective'], end="|")
                    print(" Legalized_Obj: ", off['legalized_objective'], end="|\n")
                for i, off in enumerate(population):
                    self.writer.add_scalar("The initial pop's node number", off['legalized_objective'], i)
                self.writer.add_scalar("The best pop's node number", self.manage.best_population(population)['legalized_objective'], 0)
                print()
                print("initial population has been created!")
                # Save population to a file
                filename = self.output_path + "/results/pops/population_generation_0.json"
                with open(filename, 'w') as f:
                    json.dump(population, f, indent=5)
                n_start = 0

        # main loop
        n_op = len(self.operators)

        for pop in range(n_start, self.n_pop):  
            print('*****************************************************************\n')
            print(f" Population: [{pop + 1} / {self.n_pop}] ", end="\n") 
            #print(f" [{na + 1} / {self.pop_size}] ", end="|")         
            for i in range(n_op):
                op = self.operators[i]
                print("#############################################################")
                print(f" Operator: {op}, [{i + 1} / {n_op}] ", end="\n") 
                op_w = self.operator_weights[i]
                if (np.random.rand() < op_w): 
                    parents, offsprings_left = interface_ec_left.get_algorithm(population_left, op, pop)
                    self.add2pop(population_left, offsprings_left)  # Check duplication, and add the new offspring
                    parents, offsprings_right = interface_ec_right.get_algorithm(population_right, op, pop)
                    self.add2pop(population_right, offsprings_right)  # Check duplication, and add the new offspring
                    offsprings = factor_agent.shannon_fusion(self.select, cec_check_all_path, offsprings_left, offsprings_right, factor_variable, self.input_number, self.output_number, sample_times = 2*self.pop_size)
                    offsprings = self.manage.population_management(offsprings, self.pop_size, self.local_search)
                # reflection
                if self.reflect:
                    output_folder = os.path.join(self.output_path, 'reflection')
                    os.makedirs(output_folder, exist_ok=True)
                    for j in range(len(offsprings)):
                        self.reflection.set_paras(offsprings[j], self.api_key, self.api_endpoint, self.llm_model, self.truth_file_path, output_folder)    
                        offsprings[j] = self.reflection.run()
                print(f" OP: {op}, [{i + 1} / {n_op}] ", end="\n") 
                for off in offsprings:
                    print(" Acc: ", off['accuracy'], end="|")
                    print(" Obj: ", off['objective'], end="|")
                    print(" Legalized_Obj: ", off['legalized_objective'], end="|\n")
                self.add2pop(population, offsprings)  # Check duplication, and add the new offspring
                # populatin management
                size_act = min(len(population), self.pop_size)
                population = self.manage.population_management(population, size_act, self.local_search)
                print()
                print("#############################################################")
                # if is_add:
                #     data = {}
                #     for i in range(len(parents)):
                #         data[f"parent{i + 1}"] = parents[i]
                #     data["offspring"] = offspring
                #     with open(self.output_path + "/results/history/pop_" + str(pop + 1) + "_" + str(
                #             na) + "_" + op + ".json", "w") as file:
                #         json.dump(data, file, indent=5)



            # Save population to a file
            filename = self.output_path + "/results/pops/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)

            # Save the best one to a file
            filename = self.output_path + "/results/pops_best/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population[0], f, indent=5)


            print(f"--- {pop + 1} of {self.n_pop} populations finished. Time Cost:  {((time.time()-time_start)/60):.1f} m")
            print(f"completion_tokens: {InterfaceAPI.completion_tokens}, prompt_tokens: {InterfaceAPI.prompt_tokens}")
            # print("Pop Objs: ", end=" ")
            # for i in range(len(population)):
            #     print(str(population[i]['objective']) + " ", end="")
            
            print("Pop Objs: ", end="\n")
            for i in range(len(population)):
                print(" Acc: ", population[i]['accuracy'], end="|")
                print(" Obj: ", population[i]['objective'], end="|")
                print(" Legalized_Obj: ", population[i]['legalized_objective'], end="|\n")
            self.writer.add_scalar("The best pop's node number", self.manage.best_population(population)['legalized_objective'], pop)
            print()
            print('*****************************************************************\n')    
                      
    def run_single(self):
        time_start = time.time()

        # interface for large language model (llm)
        # interface_llm = PromptLLMs(self.api_endpoint,self.api_key,self.llm_model,self.debug_mode)

        # interface for evaluation
        interface_prob = self.prob

        # generate initial output folder and aig path for cec check
        interface_prob.generate_output_folder(self.output_path, 'legalization')
        cec_check_all_path = interface_prob.generate_cecaig_from_truth(self.truth_file_path, label='all')
        # interface for ec operators
        constraints = self.get_output_constraints()
        interface_ec = InterfaceEC(self.truth_file_path, self.writer, self.output_path, self.input_number, self.output_number, cec_check_all_path, self.use_fx, self.local_search, self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model, self.use_local_llm, self.llm_local_url,
                                   self.debug_mode, interface_prob, self.legalized_parent, constraints, select=self.select,n_p=self.exp_n_proc,
                                   timeout = self.timeout, use_numba=self.use_numba
                                   )
        # run baselines operators
        _, threshold_nd = interface_prob.run_baselines(self.output_path, self.writer, self.truth_file_path)
        random_pops = []
        if self.random_generated:
            # random generate 1000, threshold = 0.01, set optimize as False, i.e., only use the sop
            pops = interface_prob.run_random_generate(self.output_path, cec_check_all_path, self.prune, sample_num=self.sample_num, truth_file_path=self.truth_file_path, threshold=0.01, threshold_nd=threshold_nd, optimize=False)
            random_pops.extend(pops)
            # random generate 1000, threshold = 0.05, set optimize as False, i.e., only use the sop
            # random_pops = interface_prob.run_random_generate(self.output_path, cec_check_all_path, sample_num=self.sample_num, truth_file_path=self.truth_file_path, threshold=0.05, optimize=False)
            # baseline_pops.extend(random_pops)
        # initialization
        population = []
        if self.use_seed: # the initial pop is provided by user
            with open(self.seed_path) as file:
                data = json.load(file)
            population = interface_ec.population_generation_seed(data,self.exp_n_proc)
            filename = self.output_path + "/results/pops/population_generation_0.json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)
            n_start = 0
        else:
            if self.load_pop:  # load population from files
                print("load initial population from " + self.load_pop_path)
                with open(self.load_pop_path) as file:
                    data = json.load(file)
                for individual in data:
                    population.append(individual)
                print("initial population has been loaded!")
                n_start = self.load_pop_id
            else:  # create new population
                print("creating initial population:")
                if self.LLM_generation_initial:
                    population = interface_ec.population_generation_llm()
                else:
                    population = interface_ec.population_generation()
                population.extend(random_pops)
                population = self.manage.population_management(population, self.pop_size, self.local_search)
                # print(len(population))
                # if len(population)<self.pop_size:
                #     for op in [self.operators[0],self.operators[2]]:
                #         _,new_ind = interface_ec.get_algorithm(population, op)
                #         self.add2pop(population, new_ind)
                #         population = self.manage.population_management(population, self.pop_size)
                #         if len(population) >= self.pop_size:
                #             break
                #         print(len(population))
                print(f"Pop initial: ")
                for i, off in enumerate(population):
                    print(" Acc: ", off['accuracy'], end="|")
                    print(" Obj: ", off['objective'], end="|")
                    print(" Legalized_Obj: ", off['legalized_objective'], end="|\n")
                for i, off in enumerate(population):
                    self.writer.add_scalar("The initial pop's node number", off['legalized_objective'], i)
                self.writer.add_scalar("The best pop's node number", self.manage.best_population(population)['legalized_objective'], 0)
                print()
                print("initial population has been created!")
                # Save population to a file
                filename = self.output_path + "/results/pops/population_generation_0.json"
                with open(filename, 'w') as f:
                    json.dump(population, f, indent=5)
                n_start = 0

        # main loop
        n_op = len(self.operators)

        for pop in range(n_start, self.n_pop):  
            print('*****************************************************************\n')
            print(f" Population: [{pop + 1} / {self.n_pop}] ", end="\n") 
            #print(f" [{na + 1} / {self.pop_size}] ", end="|")         
            for i in range(n_op):
                op = self.operators[i]
                print("#############################################################")
                print(f" Operator: {op}, [{i + 1} / {n_op}] ", end="\n") 
                op_w = self.operator_weights[i]
                if (np.random.rand() < op_w): 
                    parents, offsprings = interface_ec.get_algorithm(population, op, pop)
                # reflection
                if self.reflect:
                    output_folder = os.path.join(self.output_path, 'reflection')
                    os.makedirs(output_folder, exist_ok=True)
                    for j in range(len(offsprings)):
                        self.reflection.set_paras(offsprings[j], self.api_key, self.api_endpoint, self.llm_model, self.truth_file_path, output_folder)    
                        offsprings[j] = self.reflection.run()
                print(f" OP: {op}, [{i + 1} / {n_op}] ", end="\n") 
                for off in offsprings:
                    print(" Acc: ", off['accuracy'], end="|")
                    print(" Obj: ", off['objective'], end="|")
                    print(" Legalized_Obj: ", off['legalized_objective'], end="|\n")
                self.add2pop(population, offsprings)  # Check duplication, and add the new offspring
                # populatin management
                size_act = min(len(population), self.pop_size)
                population = self.manage.population_management(population, size_act, self.local_search)
                print()
                print("#############################################################")
                # if is_add:
                #     data = {}
                #     for i in range(len(parents)):
                #         data[f"parent{i + 1}"] = parents[i]
                #     data["offspring"] = offspring
                #     with open(self.output_path + "/results/history/pop_" + str(pop + 1) + "_" + str(
                #             na) + "_" + op + ".json", "w") as file:
                #         json.dump(data, file, indent=5)



            # Save population to a file
            filename = self.output_path + "/results/pops/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)

            # Save the best one to a file
            filename = self.output_path + "/results/pops_best/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population[0], f, indent=5)


            print(f"--- {pop + 1} of {self.n_pop} populations finished. Time Cost:  {((time.time()-time_start)/60):.1f} m")
            # print("Pop Objs: ", end=" ")
            # for i in range(len(population)):
            #     print(str(population[i]['objective']) + " ", end="")
            
            print("Pop Objs: ", end="\n")
            for i in range(len(population)):
                print(" Acc: ", population[i]['accuracy'], end="|")
                print(" Obj: ", population[i]['objective'], end="|")
                print(" Legalized_Obj: ", population[i]['legalized_objective'], end="|\n")
            self.writer.add_scalar("The best pop's node number", self.manage.best_population(population)['legalized_objective'], pop)
            print()
            print('*****************************************************************\n')

    def get_output_constraints(self):
        # SOP
        program_path = os.path.join(self.output_path, 'initial_sop_program.txt')
        command = f"./abc -c 'read_truth -xf {self.truth_file_path}; collapse; sop; strash; \
        write_aiger {os.path.join(self.output_path, 'temp.aig')}; read {os.path.join(self.output_path, 'temp.aig')}; \
        strash; write_eqn {program_path}'"
        output = subprocess.check_output(command, shell=True)
        raw_code = self.prob.from_program_to_raw_code(program_path)
        po_assignments = re.findall(r'po\d+\s*=\s*[^;]+;', raw_code)
        clean_pos = [line for line in po_assignments if 'new' not in line.split('=')[1]]
        constraints = '\n'.join([f'{i+1}.{po}' for i, po in enumerate(clean_pos)]) if clean_pos != [] else 'No constrants'
        return constraints
