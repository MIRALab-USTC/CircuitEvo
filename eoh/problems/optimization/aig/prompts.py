import json
import os
import re
class GetPrompts():
    def __init__(self):
        with open('./prompts/prompt_task.txt', 'r') as f:
            self.prompt_task = f.read()
        with open('./prompts/prompt_evolution.txt', 'r') as f:
            self.prompt_evolution = f.read()
        with open('./prompts/prompt_other.txt', 'r') as f:
            self.prompt_other_inf = f.read()

    def get_task(self):
        return self.prompt_task

    def get_evolution(self):
        def extract_between(start_label, next_label):
            pattern = rf"{start_label}:\s*(.*?)(?={next_label}:|$)"
            match = re.search(pattern, self.prompt_evolution, re.DOTALL)
            return match.group(1).strip() if match else None

        prompt_evolution = {}
        prompt_evolution['e1'] = extract_between("e1", "e2")
        prompt_evolution['e2'] = extract_between("e2", "m1")
        prompt_evolution['m1'] = extract_between("m1", "m2")
        prompt_evolution['m2'] = extract_between("m2", "e1")  # 假设后面是循环的，否则就提到结尾
        return prompt_evolution
    
    def get_other_inf(self):
        return self.prompt_other_inf
