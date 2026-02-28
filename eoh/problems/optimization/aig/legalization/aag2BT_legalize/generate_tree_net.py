from .aag2Dict import Aig2Dict, create_tree_from_node_dict



if __name__ == '__main__':
    aigfile = '.aag'
    dict_main = Aig2Dict(aigfile)
    main_aig = create_tree_from_node_dict(dict_main.node_dict)

    # 获取分类错误样本的索引
    outbits , inbits = model.out_dim, model.in_dim
    # outbits, inbits = 2,3
    test_set = truth_table_datasets.TruthTableDataset(random_data=False, input_nums=inbits, truth_table_file = truth_table_path, truth_flip=True)   
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=2 ** inbits, shuffle=False, pin_memory=True, drop_last=False)
    misclassified_truth_label1, misclassified_truth_label0 = get_misclassified_samples(model, test_set, test_loader)
    # misclassified_truth_label1, misclassified_truth_label0 = torch.tensor([[1,1,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]).T, torch.tensor([[1,1,1,1,1,1,1,1], [1,1,1,1,0,1,1,1]]).T

    # test = connect_nodes(main_aig, [1,2,3,4], [0,0,0,0])

    # 根据索引生成对应的有向无环图
    sub_aig_and_list = []
    sub_aig_or_list = []
    sub_aig_and_inv_list = []
    sub_aig_or_inv_list = []
    for i in range(outbits):
        misclassified_truth_label1_cut = misclassified_truth_label1[:,i]
        misclassified_truth_label0_cut = misclassified_truth_label0[:,i]
        sub_aig_and,  sub_aig_or, out1, out0 = generate_graph_from_index(main_aig, misclassified_truth_label1_cut, misclassified_truth_label0_cut, inbits)
        sub_aig_and_list.append(sub_aig_and)
        sub_aig_or_list.append(sub_aig_or)
        sub_aig_and_inv_list.append(out1)
        sub_aig_or_inv_list.append(out0)

    # draw_dig(main_aig, filename="/difflogic/exp6/legalization/main_aig1.png")
    # main_out_num = [6, 5]
    # main_out_inv = [1, 0]
    main_out_num = dict_main.out_node_num
    main_out_inv = dict_main.out_invs

    # 合并两个图
    if sum(sub_aig_and_list) == 0 and sum(sub_aig_or_list) == 0:
        aig_path, _ = os.path.splitext(model_path)
        aig_path = aig_path + '.txt'
        write_aig(main_aig, main_out_num, main_out_inv, inbits, outbits, filename=aig_path)
        aigtoaig_cmd = f"/difflogic/aiger/aigtoaig {aig_path} {aig_path[:-4]}"+".aig"
        os.system(aigtoaig_cmd)
    else:
        for i in range(outbits):
            if sub_aig_and_list[i] > 0 or sub_aig_or_list[i] > 0:
                main_aig, main_out_num[i], main_out_inv[i] = merge_graphs(main_aig, int(main_out_num[i]), int(main_out_inv[i]), sub_aig_and_list[i], sub_aig_or_list[i], sub_aig_and_inv_list[i], sub_aig_or_inv_list[i])
        aig_path, _ = os.path.splitext(model_path)
        aig_path = aig_path+'_legal.txt'
        write_aig(main_aig, main_out_num, main_out_inv, inbits, outbits, filename=aig_path)
        aigtoaig_cmd = f"/difflogic/aiger/aigtoaig {aig_path} {aig_path[:-4]}"+".aig"
        os.system(aigtoaig_cmd)

    # draw_dig(main_aig, filename="/difflogic/exp6/legalization/main_aig2.png")

    # 最终得到的图结构
    # print(final_graph)