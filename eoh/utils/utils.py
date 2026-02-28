import numpy as np
import math
def read_val(file):
    '''
    Args:
        file(str): truth_file_path
    Return:
        input_number
        output_number
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
    output_number = len(labels)
    input_number = math.log2(len(input))
    return input_number, output_number