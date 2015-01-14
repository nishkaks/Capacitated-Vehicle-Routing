from math import sqrt
import re

def read_vrplib_file(file_path):

   #returns instance_data = (numnodes, coordinates, distance, capacity, demand,numofvehicles)
  
   file = open(file_path, 'r')
   
   for line in file:
   
      if line.startswith('NAME'):
        file_name = line.split().pop()
        #matches = re.search('.+\-.+\-k(.+)$',file_name) 
        #numofvehicles = int(matches.group(1))
        numofvehicles = int(re.match('.*?([0-9]+)$', file_name).group(1))        
      
      if line.startswith('CAPACITY'):
        capacity = int(line.split().pop())
        
      if line.startswith('DIMENSION'):
        numnodes = int(line.split().pop())
        nodes = range(1,numnodes+1)
        
      if line.rstrip() == 'DEMAND_SECTION':
        demand = {}
        for i in range(1,numnodes+1):
          line = file.next()
          demand[i] = int(line.split().pop())
         
        #print demand
        #print '--------'
      
      if line.rstrip() == 'NODE_COORD_SECTION':
        distance = [[0 for col in range(numnodes+1)] for row in range(numnodes+1)]
        coordinates = {}
        for i in range(1,numnodes+1):
          line = file.next()
          coordinates[i] = [int(line.split()[1]),int(line.split()[2])]
        #print coordinates
        #print '--------'
          
        # Calculate distances between vertices
        for i in range(1,numnodes+1):
           for j in range(i,numnodes+1):
              if i == j:
                distance[i][j] = 0
              else:
                dist = round(sqrt(((coordinates[i][0] - coordinates[j][0])**2) + ((coordinates[i][1] - coordinates[j][1])**2)))
                distance[i][j] = dist
                distance[j][i] = dist
                
        #print distance
        #print '--------'
        
   file.close()
   instance_data = (numnodes, coordinates, distance, capacity, demand,numofvehicles)
   return instance_data
   



