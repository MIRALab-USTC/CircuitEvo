import numpy as np
import time
from .aig_evolution import Evolution
import warnings
from joblib import Parallel, delayed
from .evaluator_accelerate import add_numba_decorator
import re
import os
import subprocess
import concurrent.futures

class InterfaceEC():
    def __init__(self, truth_file_path, writer, output_path, input_number, output_number, cec_check_path, use_fx, local_search, pop_size, m, api_endpoint, api_key, 
                 llm_model,llm_use_local,llm_local_url, debug_mode, interface_prob, legalized_parent, constraints,
                 select,n_p,timeout,use_numba,**kwargs):

        # AIG settings
        self.truth_file_path = truth_file_path
        self.writer = writer
        self.output_path = output_path
        self.local_search = local_search
        self.cec_check_path = cec_check_path
        self.use_fx = use_fx
        # LLM settings
        self.pop_size = pop_size
        self.interface_eval = interface_prob
        prompts = interface_prob.prompts
        # constraints = self.get_output_constraints() # constraints for prompt
        print('The constraints are', constraints)
        self.evol = Evolution(input_number, output_number, api_endpoint, api_key, llm_model,llm_use_local,llm_local_url, debug_mode,prompts,truth_file_path,legalized_parent,constraints,**kwargs)
        self.m = m
        self.debug = debug_mode

        if not self.debug:
            warnings.filterwarnings("ignore")

        self.select = select
        self.n_p = n_p
        
        self.timeout = timeout
        self.use_numba = use_numba

    
    def code2file(self,code):
        with open("./ael_alg.py", "w") as file:
        # Write the code to the file
            file.write(code)
        return 
    
    def add2pop(self,population,offspring):
        for ind in population:
            if ind['objective'] == offspring['objective']:
                if self.debug:
                    print("duplicated result, retrying ... ")
                return False
        population.append(offspring)
        return True
    
    def check_duplicate(self,population,code):
        for ind in population:
            if code == ind['code']:
                return True
        return False

    # def population_management(self,pop):
    #     # Delete the worst individual
    #     pop_new = heapq.nsmallest(self.pop_size, pop, key=lambda x: x['objective'])
    #     return pop_new
    
    # def parent_selection(self,pop,m):
    #     ranks = [i for i in range(len(pop))]
    #     probs = [1 / (rank + 1 + len(pop)) for rank in ranks]
    #     parents = random.choices(pop, weights=probs, k=m)
    #     return parents

    # def population_generation(self):
        
    #     n_create = 2
        
    #     population = []

    #     for i in range(n_create):
    #         _,pop = self.get_algorithm([],'i1')
    #         for p in pop:
    #             population.append(p)
             
    #     return population
    
    #########################################
    '''
    step 1. generate the initial AIG program: 
            a. read_truth -xf; collapse; sop; strash
            b. read_truth -xf; bdd; strash; strash
    '''
    def population_generation(self):        
        population = []
        # SOP
        program_path = os.path.join(self.output_path, 'initial_sop_program.txt')
        command = f"./abc -c 'read_truth -xf {self.truth_file_path}; collapse; sop; strash; \
        write_aiger {os.path.join(self.output_path, 'temp.aig')}; read {os.path.join(self.output_path, 'temp.aig')}; \
        strash; write_eqn {program_path}'"
        
        output = subprocess.check_output(command, shell=True)
        raw_code = self.interface_eval.from_program_to_raw_code(program_path)
        _, eqn_nd = self.interface_eval.evaluate(self.output_path, raw_code)
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
        alg['code'] = raw_code
        alg['legalized_code'] = raw_code
        alg['objective'] = eqn_nd
        alg['legalized_objective'] = eqn_nd
        alg['algorithm'] = ''
        population.append(alg)
        
        # BDD
        program_path = os.path.join(self.output_path, 'initial_bdd_program.txt')
        command = f"./abc -c 'read_truth -xf {self.truth_file_path}; bdd; strash; \
        write_aiger {os.path.join(self.output_path, 'temp.aig')}; read {os.path.join(self.output_path, 'temp.aig')}; \
        strash; write_eqn {program_path}'"
        
        output = subprocess.check_output(command, shell=True)
        raw_code = self.interface_eval.from_program_to_raw_code(program_path)
        _, eqn_nd = self.interface_eval.evaluate(self.output_path, raw_code)
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
        alg['code'] = raw_code
        alg['legalized_code'] = raw_code
        alg['objective'] = eqn_nd
        alg['legalized_objective'] = eqn_nd
        alg['algorithm'] = ''
        population.append(alg)
        return population

    def population_generation_llm(self):        
        population = []
        for i in range(self.pop_size):
            [raw_code, _] = self.evol.i1()
            alg = {
                'algorithm': '',
                'code': raw_code,
                'legalized_code': None,
                'accuracy': None,
                'objective': None,
                'legalized_objective': None,
                'other_inf': None
            }
            
            _, _, _, off = self.interface_eval.legalize(alg, self.output_path, self.truth_file_path, self.cec_check_path, self.use_fx, self.local_search)

            population.append(off)
        return population
 
    def population_generation_seed(self,seeds,n_p):

        population = []

        fitness = Parallel(n_jobs=n_p)(delayed(self.interface_eval.evaluate)(seed['code']) for seed in seeds)

        for i in range(len(seeds)):
            try:
                seed_alg = {
                    'algorithm': seeds[i]['algorithm'],
                    'code': seeds[i]['code'],
                    'objective': None,
                    'other_inf': None
                }

                obj = np.array(fitness[i])
                seed_alg['objective'] = np.round(obj, 5) # np.round() rounds the obj to the specified number of decimal places
                population.append(seed_alg)

            except Exception as e:
                print(f"Error in seed algorithm. The reason is {e}")
                exit()

        print("Initiliazation finished! Get "+str(len(seeds))+" seed algorithms")

        return population
    

    def _get_alg(self,pop,operator):
        offspring = {
            'algorithm': None,
            'code': None,
            'legalized_code': None,
            'accuracy': None,
            'objective': None,
            'legalized_objective': None,
            'other_inf': None
        }
        if operator == "i1":
            parents = None
            [offspring['code'],offspring['algorithm']] =  self.evol.i1()            
        elif operator == "e1":
            parents = self.select.parent_selection(pop,self.m)
            [offspring['code'],offspring['algorithm']] = self.evol.e1(parents)
        elif operator == "e2":
            parents = self.select.parent_selection(pop,self.m)
            [offspring['code'],offspring['algorithm']] = self.evol.e2(parents) 
        elif operator == "m1":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.m1(parents[0])   
        elif operator == "m2":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.m2(parents[0]) 
        elif operator == "m3":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.m3(parents[0]) 
        elif operator == "rewrite":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.rewrite(parents[0]) 
        elif operator == "resub":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.resub(parents[0]) 
        else:
            print(f"Evolution operator [{operator}] has not been implemented ! \n") 

        return parents, offspring

    def get_offspring(self, pop, operator):            
        try:
            p, offspring = self._get_alg(pop, operator)
            code = offspring['code']
            # code = re.sub(r'(new_n\d+)(_+)?', lambda m: m.group(1) + '_', code)
            # code = re.sub(r'(pi\d+)(_+)?', lambda m: m.group(1), code)
            # code = re.sub(r'(po\d+)(_+)?', lambda m: m.group(1), code)
            n_retry= 1
            while self.check_duplicate(pop, offspring['code']):
                n_retry += 1
                if self.debug:
                    print("duplicated code, wait 1 second and retrying ... ")
                p, offspring = self._get_alg(pop, operator)
                code = offspring['code']
                if n_retry > 1:
                    break
            # correct the code's form
            # print(f'The raw generated code is {code}')
            code = re.sub(r'(new_n\d+)(_+)?', lambda m: m.group(1) + '_', code)
            code = re.sub(r'(pi\d+)(_+)?', lambda m: m.group(1), code)
            code = re.sub(r'(po\d+)(_+)?', lambda m: m.group(1), code)
            offspring['code'] = code
            print(f'The correct generated code is {code}')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.interface_eval.evaluate, self.output_path, code)
                program_nd, eqn_nd = future.result(timeout=self.timeout)
                offspring['objective'] = np.round(eqn_nd, 5)
                future.cancel()        
                # fitness = self.interface_eval.evaluate(code)
        except Exception as e:
            print(f'wrong in getting offsprings. The reason is {e}')
            offspring = {
                'algorithm': None,
                'code': None,
                'legaized_code': None,
                'accuracy': None,
                'objective': None,
                'legalized_objective': None,
                'other_inf': None
            }
            p = None

        # Round the objective values
        return p, offspring
            # if self.use_numba:
                
            #     # Regular expression pattern to match function definitions
            #     pattern = r"def\s+(\w+)\s*\(.*\):"

            #     # Search for function definitions in the code
            #     match = re.search(pattern, offspring['code'])

            #     function_name = match.group(1)

            #     code = add_numba_decorator(program=offspring['code'], function_name=function_name)
            # else:
            #     code = offspring['code']

            # n_retry= 1
            # while self.check_duplicate(pop, offspring['code']):
                
            #     n_retry += 1
            #     if self.debug:
            #         print("duplicated code, wait 1 second and retrying ... ")
                    
            #     p, offspring = self._get_alg(pop, operator)

            #     if self.use_numba:
            #         # Regular expression pattern to match function definitions
            #         pattern = r"def\s+(\w+)\s*\(.*\):"

            #         # Search for function definitions in the code
            #         match = re.search(pattern, offspring['code'])

            #         function_name = match.group(1)

            #         code = add_numba_decorator(program=offspring['code'], function_name=function_name)
            #     else:
            #         code = offspring['code']
                    
            #     if n_retry > 1:
            #         break
                
                
            #self.code2file(offspring['code'])
        #     with concurrent.futures.ThreadPoolExecutor() as executor:
        #         future = executor.submit(self.interface_eval.evaluate, self.output_path, code)
        #         program_nd, eqn_nd = future.result(timeout=self.timeout)
        #         offspring['objective'] = np.round(eqn_nd, 5)
        #         future.cancel()        
        #         # fitness = self.interface_eval.evaluate(code)
            
        # except Exception as e:
        #     print(f'wrong in getting offsprings. The reason is {e}')
        #     offspring = {
        #         'algorithm': None,
        #         'code': None,
        #         'objective': None,
        #         'other_inf': None
        #     }
        #     p = None

        # # Round the objective values
        # return p, offspring
        
    # def process_task(self,pop, operator):
    #     result =  None, {
    #             'algorithm': None,
    #             'code': None,
    #             'objective': None,
    #             'other_inf': None
    #         }
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         future = executor.submit(self.get_offspring, pop, operator)
    #         try:
    #             result = future.result(timeout=self.timeout)
    #             future.cancel()
    #             #print(result)
    #         except:
    #             future.cancel()
                
    #     return result

    
    def get_algorithm(self, pop, operator, step):
        results = []
        # try:
            # results = Parallel(n_jobs=self.n_p,timeout=self.timeout+15)(delayed(self.get_offspring)(pop, operator)\
            #     for _ in range(self.pop_size))
            # delete the time constraint and parallel for debug
        results = [self.get_offspring(pop, operator) for _ in range(self.pop_size)]
        # except Exception as e:
        #     if self.debug:
        #         print(f"Error: {e}")
        #     print("Parallel time out .")
            
        time.sleep(2)

        # legalization process
        out_p = []
        out_off = []
        accuracy_before_legalized_off_list = []
        fitness_before_legalized_off_list = []
        fitness_after_legalized_off_list = []
        print('-------------------------------------------')
        print('start legalization \n')
        for i, (p, off) in enumerate(results):
            print(f"The {i}th offspring code is\n: {off['code']}")
            if not self.interface_eval.check_raw_code(off['code'], self.truth_file_path, self.output_path):
                print(f"Check raw_code is Wrong! The {i}th offspring is Wrong!")
                continue
            # legalize the program to ensure the accuracy
            accuracy_before_legalized_off, fitness_before_legalized_off, fitness_after_legalized_off, off = self.interface_eval.legalize(off, self.output_path, self.truth_file_path, self.cec_check_path, self.use_fx, self.local_search)
            accuracy_before_legalized_off_list.append(accuracy_before_legalized_off)
            fitness_before_legalized_off_list.append(fitness_before_legalized_off)
            fitness_after_legalized_off_list.append(fitness_after_legalized_off)
            print(f"The {i}th offspring final fitness is: {off['legalized_objective']}")
            # remove the off with None fitness
            if off['objective'] != None:
                out_p.append(p)
                out_off.append(off)
            if self.debug:
                print(f">>> check offsprings: \n {off}") 

        # Find the index of the minimum value in the filtered list
        if all(element is None for element in fitness_after_legalized_off_list):
            pass
        else:
            if self.local_search:
                best_pop_index = min((index for index, value in enumerate(accuracy_before_legalized_off_list) if value is not None), key=lambda x: accuracy_before_legalized_off_list[x])
            else:
                best_pop_index = min((index for index, value in enumerate(fitness_after_legalized_off_list) if value is not None), key=lambda x: fitness_after_legalized_off_list[x])
            self.writer.add_scalar(f'{operator}_best_pop_ACC_before_legalized', accuracy_before_legalized_off_list[best_pop_index], step)
            self.writer.add_scalar(f'{operator}_best_pop_node_number_before_legalized', fitness_before_legalized_off_list[best_pop_index], step)
            self.writer.add_scalar(f'{operator}_best_pop_node_number_after_legalized', fitness_after_legalized_off_list[best_pop_index], step)

        print('end legalization')  
        print('-------------------------------------------')
        return out_p, out_off
    # def get_algorithm(self,pop,operator, pop_size, n_p):
        
    #     # perform it pop_size times with n_p processes in parallel
    #     p,offspring = self._get_alg(pop,operator)
    #     while self.check_duplicate(pop,offspring['code']):
    #         if self.debug:
    #             print("duplicated code, wait 1 second and retrying ... ")
    #         time.sleep(1)
    #         p,offspring = self._get_alg(pop,operator)
    #     self.code2file(offspring['code'])
    #     try:
    #         fitness= self.interface_eval.evaluate()
    #     except:
    #         fitness = None
    #     offspring['objective'] =  fitness
    #     #offspring['other_inf'] =  first_gap
    #     while (fitness == None):
    #         if self.debug:
    #             print("warning! error code, retrying ... ")
    #         p,offspring = self._get_alg(pop,operator)
    #         while self.check_duplicate(pop,offspring['code']):
    #             if self.debug:
    #                 print("duplicated code, wait 1 second and retrying ... ")
    #             time.sleep(1)
    #             p,offspring = self._get_alg(pop,operator)
    #         self.code2file(offspring['code'])
    #         try:
    #             fitness= self.interface_eval.evaluate()
    #         except:
    #             fitness = None
    #         offspring['objective'] =  fitness
    #         #offspring['other_inf'] =  first_gap
    #     offspring['objective'] = np.round(offspring['objective'],5) 
    #     #offspring['other_inf'] = np.round(offspring['other_inf'],3)
    #     return p,offspring
