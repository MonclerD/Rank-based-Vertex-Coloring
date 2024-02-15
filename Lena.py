from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n = comm.Get_size()

ROUND = 0
COLOR = 1
ROVER = 2
FIN = 3

msg = np.array([-1, -1, -1, -1])
children = [[3, 4, 7], [], [6], [2], [], [1], [], [5]]
parents = [0, 5, 3, 0, 0, 7, 2, 0]

finished, round_end = set(), set()
childs = children[rank]
parent = parents[rank]
childs = set(childs)
neighs, received = set(), set()
colors = {}

A = np.array([[0,0,0,1,1,0,0,1],
              [0,0,0,0,0,1,0,1],
              [0,0,0,1,1,0,1,0], 
              [1,0,1,0,1,0,1,0],
              [1,0,1,1,0,1,0,1],
              [0,1,0,0,1,0,0,1],
              [0,0,1,1,0,0,0,0],
              [1,1,0,0,1,1,0,0]], dtype=int)
neighbors = A[rank,:]
s = []
for i in range (0,n):
    if neighbors[i] == 1:
        neighs.add(i)
        colors.update([(i,-1)])
        
count = n - 1
round_num = 0
color = -1
changed = False
if 0 in neighs: 
    colors[0] = 0
    
if rank == 0:
    color = 0
    
while count > 0:
    neighs_over, childs_end, round_over = False, False, False
    round_end.clear()
    
    if rank == 0:
        round_num = round_num + 1
        msg[0], msg[1], msg[2] = rank, ROUND, round_num
        for child in childs:
            comm.send(msg, dest=child, tag=ROUND)
    
    while not round_over:
        msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        sender, typ, roun, neigh_color=msg[0], msg[1], msg[2], msg[3]
        msg[0] = rank
        if typ == ROUND:  
            if len(childs) != 0:
                for child in childs:
                    comm.send(msg, dest=child, tag=ROUND)
            else:
                childs_end = True
            if rank == roun:
                for key,value in colors.items():#find an unused color
                    s.append(value)
                s.sort()
                found = False
                for i in range(1,len(s)):
                    if s[i] - s[i-1] > 1:
                        color = s[i-1] + 1
                        found = True
                        break 
                if not found:
                    color = max(s) + 1
                colors[rank] = color
                msg[1] = COLOR
                msg[3] = color
                for node in neighs:
                    comm.send(msg, dest=node, tag=COLOR)
                changed = True
                
            if len(childs) == 0 and roun not in neighs:
                msg[1] = ROVER
                comm.send(msg, dest=parent, tag=ROVER)
                round_over = True
                
        elif typ == COLOR:
            colors[sender] = neigh_color
            changed = True
            if childs_end:
                if rank != 0:
                    msg[1] = ROVER
                    comm.send(msg, dest=parent, tag=ROVER)
                round_over = True
            
        elif typ == ROVER:
            round_end.add(sender)
            if round_end == childs:
                childs_end = True
                if roun == rank:
                    if changed:
                        round_over = True
                elif roun in neighs:
                    if changed:
                        round_over = True
                else:  
                    round_over = True
                if rank != 0:
                    comm.send(msg, dest=parent, tag=ROVER)
    count = count - 1

print("rank: {}, color: {}".format(rank,color))
