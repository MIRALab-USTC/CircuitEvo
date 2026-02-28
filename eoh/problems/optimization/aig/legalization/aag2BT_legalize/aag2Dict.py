import torch
import numpy as np
import math
import sys
import os

import networkx as nx
class aig_node():
    def __init__(self, and_num = None, left_child = None, right_child = None, left_inv = None, right_inv = None):
        self.and_num = and_num
        self.left_child = left_child
        self.right_child = right_child
        self.left_inv = left_inv
        self.right_inv = right_inv
        
class Aig2Dict():
    def __init__(self, aigfile=None):
        self.aigfile = aigfile

        # 打开aigfile，读入文件的第一行，按顺序提取五个数字并填入对应变量
        with open(self.aigfile, 'r') as file:
            [self.total_nodes, self.I, self.L, self.O, self.and_gates] = self.read_header(file)

            # 根据self.I, 跳过接下来的I行
            for _ in range(self.I):
                next(file)

            # 根据self.O, 处理接下来的O行，每行代表一个输出的编号
            self.out_node_num, self.out_invs = self.process_output_lines(file)  

            # 根据self.and_gates, 处理接下来的A行，每行放入一个aignode
            self.node_dict = {}
            self.process_and_lines(file)

    def process_output_lines(self, file):
        # 处理接下来的O行，每行代表一个输出的编号
        out_node_num = torch.zeros(self.O)
        out_invs = torch.zeros(self.O)
        for i in range(self.O):
            line = next(file)
            out_invs[i] = int(line) % 2  # 判断奇偶
            out_node_num[i] = int(line) // 2
        return out_node_num, out_invs

    def process_and_lines(self, file):
        # 处理接下来的A行，每行放入一个aignode
        for line in file:
            A, B, C = map(int, line.split())
            left_child = B // 2
            inv1 = B % 2
            right_child = C // 2
            inv2 = C % 2
            node_num = A // 2

            # 将它们分别处理，并写入写入结构体node
            aignode = aig_node()
            aignode.left_child = int(left_child)
            aignode.right_child = int(right_child)
            aignode.left_inv = inv1
            aignode.right_inv = inv2
            aignode.and_num = node_num

            # node写入字典，layer固定为1，[node]编号为单调递增的正整数即可
            if 1 not in self.node_dict:
                self.node_dict[1] = {}
            self.node_dict[1][node_num] = aignode

    def read_header(self, file):
        # 读入文件第一行，将五个数字分别写入和返回
        line = file.readline()
        total_nodes, I, L, O, and_gates = map(int, line.split()[1:])
        return total_nodes, I, L, O, and_gates

def create_tree_from_node_dict(node_dict):
    # node_dict[layer][unit]=node
    # node.and_num = N
    # node.left_child right_child left_inv right_inv are int
    # for node in node_dict, add node information into G
    G = nx.DiGraph()
    existing_nodes = {}
    for layer in node_dict:
        for unit in node_dict[layer]:
            node = node_dict[layer][unit]
            if node.and_num not in existing_nodes:
                G.add_node(node.and_num)
                existing_nodes[node.and_num] = True
            # 合并两个child，批量处理，合并两个inv，批量处理
            child = [node.left_child, node.right_child]
            inv = [node.left_inv, node.right_inv]
            # 对于每个child，如果不存在，则添加节点
            for i in range(2):
                if child[i] not in existing_nodes:
                    G.add_node(child[i])
                    existing_nodes[child[i]] = True
            # 添加边，注意也要添加边的inv信息，作为inv添加
                if child[0] != child[1]:
                    G.add_weighted_edges_from([(node.and_num,child[i],inv[i])], weight='inv')
                else:
                    G.add_weighted_edges_from([(node.and_num,child[i],inv[1]+inv[0])], weight='inv')
                    break
               
    return G    
if __name__ == '__main__':
    aigfile = '.aag'
    dict_main = Aig2Dict(aigfile)
    main_aig = create_tree_from_node_dict(dict_main.node_dict)