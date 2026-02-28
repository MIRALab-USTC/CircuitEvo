import heapq

def best_population(population):
    best_pop = min(population, key=lambda x: x["legalized_objective"])
    return best_pop

def population_management(pop, size, local_search=False):
    # if local_search:
        # choose by the acc
    pop = [individual for individual in pop if individual['accuracy'] is not None]
    if size > len(pop):
        size = len(pop)
    # reserve the pop with the same objective
    # pop_new = heapq.nsmallest(size, pop, key=lambda x: x['objective'])
    # return pop_new

    ##### delete the pop with the same objective
    unique_pop = [] 
    unique_acc = []
    unique_objective = []
    for individual in pop:
        if individual['accuracy'] not in unique_acc or individual['legalized_objective'] not in unique_objective:
            unique_pop.append(individual)
            unique_acc.append(individual['accuracy'])
            unique_objective.append(individual['legalized_objective'])
    # Delete the worst individual
    pop_new = heapq.nsmallest(size, unique_pop, key=lambda x: x['legalized_objective'])
        # select size elements from the unique_pop based on x['objective']
        # pop_new = heapq.nlargest(size, unique_pop, key=lambda x: x['legalized_objective'])
    # else:
    #     # choose only by the node number
    #     pop = [individual for individual in pop if individual['objective'] is not None]
    #     if size > len(pop):
    #         size = len(pop)
    #     # reserve the pop with the same objective
    #     # pop_new = heapq.nsmallest(size, pop, key=lambda x: x['objective'])
    #     # return pop_new

    #     ##### delete the pop with the same objective
    #     unique_pop = [] 
    #     unique_objectives = []
    #     for individual in pop:
    #         if individual['objective'] not in unique_objectives:
    #             unique_pop.append(individual)
    #             unique_objectives.append(individual['objective'])
    #     # Delete the worst individual
    #     # pop_new = heapq.nsmallest(size, pop, key=lambda x: x['objective'])
    #     # select size elements from the unique_pop based on x['objective']
    #     pop_new = heapq.nsmallest(size, unique_pop, key=lambda x: x['objective'])
    return pop_new