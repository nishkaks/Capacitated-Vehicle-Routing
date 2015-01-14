try:
  import matplotlib.pyplot as plt
  import networkx as nx
except ImportError:
  print "install 'networkx' and 'matplotlib' for plotting"
  exit(0)
  
from collections import defaultdict

def plotsolution(numnodes,coordinates,routes):
   plt.ion() # interactive mode on
   G=nx.Graph()
   
   nodes = range(1,numnodes+1)
   nodedict = {}
   for i in nodes:
     nodedict[i] = i
   
   nodecolorlist = ['b' for i in nodes]
   nodecolorlist[0] = 'r'
     
   # nodes  
   nx.draw_networkx_nodes(G, coordinates, node_color=nodecolorlist, nodelist=nodes)
   # labels
   nx.draw_networkx_labels(G,coordinates,font_size=9,font_family='sans-serif',labels = nodedict)
   
   edgelist = defaultdict(list)
   
   colors = ['Navy','PaleVioletRed','Yellow','Darkorange','Chartreuse','CadetBlue','Tomato','Turquoise','Teal','Violet','Silver','LightSeaGreen','DeepPink', 'FireBrick','Blue','Green']
   
   for i in (routes):
     edge1 = 1
     for j in routes[i][1:]:
       edge2 = j
       edgelist[i].append((edge1,edge2))
       edge1 = edge2
       nx.draw_networkx_edges(G,coordinates,edgelist=edgelist[i],
                        width=6,alpha=0.5,edge_color=colors[i]) #,style='dashed'
   
   plt.savefig("path.png")

   plt.show()