import json
import re
import os
from typing import Dict, List
import math
import random

import requests
import numpy as np
# from .run import AIGenerator
import sys
# sys.path.append('..')
from ..legalization.abc_append import legalization, utils_abc
from ..run import AIGenerator

class Reflection():
    """Use the reflection API as follows:
    
    >>> reflection = Reflection(...)
    >>> reflection.run()
    >>> off = reflection.candidate
    
    Remember to comment out `from .run import AIGenerator` and `aig: AIGenerator`"""

    total = 0
    better = 0
    same = 0
    worse = 0
    bad = 0

    def __init__(self):
        self.aig = AIGenerator()
        
    def set_paras(
        self, 
        program: Dict = None,
        llm_api_key: str = None,
        llm_api_endpoint: str= None,
        llm_model: str = None,
        truth_file_path: str = None,
        output_folder: str = None,
        num_trial: int = 3,
        num_iter: int = 5,
        num_sample: int = 10, # number of the sample bits
        num_program: int = 3 # number of the generated reflection programs
        ): 
        self.program = program
        self.llm_api_key = llm_api_key
        self.llm_api_endpoint = llm_api_endpoint
        self.llm_model = llm_model
        self.truth_file_path = truth_file_path
        self.output_folder = output_folder
        self.num_trial = num_trial
        self.num_iter = num_iter
        self.num_sample = num_sample
        self.num_program = num_program
        self.candidate = self.program
        self.aig.folder_path = self.output_folder
    def run(self):
        """Run the reflection process."""
        print('*****************************************************************\n')
        print('Start reflection')
        print("\nRunning reflection process for: \n")
        print(self.candidate["code"])
        print("Analysis of the initial candidate:")
        print(self.analysis(self.candidate["code"]))

        self.candidate["accuracy"] = self.evaluate_accuracy(self.candidate["code"])
        if self.candidate["accuracy"] == 1:
            print("The initial candidate is already accurate enough.")
            return self.candidate
        
        for _ in range(self.num_iter):
            try:
                self.reflection()
            except Exception as e:
                print(f"Run reflection failed. The reason is {e}")
                continue
        print('End reflection')
        print(f"\nReflection process completed. Run {Reflection.total} times. Find a better candidate {Reflection.better} \
times, the same candidate {Reflection.same} times, a worse candidate {Reflection.worse} times, and a bad candidate \
{Reflection.bad} times.")
        print('*****************************************************************\n')
        return self.candidate
     
    def reflection(self):
        """A single iteration of the reflection process."""
        Reflection.total += 1
        # Reflection
        response = self.reflect()
        print(f"\nReflection response:\n{response}\n")
        # Generate by the abc
        code = self.generate(response)
        print(f"\nGenerated code after reflection:\n{code}\n")
        accuracy = self.evaluate_accuracy(code)
        print("Analysis of the generated code:")
        result = self.analysis(code)
        print(result)
        if result["accuracy"] >= self.candidate["accuracy"]:
            if result["legalized_objective"] < self.candidate["legalized_objective"]:
                Reflection.better += 1
                print(f"Find a better candidate with accuracy {accuracy}.")
                self.candidate["code"] = code
                self.candidate["accuracy"] = accuracy
                self.candidate['reflection'] = True
            else:
                Reflection.worse += 1
                print("Find a worse candidate. Keep the current one.")
        else:
            if accuracy > 0:
                Reflection.worse += 1
                print("Find a worse candidate. Keep the current one.")
            else:
                Reflection.bad += 1
                print("Find a bad candidate. Keep the current one.")

    def reflect(self) -> str:
        """Reflect on the current candidate program.
        
        :param inputs: A list of candidate programs.
        :type inputs: List[str]
        
        :return: The response from the reflection API.
        :rtype: str"""
        code = self.candidate["code"]
        prompt = self.reflection_prompt(code, self.candidate['accuracy'])
        # print(f'The prompt for reflection is: {prompt}')
        response = self.get_response(prompt)
        if response is not None:
            index = response.find('1.')
            if index != '-1':
                response = response[index:]
            return response
        raise Exception("Reflection failed. Check the API or your network connection.")

    # def generate(self, program_pre_0_lab_1, program_pre_1_lab_0) -> str:
    #     code = self.candidate["code"]
    #     program_path = os.path.join(self.output_folder, 'temp_before_legalized_program.txt')
    #     complementary_pre_1_lab_0_program_path = os.path.join(self.output_folder, 'temp_complementary_pre_1_lab_0_program_path.txt')
    #     complementary_pre_0_lab_1_program_path = os.path.join(self.output_folder, 'temp_complementary_pre_0_lab_1_program_path.txt')
    #     utils_abc.from_raw_code_to_program(code, program_path)
    #     utils_abc.from_raw_code_to_program(program_pre_0_lab_1, complementary_pre_0_lab_1_program_path)
    #     utils_abc.from_raw_code_to_program(program_pre_1_lab_0, complementary_pre_1_lab_0_program_path)
    #     # step 2: make sure that the three program files have the same input names and different output names.
    #     utils_abc.refresh(program_path, self.output_folder)
    #     utils_abc.refresh(complementary_pre_1_lab_0_program_path, self.output_folder)
    #     utils_abc.refresh(complementary_pre_0_lab_1_program_path, self.output_folder)
    #     outorder, outorder_pre_0_lab_1, outorder_pre_1_lab_0 = legalization.process_program_for_cmd_append(program_path, self.output_folder, complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path)
        
    #     # step 3: use abc command 'abc' to get the combined program file.
    #     appended_program_path = os.path.join(self.output_folder, 'temp_append_program.txt')
    #     legalization.append_programs(complementary_pre_1_lab_0_program_path, complementary_pre_0_lab_1_program_path, appended_program_path, optimize=False)        
    #     _, eqn_nd = utils_abc.evaluate(utils_abc.from_program_to_raw_code(appended_program_path), self.output_folder)
    #     print(f'The complementary eqn node number is {eqn_nd}')
    #     with open(appended_program_path, 'r') as f:
    #         lines = f.readlines()
    #     mapping = {f'po{i}': outorder_pre_0_lab_1[i] for i in range(len(outorder_pre_0_lab_1))} if len(outorder_pre_0_lab_1) <= 10 else {f'po{i:02}': outorder_pre_0_lab_1[i] for i in range(len(outorder_pre_0_lab_1))}
    #     for i in range(len(lines)):
    #         for key in mapping.keys():
    #             if key in lines[i]:
    #                 lines[i] = lines[i].replace(key, mapping[key])
    #     with open(appended_program_path, 'w') as f:
    #         f.writelines(lines)
    #     legalization.append_programs(appended_program_path, program_path, appended_program_path, optimize=False)
    #     # step 4: process the combined program file and return the final legalized program file.        
    #     legalized_program_path = os.path.join(self.output_folder, 'temp_legalized_program.txt')
    #     legalization.legal(appended_program_path, legalized_program_path, outorder, outorder_pre_0_lab_1, outorder_pre_1_lab_0, self.output_folder, optimize=False)  
    #     legalized_program = utils_abc.from_program_to_raw_code(legalized_program_path)
    #     return legalized_program
    
    def generate(self, reflection: str) -> str:
        """Generate a new candidate program.
        
        :param reflection: The reflection response from the API.
        :type reflection: str
        
        :return: The response from the reflection API.
        :rtype: str"""
        code = self.candidate["code"]
        prompt = self.generator_prompt(code, reflection)
        response = self.get_response(prompt)
        if response is not None:
            response = re.sub(r'(new_n\d+)(_+)?', lambda m: m.group(1) + '_', response)
            response = re.sub(r'(pi\d+)(_+)?', lambda m: m.group(1), response)
            response = re.sub(r'(po\d+)(_+)?', lambda m: m.group(1), response)
            response = response.replace('`', '')
            return response
        raise Exception("Generation failed. Check the API or your network connection.")

    def analysis(self, code: str) -> str:
        result = {}
        try:
            result['accuracy'] = float(self.evaluate_accuracy(code))
            result['objective'] = int(self.aig.evaluate(self.output_folder, code)[1])
            cec_check_path = self.aig.generate_cecaig_from_truth(self.truth_file_path, label='all')
            legalized_code = self.aig._legalize_(code, self.truth_file_path, cec_check_path)
            result['legalized_objective'] = int(self.aig.evaluate(self.output_folder, legalized_code)[1])
        except Exception as e:
            print(f'Error in analysis. The reason is {e}')
            pass

        return result
    
    def evaluate_accuracy(self, code: str) -> float:
        try:
            temp_program_path = self.aig.from_raw_code_to_program(code, self.output_folder, 'for_conversion_program.txt')
            acc_list = legalization.get_accuracy(temp_program_path, self.truth_file_path, self.output_folder)
            average_acc = np.mean(acc_list)
        except Exception as e:
            pass
            return 0.0
        return average_acc

    def get_response(self, content: str) -> str:
        payload_explanation = json.dumps(
            {
                "model": self.llm_model,
                "messages": [
                    {"role": "user", "content": content}
                ],
            }
        )
        headers = {
            "Authorization": "Bearer " + self.llm_api_key,
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "x-api2d-no-cache": "1",
        }
        response = None
        n_trial = 1
        while True:
            n_trial += 1
            if n_trial > self.num_trial:
                return response
            try:
                conn = requests.post(
                    f"https://{self.llm_api_endpoint}/v1/chat/completions",
                    data=payload_explanation,
                    headers=headers
                )
                response = conn.json()["choices"][0]["message"]["content"]
                break
            except Exception as e:
                print(f"Request failed. The reason is {e}")
                continue
        return response

    def reflection_prompt(self, code: str, accuracy: float) -> str:
        with open('/yqbai/LLM4Boolean/LLM4AIG/eoh/src/eoh/problems/optimization/aig/reflection/prompts/reflection_v2.txt', 'r') as f:
            content = f.read()
        content = content.format(program=code, accuracy=accuracy)
        return content
    
    def generator_prompt(self, code: str, reflection: str) -> str:
        with open('/yqbai/LLM4Boolean/LLM4AIG/eoh/src/eoh/problems/optimization/aig/reflection/prompts/generation_v2.txt', 'r') as f:
            content = f.read()
        content = content.format(program=code, reflection=reflection)
        return content
        
if __name__ == '__main__':
    programs = [
        {
            "algorithm": "",
            "code": "\nINORDER = pi0 pi1 pi2 pi3 pi4 pi5 pi6;\nOUTORDER = po0 po1;\nnew_n10_ = !pi1 * pi4;\nnew_n11_ = pi3 * !new_n10_;\nnew_n12_ = pi0 * new_n11_;\nnew_n13_ = pi1 * !pi4;\nnew_n14_ = !pi1 * !pi3;\nnew_n15_ = !new_n13_ * !new_n14_;\nnew_n16_ = pi5 * !new_n15_;\nnew_n17_ = !pi0 * new_n16_;\nnew_n18_ = pi4 * new_n14_;\nnew_n19_ = !new_n17_ * !new_n18_;\nnew_n20_ = !new_n12_ * new_n19_;\nnew_n21_ = pi2 * !new_n20_;\nnew_n22_ = !pi3 * pi4;\nnew_n23_ = !pi1 * pi3;\nnew_n24_ = !new_n22_ * !new_n23_;\nnew_n25_ = !pi2 * !new_n24_;\nnew_n26_ = pi5 * new_n25_;\nnew_n27_ = !new_n18_ * !new_n26_;\nnew_n28_ = !pi0 * !new_n27_;\nnew_n29_ = pi0 * new_n13_;\nnew_n30_ = !pi2 * new_n10_;\nnew_n31_ = !new_n29_ * !new_n30_;\nnew_n32_ = pi3 * !new_n31_;\nnew_n33_ = pi5 * new_n32_;\nnew_n34_ = !new_n28_ * !new_n33_;\nnew_n35_ = !new_n21_ * new_n34_;\nnew_n36_ = pi3 * pi4;\nnew_n37_ = !pi3 * !pi4;\nnew_n38_ = !new_n36_ * !new_n37_;\nnew_n39_ = pi1 * !new_n38_;\nnew_n40_ = !pi1 * new_n27_;\nnew_n41_ = !new_n39_ * !new_n40_;\nnew_n42_ = !pi2 * !new_n41_;\nnew_n43_ = !pi0 * new_n42_;\npo1 = new_n35_ * new_n43_;\npo0 = !pi6;\n\n",
            "accuracy": 0.75,
            "objective": 35.0,
            "legalized_objective": 78.0,
            "reflection": False,
            "other_inf": "59"
        },
        {
            "algorithm": "",
            "code": "# Equations for \"./outputs/2025-01-07/16-23-25/random_generate/temp_aig\" written by ABC on Tue Jan  7 16:23:27 2025\nINORDER = pi0 pi1 pi2 pi3 pi4 pi5 pi6;\nOUTORDER = po0 po1;\nnew_n10_ = pi0 * !pi1;\nnew_n11_ = !pi3 * !new_n10_;\nnew_n12_ = !pi5 * new_n11_;\nnew_n13_ = !pi1 * pi3;\nnew_n14_ = !pi0 * new_n13_;\nnew_n15_ = !new_n12_ * !new_n14_;\nnew_n16_ = !pi2 * !new_n15_;\nnew_n17_ = pi3 * !pi6;\nnew_n18_ = !pi1 * !new_n17_;\nnew_n19_ = pi0 * pi3;\nnew_n20_ = !new_n18_ * !new_n19_;\nnew_n21_ = pi2 * !new_n20_;\nnew_n22_ = pi3 * pi5;\nnew_n23_ = !new_n21_ * !new_n22_;\nnew_n24_ = !new_n16_ * new_n23_;\nnew_n25_ = !pi4 * !new_n24_;\nnew_n26_ = !pi2 * pi3;\nnew_n27_ = pi0 * new_n26_;\nnew_n28_ = !pi0 * !pi3;\nnew_n29_ = !new_n27_ * !new_n28_;\nnew_n30_ = pi1 * !new_n29_;\nnew_n31_ = !pi2 * pi5;\nnew_n32_ = !pi1 * !pi3;\nnew_n33_ = !pi6 * new_n32_;\nnew_n34_ = !new_n31_ * !new_n33_;\nnew_n35_ = pi0 * !new_n34_;\nnew_n36_ = pi2 * !pi3;\nnew_n37_ = !pi5 * new_n36_;\nnew_n38_ = !new_n35_ * !new_n37_;\nnew_n39_ = !new_n30_ * new_n38_;\nnew_n40_ = pi4 * !new_n39_;\nnew_n41_ = !pi1 * !new_n28_;\nnew_n42_ = pi2 * pi3;\nnew_n43_ = !new_n41_ * !new_n42_;\nnew_n44_ = pi5 * !new_n43_;\nnew_n45_ = !new_n40_ * !new_n44_;\npo1 = new_n25_ * !new_n45_;\npo0 = !pi6;\n\n",
            "accuracy": 0.75781,
            "objective": 37.0,
            "legalized_objective": 74.0,
            "reflection": False,
            "other_inf": "60"
        },
        {
            "algorithm": "",
            "code": "# Equations for \"./outputs/2025-01-02/19-46-34/sop_factor/./temp_aig\" written by ABC on Thu Jan  2 19:49:42 2025\nINORDER = pi00 pi01 pi02 pi03 pi04 pi05 pi06 pi07 pi08 pi09 pi10;\nOUTORDER = po0 po1 po2 po3 po4 po5 po6 po7 po8;\nnew_n21_ = !pi03 * !pi06;\nnew_n22_ = pi01 * new_n21_;\nnew_n23_ = !pi01 * new_n21_;\npo0 = new_n22_ + new_n23_;\nnew_n25_ = !pi04 * !pi08;\nnew_n26_ = pi00 * pi07;\nnew_n27_ = new_n25_ * !new_n26_;\nnew_n28_ = pi01 * new_n27_;\nnew_n29_ = !pi00 * !pi07;\nnew_n30_ = !pi01 * new_n29_;\npo1 = new_n28_ + new_n30_;\nnew_n32_ = pi01 * new_n25_;\npo2 = new_n30_ + new_n32_;\nnew_n34_ = !pi02 * !pi10;\nnew_n35_ = pi03 * pi06;\nnew_n36_ = new_n21_ * !new_n35_;\nnew_n37_ = new_n34_ * new_n36_;\nnew_n38_ = !pi06 * new_n34_;\nnew_n39_ = new_n25_ * new_n38_;\nnew_n40_ = new_n25_ * new_n39_;\nnew_n41_ = !new_n26_ * new_n40_;\nnew_n42_ = new_n37_ * new_n41_;\nnew_n43_ = !new_n37_ * !new_n42_;\nnew_n44_ = pi01 * new_n43_;\nnew_n45_ = new_n21_ * new_n34_;\nnew_n46_ = new_n21_ * new_n45_;\nnew_n47_ = new_n25_ * new_n46_;\nnew_n48_ = new_n25_ * new_n47_;\nnew_n49_ = new_n29_ * new_n48_;\nnew_n50_ = !pi01 * new_n49_;\npo3 = new_n44_ + new_n50_;\nnew_n52_ = !pi03 * new_n38_;\nnew_n53_ = pi02 * pi06;\nnew_n54_ = pi10 * new_n53_;\nnew_n55_ = new_n52_ * !new_n54_;\nnew_n56_ = new_n25_ * new_n55_;\nnew_n57_ = new_n25_ * new_n56_;\nnew_n58_ = !pi07 * new_n57_;\nnew_n59_ = pi00 * !new_n58_;\nnew_n60_ = pi01 * new_n59_;\npo4 = new_n50_ + new_n60_;\nnew_n62_ = new_n34_ * !new_n35_;\nnew_n63_ = new_n21_ * new_n62_;\nnew_n64_ = pi01 * new_n63_;\nnew_n65_ = new_n25_ * new_n29_;\nnew_n66_ = new_n47_ * new_n65_;\nnew_n67_ = !new_n47_ * !new_n66_;\nnew_n68_ = !pi01 * new_n67_;\npo5 = new_n64_ + new_n68_;\nnew_n70_ = pi01 * pi09;\nnew_n71_ = !pi01 * pi09;\npo6 = new_n70_ + new_n71_;\nnew_n73_ = pi01 * new_n34_;\nnew_n74_ = !pi01 * new_n34_;\npo7 = new_n73_ + new_n74_;\nnew_n76_ = pi01 + pi08;\nnew_n77_ = pi01 * pi08;\npo8 = new_n76_ + new_n77_;\n\n",
            "accuracy": 0.69857,
            "objective": 58.0,
            "legalized_objective": 317.0,
            "reflection": False,
            "other_inf": "61"
        },
        {
            "algorithm": "",
            "code": "# Equations for \"./outputs/2025-01-07/16-23-25/temp\" written by ABC on Tue Jan  7 16:23:29 2025\nINORDER = pi0 pi1 pi2 pi3 pi4 pi5 pi6;\nOUTORDER = po0 po1;\nnew_n10_ = !pi2 * pi4;\nnew_n11_ = pi2 * !pi4;\nnew_n12_ = !new_n10_ * !new_n11_;\nnew_n13_ = pi1 * pi3;\nnew_n14_ = !pi1 * !pi3;\nnew_n15_ = !new_n13_ * !new_n14_;\nnew_n16_ = pi3 * pi5;\nnew_n17_ = !pi1 * new_n16_;\nnew_n18_ = new_n15_ * !new_n17_;\nnew_n19_ = pi0 * !new_n18_;\nnew_n20_ = !pi0 * !pi1;\nnew_n21_ = new_n16_ * new_n20_;\nnew_n22_ = !new_n19_ * !new_n21_;\nnew_n23_ = !new_n12_ * !new_n22_;\nnew_n24_ = pi2 * pi4;\nnew_n25_ = !pi2 * !pi4;\nnew_n26_ = !new_n24_ * !new_n25_;\nnew_n27_ = !pi3 * !pi5;\nnew_n28_ = !new_n16_ * !new_n27_;\nnew_n29_ = !pi0 * !new_n28_;\nnew_n30_ = pi0 * new_n16_;\nnew_n31_ = !new_n29_ * !new_n30_;\nnew_n32_ = !pi1 * pi5;\nnew_n33_ = pi1 * !pi5;\nnew_n34_ = !new_n32_ * !new_n33_;\nnew_n35_ = !pi3 * !new_n34_;\nnew_n36_ = pi0 * new_n35_;\nnew_n37_ = new_n31_ * !new_n36_;\nnew_n38_ = !new_n26_ * !new_n37_;\nnew_n39_ = !pi3 * pi4;\nnew_n40_ = pi3 * !pi4;\nnew_n41_ = !new_n39_ * !new_n40_;\nnew_n42_ = pi1 * pi5;\nnew_n43_ = !pi0 * new_n42_;\nnew_n44_ = !pi1 * !pi5;\nnew_n45_ = pi0 * new_n44_;\nnew_n46_ = !new_n43_ * !new_n45_;\nnew_n47_ = !new_n41_ * !new_n46_;\nnew_n48_ = !pi3 * !pi4;\nnew_n49_ = !pi1 * new_n48_;\nnew_n50_ = !pi0 * new_n49_;\nnew_n51_ = !new_n47_ * !new_n50_;\nnew_n52_ = pi2 * !new_n51_;\nnew_n53_ = pi0 * pi5;\nnew_n54_ = pi0 * !new_n53_;\nnew_n55_ = pi4 * new_n54_;\nnew_n56_ = pi3 * new_n55_;\nnew_n57_ = pi1 * new_n56_;\nnew_n58_ = pi4 * !pi5;\nnew_n59_ = pi3 * new_n58_;\nnew_n60_ = new_n20_ * new_n59_;\nnew_n61_ = !new_n57_ * !new_n60_;\nnew_n62_ = pi2 * new_n61_;\nnew_n63_ = !new_n52_ * new_n62_;\nnew_n64_ = !new_n38_ * new_n63_;\npo1 = !new_n23_ * new_n64_;\npo0 = !pi6 * pi5;\n\n",
            "accuracy": 0.5,
            "objective": 56.0,
            "legalized_objective": 108.0,
            "reflection": False,
            "other_inf": "60"
        },
        {
            "algorithm": "",
            "code": "# Equations for \"./outputs/2025-01-02/19-46-34/sop_factor/./temp_aig\" written by ABC on Thu Jan  2 19:49:43 2025\nINORDER = pi00 pi01 pi02 pi03 pi04 pi05 pi06 pi07 pi08 pi09 pi10;\nOUTORDER = po0 po1 po2 po3 po4 po5 po6 po7 po8;\nnew_n21_ = !pi03 * !pi06;\nnew_n22_ = pi01 * new_n21_;\nnew_n23_ = !pi01 * new_n21_;\npo0 = new_n22_ + new_n23_;\nnew_n25_ = !pi00 * !pi07;\nnew_n26_ = pi01 * new_n25_;\nnew_n27_ = !pi01 * new_n25_;\npo1 = new_n26_ + new_n27_;\nnew_n29_ = !pi04 * !pi08;\nnew_n30_ = pi01 * new_n29_;\npo2 = new_n27_ + new_n30_;\nnew_n32_ = !pi02 * !pi10;\nnew_n33_ = new_n21_ * new_n32_;\nnew_n34_ = !pi06 * new_n32_;\nnew_n35_ = new_n29_ * new_n34_;\nnew_n36_ = new_n29_ * new_n35_;\nnew_n37_ = !new_n25_ * !new_n36_;\nnew_n38_ = !new_n33_ * new_n37_;\nnew_n39_ = new_n33_ * !new_n38_;\nnew_n40_ = pi01 * !new_n39_;\nnew_n41_ = new_n21_ * new_n33_;\nnew_n42_ = new_n29_ * new_n41_;\nnew_n43_ = new_n29_ * new_n42_;\nnew_n44_ = new_n25_ * new_n43_;\nnew_n45_ = !pi01 * new_n44_;\npo3 = new_n40_ + new_n45_;\nnew_n47_ = pi01 * new_n37_;\npo4 = new_n45_ + new_n47_;\nnew_n49_ = new_n25_ * new_n29_;\nnew_n50_ = new_n42_ * new_n49_;\nnew_n51_ = !new_n42_ * !new_n50_;\nnew_n52_ = !pi01 * new_n51_;\npo5 = new_n26_ + new_n52_;\nnew_n54_ = pi01 * pi09;\nnew_n55_ = !pi01 * pi09;\npo6 = new_n54_ + new_n55_;\nnew_n57_ = pi01 * new_n32_;\nnew_n58_ = !pi01 * new_n32_;\npo7 = new_n57_ + new_n58_;\nnew_n60_ = pi01 * pi08;\nnew_n61_ = pi01 * pi08;\npo8 = new_n60_ * new_n61_;\n\n",
            "accuracy": 0.69792,
            "objective": 42.0,
            "legalized_objective": 332.0,
            "reflection": False,
            "other_inf": "61"
        },
    ]

    p = AIGenerator()
    p.folder_path = "./temp_output"

    index = 0
    for program in programs:
        print("Starting program ", index + 1)
        print("=" * 80)
        r = Reflection()
        r.set_paras(
            aig=p,
            program=program,
            llm_api_key="provide_your_key_here",
            llm_api_endpoint="provide_your_endpoint_here",
            llm_model="gpt-3.5-turbo",
            truth_file_path=f"/yqbai/LLM4Boolean/LLM4AIG//benchmark/iwls2024/all/ex{program['other_inf']}.truth",
            output_folder="./temp_output",
            num_trial=3,
            num_iter=5,
        )
        _ = r.run()
        index += 1
