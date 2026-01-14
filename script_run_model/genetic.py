from random import randint, random
from operator import add
from functools import reduce

def individual(length, min, max):
    'Create a member of the population.'
    return [ randint(min,max) for x in range(length) ]

def population(count, length, min, max):
    """
    Create a number of individuals (i.e. a population).

    count: the number of individuals in the population
    length: the number of values per individual
    min: the minimum possible value in an individual's list of values
    max: the maximum possible value in an individual's list of values

    """
    return [ individual(length, min, max) for x in range(count) ]

def fitness(individual, target):
    """
    Determine the fitness of an individual. Higher is better.

    individual: the individual to evaluate
    target: the target number individuals are aiming for
    """
    sum = reduce(add, individual, 0)
    return abs(target-sum)

def grade(pop, target):
    'Find average fitness for a population.'
    summed = reduce(add, (fitness(x, target) for x in pop))
    return summed / (len(pop) * 1.0)

def evolve_pop(pop,fitnessid,retain=0.2, random_select=0.05, mutate=0.01):
    """Evolution algorithm: select best performers, apply crossover, mutation.
    
    fitnessid: 0=Nash-Sutcliffe (maximize), 1=RMSE (minimize), 2=MAE (minimize)
    retain: fraction of population kept as parents for next generation
    random_select: fraction of weaker individuals kept for genetic diversity
    mutate: mutation rate for random parameter changes
    """
    # select the type of fitness
    if fitnessid==0:
        graded = [ (x.Eff, x.chromosomes) for x in pop]
        Eff_list= [ x[0] for x in sorted(graded,reverse=True)]
        graded = [ x[1] for x in sorted(graded,reverse=True)]
    elif fitnessid==1:
        graded = [ (x.RMSE, x.chromosomes) for x in pop]
        Eff_list= [ x[0] for x in sorted(graded,reverse=False)]
        graded = [ x[1] for x in sorted(graded,reverse=False)]
    elif fitnessid==2:
        graded = [ (x.MAE, x.chromosomes) for x in pop]
        Eff_list= [ x[0] for x in sorted(graded,reverse=False)]
        graded = [ x[1] for x in sorted(graded,reverse=False)]

    retain_length = int(len(graded)*retain)
    parents = graded[:retain_length]
    # randomly add other individuals to
    # promote genetic diversity
    for individual in graded[retain_length:]:
        if random_select > random():
            parents.append(individual)
    # mutate some individuals of a small random portion of the population
    for individual in parents:
        if mutate > random():
            pos_to_mutate = randint(0, len(individual)-1)
            # this mutation is not ideal, because it
            # restricts the range of possible values,
            # but the function is unaware of the min/max
            # values used to create the individuals,
            individual[pos_to_mutate] = randint(
                min(individual), max(individual))
    # crossover parents to create children
    parents_length = len(parents)
    desired_length = len(pop) - parents_length
    children = []
    while len(children) < desired_length:
        male = randint(0, parents_length-1)
        female = randint(0, parents_length-1)
        if male != female:
            male = parents[male]
            female = parents[female]
##            # Single-point crossover
##            half = int(len(male) / 2)
##            half+=randint(0,1)
##            child = male[:half] + female[half:]
            # Two-point crossover
            aquarter=int(len(male) / 4)
            half = int(len(male) / 2)+ aquarter
            child = male[:aquarter] + female[aquarter:half] + male[half:]

            children.append(child)
    parents.extend(children)
    return parents, Eff_list, graded


def evolve(pop, target, retain=0.2, random_select=0.05, mutate=0.01):

    graded = [ (fitness(x, target), x) for x in pop]
    graded = [ x[1] for x in sorted(graded)]
    retain_length = int(len(graded)*retain)
    parents = graded[:retain_length]
    # randomly add other individuals to
    # promote genetic diversity
    for individual in graded[retain_length:]:
        if random_select > random():
            parents.append(individual)
    # mutate some individuals
    for individual in parents:
        if mutate > random():
            pos_to_mutate = randint(0, len(individual)-1)
            # this mutation is not ideal, because it
            # restricts the range of possible values,
            # but the function is unaware of the min/max
            # values used to create the individuals,
            individual[pos_to_mutate] = randint(
                min(individual), max(individual))
    # crossover parents to create children
    parents_length = len(parents)
    desired_length = len(pop) - parents_length
    children = []
    while len(children) < desired_length:
        male = randint(0, parents_length-1)
        female = randint(0, parents_length-1)
        if male != female:
            male = parents[male]
            female = parents[female]
            half = int(len(male) / 2)
            half+= int(random)
            child = male[:half] + female[half:]
            children.append(child)
    parents.extend(children)
    return parents
