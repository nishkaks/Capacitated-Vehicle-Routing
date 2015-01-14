from numpy import *
from collections import defaultdict

def generate_random_solution(numnodes, distance, capacity, demand,numofvehicles):
    customers = list(range(2,numnodes+1))
    #random.shuffle(customers)
    routes = defaultdict(list) #[[] for vehicle in range(numofvehicles)]
    remaining_capacity = ones(numofvehicles, dtype=int) * capacity
       
    for vehicle in range(numofvehicles):
      
        # Try to feasibly add customers to the vehicle
        for id in customers:
            q = demand[id]
            # If there is remaining capacity, or it is the last vehicle
            if q <= remaining_capacity[vehicle]: 
                routes[vehicle].append(id)
                remaining_capacity[vehicle] -= q

        # Remove from the list the customers actually added
        for id in routes[vehicle]:
            customers.remove(id)
                  
        # Add the depot to the start and end of of the route
        routes[vehicle].insert(0, 1)
        routes[vehicle].append(1)
                           
    print 'remaining_capacity',remaining_capacity
    return (routes)
    
   

