from readvrplib import read_vrplib_file
from NNH import generate_random_solution
from plotsolution import plotsolution
from collections import defaultdict
from itertools import chain, combinations
import sys
import os

#Read file name from command line argument
if len(sys.argv) < 2:
    print 'Usage: maingams.py filename'
    quit()

file_name = sys.argv[1]
  
def get_routecst_ksitranspose(route,numnodes):
    
    ksit  = [1e-250] * (numnodes+1)  # GAMS does not like zeros!!
    routecst = 0
    routelength = len(route)
    lastcustomer = 1
    
    for i,cust in enumerate(route[1:]):
      ksit[cust] +=1      
      routecst += distance[cust][lastcustomer]
      lastcustomer = cust
          
    return routecst,ksit

def getOptimalRoutes():
    global optimalroutes
    iter = 0    
    for rec in t4.out_db["y"]:
      if rec.level > 0.0001:
        optimalroutes[iter] = routes[int(rec.keys[0])]
        iter+=1

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
          if i != prev[j,q-demand[i]][0] and  temp < mintemp:  # (remove 2-loop) 
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
     return reconstructpath(prev[i,q][0], prev[i,q][1]) + [i]
     
(numnodes, coordinates, distance, capacity, demand,numofvehicles) = read_vrplib_file(file_name)

(routes) = generate_random_solution(numnodes, distance, capacity, demand,numofvehicles)
initialroutecount =  len(routes)

ksitranspose = defaultdict(list)
routecost    = defaultdict(float)
for r in range(initialroutecount):
  routecost[r],ksitranspose[r] = get_routecst_ksitranspose(routes[r],numnodes)

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

for i in range(len(tempq)):
   if sum(stuff) > capacity:
     stuff.pop()
   else:
     break
    
for L in range(2,len(stuff)+1):
  for subset in combinations(tempq1, L):
    tempq.append(sum(list(subset)))
# get distinct values
qlist1 = list(set(tempq))
# get q which is less than the capacity   
qlist = [x for x in qlist1 if x <= capacity]
#print qlist

# Model

from gams import *
import sys

def get_model_text():
    return '''
  Set i        customers;

  Scalar K  Number of vehicles;
  
  Set
       r       possible routes /0*15000/
       rr(r)   dynamic set of routes
          ;

     Parameters
       rc(r)   Cost for each route
       ksi(r,i)   Number of times a customer is visited in each route;

$gdxin vrpdatabase
$load i K rr rc ksi

  %currvariabletype% Variable
       y(r)  Route selected in the optimal solution;

  variable
       z cost;

  y.up(r) = 1;


  Equations
       cost        define objective function
       cover(i)    All customer nodes are visited
       vehiclenumber   satisfy demand at market j ;

  cost ..        z  =e=  sum(rr, rc(rr)*y(rr)) ;

  cover(i) ..   sum(rr, ksi(rr,i) * y(rr))  =g=  1 ;

  vehiclenumber ..   -1 * sum(rr, y(rr))  =g=  - K ;

  Model setpartitionvrp /all/ ;
  
 Solve setpartitionvrp using %problemtype% minimizing z ;

 
 '''

if __name__ == "__main__":
    ws = GamsWorkspace()

    customers   = range(2,numnodes+1)
    customers = map(str,customers)
    initialroutes = range(initialroutecount)
    initialroutes = map(str,initialroutes)
    
    
    db = ws.add_database('vrpdatabase')
       
    i = GamsSet(db, "i", 1, "customers")
    for c in customers:
        i.add_record(c)
    
    rr = GamsSet(db, "rr", 1, "routes")
    for i in initialroutes:
        rr.add_record(i)
        
    rc = GamsParameter(db, "rc", 1, "Cost for each route")
    for r in initialroutes:
        rc.add_record(r).value = routecost[int(r)]
        #print routecost[int(r)]
    
    ksi = GamsParameter(db, "ksi", 2, "Number of times a customer is visited in each route")
    for r in initialroutes:
      for c in customers:
        ksi.add_record((r,c)).value =  ksitranspose[int(r)][int(c)]
     
    K = GamsParameter(db, "K", 0, "number of vehicles available")
    K.add_record().value = numofvehicles
    
    t4 = GamsJob(ws, source=get_model_text())
    opt = GamsOptions(ws)
    
    opt.defines["gdxincname"] = db.name
    opt.defines["currvariabletype"] = "positive"
    opt.defines["problemtype"] = "lp" 
    opt.all_model_types = "Gurobi"
    
    #db.export("E:/Study/spring2013/635/project/vehicle routing/720 code/result.gdx")
 

iter = 1
while (iter < 100):
    t4.run(opt, databases = db,output=sys.stdout)

    pi =[]
    pi = [c1.marginal for c1 in t4.out_db["cover"]]
    theta = [c2.marginal for c2 in t4.out_db["vehiclenumber"]]
    pi.insert(0, 0)
    print "theta", theta[0]
    
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
         fiq[i,q] =  get_fiq(i,q)
         
    
    fiq0 = defaultdict(float)
    for q in qlist:
      for i in range(2,numnodes+1):
        fiq0[i,q] = fiq[i,q] + c[i][1] 
    
    print 'print fiq0, path'
    testcount = 0
    for q in qlist:
      for i in range(2,numnodes+1):
        if fiq0[i,q] < - theta[0]:  
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
      rr.add_record(str(K))
      rc.add_record(str(K)).value = routecost[K]
      for c in customers:
        ksi.add_record((str(K),c)).value =  ksitranspose[K][int(c)]
        
      K +=1
    
    iter +=1
    

# solve IP 

# Set variable type back to binary
opt.defines["currvariabletype"] = "binary"
opt.defines["problemtype"] = "mip"
opt.optcr = 0.0  # Solve to optimality 
    
t4.run(opt, databases = db,output=sys.stdout)

optimalroutes = defaultdict(list)
optimalroutes = getOptimalRoutes()

print optimalroutes

#plot optimal routes
plotsolution(numnodes,coordinates,optimalroutes);

raw_input("press [enter] to continue")