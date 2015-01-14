from readvrplib import read_vrplib_file
from NNH import generate_random_solution
from plotsolution import plotsolution
from gurobipy import *
from collections import defaultdict
from itertools import chain, combinations
import time

# Read file name from command line argument
if len(sys.argv) < 2:
    print 'Usage: main.py filename'
    quit()

file_name = sys.argv[1]
  
def get_routecst_ksitranspose(route,numnodes):
    
    ksit  = [0] * (numnodes+1)
    routecst = 0
    routelength = len(route)
    lastcustomer = 1
    
    for i,cust in enumerate(route[1:]):
      ksit[cust] +=1      
      routecst += distance[cust][lastcustomer]
      lastcustomer = cust
          
    return routecst,ksit

def printSolution(m,NumberofVariable):
    global optimalroutes
    if m.status == GRB.status.OPTIMAL:
        print 'Optimal Objective:', m.objVal
        iter = 0
        for r in range(NumberofVariable):
            if y[r].x > 0.0001:
               optimalroutes[iter] = routes[r]
               iter+=1
               print r, y[r].x
    else:
        print 'No solution'
    return optimalroutes
        
def get_fiq(i,q):

    if q < mindemand or q not in qlist:
      prev[i,q] = [-99,-99] # dummy
      return float('infinity');
    elif fiq[i,q] != float('infinity'):
      return fiq[i,q]
    elif q == demand[i]:
      prev[i,q] = [1,q-demand[i]]
      fiq[i,q] = c[1][i]      
      return c[1][i]
    else:
      mintemp = float('infinity')
      minj = 0
      for j in range(2,numnodes+1):
        if j != i:
          temp = get_fiq(j,q-demand[i]) + c[j][i]
          #print i,j,q,demand[i],prev[j,q-demand[i]][0] 
          if i != prev[j,q-demand[i]][0] and  temp < mintemp:  # the first condition(remove 2-loop) might not be right, Ignores some solutions
            mintemp = temp
            minj = j
      fiq[i,q] = mintemp
       
      if minj != 0:
        prev[i,q] = [minj,q-demand[i]]
      else: 
        prev[i,q] = [-99,-99] # dummy
    
      #fiq[i,q] = min((get_fiq(j,q-demand[i]) + c[j][i] for j in range(2,numnodes+1) if j != i)); Not able to extract j here
      return fiq[i,q]       

def reconstructpath(i,q):
   if fiq[i,q] == float('infinity'):
     return []
   elif q == 0:
     return [1]
   else:
     #print i,q,prev[i,q]
     return reconstructpath(prev[i,q][0], prev[i,q][1]) + [i]
     
(numnodes, coordinates, distance, capacity, demand,numofvehicles) = read_vrplib_file(file_name)
#print distance

start_time = time.clock()


(routes) = generate_random_solution(numnodes, distance, capacity, demand,numofvehicles)
initialroutecount =  len(routes)

ksitranspose = defaultdict(list)
routecost    = defaultdict(float)
for r in range(initialroutecount):
  routecost[r],ksitranspose[r] = get_routecst_ksitranspose(routes[r],numnodes)

#print 'ksitranspose',ksitranspose
#print 'routecost',sum(routecost)

#plotsolution(numnodes,coordinates,routes);

# Model
master = Model("MASTER")
master.modelSense = GRB.MINIMIZE 

# Create decision variables 
y = {}
for r in range(initialroutecount):
    y[r] = master.addVar(lb=0.0, vtype=GRB.CONTINUOUS,obj=routecost[r],name='y_%s' % (r))
    
# Update model to integrate new variables
master.update()

# constraints
custconstr = {}
for i in range(2,numnodes+1):
    custconstr[i] = master.addConstr(
      quicksum(ksitranspose[r][i] * y[r] for r in range(initialroutecount)) >= 1,
               'cust_%s' % (i))
               
vehiclecosntr = master.addConstr(
   -1 * quicksum(y[r] for r in range(initialroutecount)) >= - numofvehicles,
               'vehicle' )

# Solve

master.update()

mindemand = min(demand[i] for i in range(2,numnodes+1))

#Generate the possible values of q 
tempq = list(demand.values())
tempq1 = list(demand.values())
stuff = list(demand.values())
stuff.sort()
tempq.sort()
tempq1.sort()
#delete 0
del stuff[0]
del tempq[0] 
del tempq1[0] 
#print 'tempq',tempq

#print 'stuff',stuff 

for i in range(len(tempq)):
   if sum(stuff) > capacity:
     stuff.pop()
   else:
     break
    
print 'stuff2',stuff,sum(stuff)

for L in range(2,len(stuff)+1):
  for subset in combinations(tempq1, L):
    tempq.append(sum(list(subset)))
# get distinct values
qlist1 = list(set(tempq))
#print 'qlist1',qlist1
# get q which is less than the capacity   
qlist = [x for x in qlist1 if x <= capacity]
print qlist

iter = 1
temp = []
while (iter < 100): #Arbitrary for small instances
    master.optimize()
    #printSolution(master)
    pi =[]
    pi = [c.Pi for c in  master.getConstrs()] #  dual variables
    theta = pi.pop()
    pi.insert(0, 0)
    
    c={}
    c = [[0 for col in range(numnodes+1)] for row in range(numnodes+1)]
    for i in range(1,numnodes+1):
      for j in range(1,numnodes+1):
        c[i][j] = distance[i][j] - pi[j-1]
     
    #Dynamic programming 
    
    fiq = defaultdict(float)
    prev = defaultdict(list)
    cgroutes = []
    
    # initial conditions for fiq
    for q in qlist:
      for i in range(2,numnodes+1):
        fiq[i,q] = float('infinity')
    
    for q in qlist:
      for i in range(2,numnodes+1):
         #print i,q
         fiq[i,q] =  get_fiq(i,q)         
    
    fiq0 = defaultdict(float)
    for q in qlist:
      for i in range(2,numnodes+1):
        fiq0[i,q] = fiq[i,q] + c[i][1] 
    
    print 'print fiq0, path'
    testcount = 0
    for q in qlist:
      for i in range(2,numnodes+1):
        if fiq0[i,q] < - theta:  
          temp = reconstructpath(i,q)
          temp.append(1) # append depot(1) at the end of the routes
          if temp[::-1] not in cgroutes:   # check for symmetric routes in an iteration of cg
            cgroutes.append(temp)
            #print fiq0[i,q],i,q,cgroutes[testcount]
            testcount +=1       
     
    # Column generation
    numcols = len(cgroutes)
    
    if numcols == 0:
      print 'numcols 0'
      break    
    
    oldroutecount =  len(routes)
    K=oldroutecount 
    print 'old', len(routecost)
    for i in cgroutes:
      routecost[K],ksitranspose[K] = get_routecst_ksitranspose(i,numnodes)
      routes[K] = i
    
      # add new columns to the master problem
      col = Column()
      for i in range(2,numnodes+1):
        col.addTerms(ksitranspose[K][i], custconstr[i])
      col.addTerms(-1,vehiclecosntr)
      y[K] = master.addVar(lb=0.0, vtype=GRB.CONTINUOUS,obj=routecost[K], column=col,name='y_%s' % (K))
      master.update()     
      K +=1
    
      
    print 'new numroutes', len(routecost)
    print 'new numvars' ,master.numVars
    iter +=1
    
master.write("VRP"+".lp")

#print 'K,master.numVars',K,master.numVars

# solve IP 
# Set variable type back to binary
NumberofVariable = len(routecost)
for i in range(NumberofVariable):
    y[i].vType = GRB.BINARY
    
master.update()   
master.optimize()

optimalroutes = defaultdict(list)
optimalroutes = printSolution(master,NumberofVariable)

print optimalroutes

print "Time taken                  = ",time.clock() - start_time, "seconds"

#plot optimal routes
plotsolution(numnodes,coordinates,optimalroutes);

raw_input("press [enter] to continue")

