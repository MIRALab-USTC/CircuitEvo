# file_name=(ex00 ex01 ex02 ex03 ex04 ex05 ex06 ex07 ex08 ex09)
file_name=(ex00 ex01 ex02 ex03 ex04 ex05 ex06 ex07 ex08 ex09)
# before_optimize_legalize_nooptimize
for file in "${file_name[@]}"
do
    nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.01 --before_legalized_optimize > ./out/motivation_test_before_opt_legalize_noopt_${file}_threshold_1.out 2>&1 &
    sleep 10s
    nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.05 --before_legalized_optimize > ./out/motivation_test_before_opt_legalize_noopt_${file}_threshold_5.out 2>&1 &
    sleep 10s
    # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.1 > ./out/motivation_test_${file}_threshold_10.out 2>&1 &
    # sleep 10s
    # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.3 > ./out/motivation_test_${file}_threshold_30.out 2>&1 &
    # sleep 10s
    # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.5 > ./out/motivation_test_${file}_threshold_50.out 2>&1 &
    # sleep 10s
done

# before_nooptimize_legalize_nooptimize
# for file in "${file_name[@]}"
# do
#     nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.01 > ./out/motivation_test_${file}_before_noopt_legalize_noopt_threshold_1.out 2>&1 &
#     sleep 10s
#     nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.05 > ./out/motivation_test_${file}_before_noopt_legalize_noopt_threshold_5.out 2>&1 &
#     sleep 10s
#     # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.1 > ./out/motivation_test_${file}_threshold_10.out 2>&1 &
#     # sleep 10s
#     # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.3 > ./out/motivation_test_${file}_threshold_30.out 2>&1 &
#     # sleep 10s
#     # nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/all/${file}.truth --num 1000 --threshold 0.5 > ./out/motivation_test_${file}_threshold_50.out 2>&1 &
#     # sleep 10s
# done
# nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/small_truth/ex16.truth > ./out/motivation_test_ex16.out 2>&1 &
# wait
# nohup python motivation_test.py --truth_file_path /yqbai/LLM4Boolean/LLM4AIG/benchmark/iwls2022/small_truth/ex35.truth > ./out/motivation_test_ex35.out 2>&1 &