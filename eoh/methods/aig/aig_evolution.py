import re
import time
import numpy as np
import math
from ...llm.interface_LLM import InterfaceLLM

class Evolution():

    def __init__(self, input_number, output_number, api_endpoint, api_key, model_LLM,llm_use_local,llm_local_url, debug_mode, prompts, truth_file_path, legalized_parent, constraints, **kwargs):

        # set prompt interface
        #getprompts = GetPrompts()
        self.input_number = int(input_number)
        self.output_number = int(output_number)
        self.prompt_task         = prompts.get_task()
        self.prompt_evolution   = prompts.get_evolution()
        # self.prompt_func_name    = prompts.get_func_name()
        # self.prompt_func_inputs  = prompts.get_func_inputs()
        # self.prompt_func_outputs = prompts.get_func_outputs()
        # self.prompt_inout_inf    = prompts.get_inout_inf()
        self.prompt_other_inf    = prompts.get_other_inf()
        self.llm_init_sample = 10
        self.truth_file_path = truth_file_path
        self.legalized_parent = legalized_parent
        self.constraints = constraints
        # if len(self.prompt_func_inputs) > 1:
        #     self.joined_inputs = ", ".join("'" + s + "'" for s in self.prompt_func_inputs)
        # else:
        #     self.joined_inputs = "'" + self.prompt_func_inputs[0] + "'"

        # if len(self.prompt_func_outputs) > 1:
        #     self.joined_outputs = ", ".join("'" + s + "'" for s in self.prompt_func_outputs)
        # else:
        #     self.joined_outputs = "'" + self.prompt_func_outputs[0] + "'"

        # set LLMs
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode # close prompt checking
        self.interface_llm = InterfaceLLM(self.api_endpoint, self.api_key, self.model_LLM,llm_use_local,llm_local_url, self.debug_mode)

    def get_prompt_i1(self):
        with open("prompts/initialization.txt", "r") as f:
            prompt_content = f.read()

        labels = []
        with open(self.truth_file_path) as f:
            line = f.readline()
            while line:
                label = np.array([int(x) for x in line if x>='0' and x<='9'])
                labels.append(label)
                line = f.readline()
            
        output_num = len(labels)
        labels = np.array(labels).T
        result = []
        length = len(label)
        input_num = int(math.log2(length))
        for i in range(length):
            row = [int(x) for x in bin(i)[2:].zfill(input_num)]
            result.append(row)
            
        inputs = np.flip(np.array(result), axis=(0,1))
        
        samples = np.random.randint(0, length, self.llm_init_sample)

        header = ", ".join([f"pi{i}" for i in range(input_num)] + [f"po{i}" for i in range(output_num)])
        lines = [header]
        for i in samples:
            line = ", ".join([str(x) for x in inputs[i]] + [str(x) for x in labels[i]])
            lines.append(line)

        return prompt_content.replace('{truth_table}', "\n".join(lines)).replace('{num_input}', str(input_num)).replace('{num_output}', str(output_num))

    def get_prompt_e1(self,indivs):
        prompt_indiv = ""
        if self.legalized_parent == True:
            for i in range(len(indivs)):
                prompt_indiv=prompt_indiv+"No."+str(i+1) +" program and the corresponding code are: \n" + indivs[i]['legalized_code']+"\n"
        else:
            for i in range(len(indivs)):
                prompt_indiv=prompt_indiv+"No."+str(i+1) +" program and the corresponding code are: \n" + indivs[i]['code']+"\n"      
        prompt_parts = [
            self.prompt_task.format(constraints=self.constraints),
            self.prompt_evolution['e1'].format(
                program_number=len(indivs), 
                prompt_indiv=prompt_indiv
            )
            # f"I have {len(indivs)} existing programs as follows:",
            # prompt_indiv,
            # "Please help me create a new program that has a totally different Program Body from the given ones but can be motivated from them.",
            # "You can generate new Program Bodies and mix them with parts of the Program Body from the given program, \
            # similar to the crossover operation in genetic algorithms.",
            # self.prompt_other_inf,
            # "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def get_prompt_e2(self, indivs):
        prompt_indiv = ""
        if self.legalized_parent == True:
            for i in range(len(indivs)):
                prompt_indiv=prompt_indiv+"No."+str(i+1) +" program and the corresponding code are: \n" + indivs[i]['legalized_code']+"\n"
        else:
            for i in range(len(indivs)):
                prompt_indiv=prompt_indiv+"No."+str(i+1) +" program and the corresponding code are: \n" + indivs[i]['code']+"\n"   

        prompt_parts = [
            self.prompt_task.format(constraints=self.constraints),
            self.prompt_evolution['e2'].format(
                program_number=len(indivs), 
                prompt_indiv=prompt_indiv
            )
            # f"I have {len(indivs)} existing programs as follows:",
            # prompt_indiv,
            # "Please help me create a new program that has a totally different form from the given ones.",
            # self.prompt_other_inf,
            # "Do not give additional explanations and redundant strings."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def get_prompt_m1(self, indiv1):
        if self.legalized_parent == True:
            prompt_indiv = indiv1['legalized_code']
        else:
            prompt_indiv = indiv1['code']
        prompt_parts = [
            self.prompt_task.format(constraints=self.constraints),
            self.prompt_evolution['m1'].format(
                prompt_indiv=prompt_indiv
            )            
            # f"I have one program as follows:",
            # indiv1['code'],
            # "Please assist me in creating a new program that has a different form but can be a modified version of the program provided. \
            # You can modify the program by selectively adding or removing the NOT operator (!) before some variables, changing some AND operators (*) to OR (+), \
            # or vice versa, similar to the mutation process in genetic algorithms.",
            # self.prompt_other_inf,
            # "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def get_prompt_m2(self,indiv1):
        if self.legalized_parent == True:
            prompt_indiv = indiv1['legalized_code']
        else:
            prompt_indiv = indiv1['code']
        prompt_parts = [
            self.prompt_task.format(constraints=self.constraints),
            self.prompt_evolution['m2'].format(
                prompt_indiv=prompt_indiv
            )              
            # f"I have one program as follows:",
            # indiv1['code'],
            # "Please identify the main program structures and assist me in creating a new program that has a different structure of the program provided.",
            # self.prompt_other_inf,
            # "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def get_prompt_m3(self,indiv1):
        prompt_parts = [
            "First, you need to identify the main components in the program below.",
            "Next, analyze whether any of these components can be overfit to the in-distribution instances.",
            "Then, based on your analysis, simplify the components to enhance the generalization to potential out-of-distribution instances.",
            "Finally, provide the revised program, keeping the inputs, and outputs unchanged.",
            indiv1['code'],
            self.prompt_other_inf,
            "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content

    def get_prompt_rewrite(self, indiv1):
        prompt_parts = [
            self.prompt_task,
            f"I have one And-inverter-Graph(AIG) with its program as follows:",
            f"Program description: {indiv1['algorithm']}",
            "Code:",
            indiv1['code'],
            "Please simplify the AIG program by applying Boolean equivalences and eliminating redundancy.",
            "First, describe your new program and main steps in one sentence. The description must be inside a brace. Next, implement it in a progarm.",
            f"This program should accept {self.input_number} inputs and return {self.output_number} outputs.",
            self.prompt_other_inf,
            "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def get_prompt_resub(self, indiv1):
        prompt_parts = [
            self.prompt_task,
            f"I have one And-inverter-Graph(AIG) with its program as follows:",
            f"Program description: {indiv1['algorithm']}",
            "Code:",
            indiv1['code'],
            "Please optimize the AIG program by exploring alternative gate combinations and reducing logic complexity.",
            "First, describe your new program and main steps in one sentence. The description must be inside a brace. Next, implement it in a progarm.",
            f"This program should accept {self.input_number} inputs and return {self.output_number} outputs.",
            self.prompt_other_inf,
            "Do not give additional explanations."
        ]
        prompt_content = "\n".join(prompt_parts)
        return prompt_content
    
    def _get_alg(self,prompt_content):
        # print(f"\nprompt content:\n{prompt_content}\n")
        response = self.interface_llm.get_response(prompt_content)
        # print('The response of LLM is:', response)
        algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
        if len(algorithm) == 0:
            if 'python' in response:
                algorithm = re.findall(r'^.*?(?=python)', response,re.DOTALL)
            elif 'import' in response:
                algorithm = re.findall(r'^.*?(?=import)', response,re.DOTALL)
            else:
                algorithm = re.findall(r'^.*?(?=def)', response,re.DOTALL)
        code = re.findall(r"^.*=.*$", response, flags=re.MULTILINE)
            # code = re.findall(r"def.*return", response, re.DOTALL)

        n_retry = 1
        # while (len(algorithm) == 0 or len(code) == 0):
        while (len(code) == 0):
            if self.debug_mode:
                print("Error: algorithm or code not identified, wait 1 seconds and retrying ... ")

            response = self.interface_llm.get_response(prompt_content)

            algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
            if len(algorithm) == 0:
                if 'python' in response:
                    algorithm = re.findall(r'^.*?(?=python)', response,re.DOTALL)
                elif 'import' in response:
                    algorithm = re.findall(r'^.*?(?=import)', response,re.DOTALL)
                else:
                    algorithm = re.findall(r'^.*?(?=def)', response,re.DOTALL)

            code = re.findall(r"^.*=.*$", response, flags=re.MULTILINE)
                
            if n_retry > 3:
                break
            n_retry +=1

        # algorithm = algorithm[0]
        # no need for algorithm
        algorithm = ''
        code = '\n'.join([raw for raw in code]) 
        code_all = code
        # print(f'code is {code_all}')
        if len(code_all) == 0:
            raise ValueError(f'The code is None, the response is:\n {response}')
        # code_all = code+" "+", ".join(s for s in self.prompt_func_outputs) 


        return [code_all, algorithm]


    def i1(self):

        prompt_content = self.get_prompt_i1()

        print("\n", "#" * 20, "Initialization Prompt", "#" * 20)
        print(prompt_content)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ llm initialization ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
        
        [code_all, algorithm] = self._get_alg(prompt_content)

        print("\n", "#" * 20, "Initialization Response", "#" * 20)
        print(code_all)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def e1(self,parents):
      
        prompt_content = self.get_prompt_e1(parents)
        
        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e1 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def e2(self,parents):
      
        prompt_content = self.get_prompt_e2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e2 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def m1(self,parents):
      
        prompt_content = self.get_prompt_m1(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m1 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def m2(self,parents):
      
        prompt_content = self.get_prompt_m2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m2 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def m3(self, parents):
      
        prompt_content = self.get_prompt_m3(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m3 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def rewrite(self, parents):
        prompt_content = self.get_prompt_rewrite(parents)
        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ rewrite ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def resub(self, parents):
        prompt_content = self.get_prompt_resub(parents)
        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ resub ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
