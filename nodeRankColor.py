from mpi4py import MPI
import numpy as np 

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n = comm.Get_size()

#states
UNDEC = 0
INCOV = 1
NOTCOV = 2

# message types
ROUND = 0
DATA = 1
ROVER = 2
FINISHED = 3
TERMINATE = 4

# sender, type, round number, sender state
msg = np.array([-1, -1, -1, -1])

A = np.array([[0,0,0,1,1,0,0,1],
              [0,0,0,0,0,1,0,1],
              [0,0,0,1,1,0,1,0], 
              [1,0,1,0,1,0,1,0],
              [1,0,1,1,0,1,0,1],
              [0,1,0,0,1,0,0,1],
              [0,0,1,1,0,0,0,0],
              [1,1,0,0,1,1,0,0]], dtype=int)

#sender, type, round number, sender state
msg = [-1, -1, -1, -1]
children = [[3, 4, 7], [], [6], [2], [], [1], [], [5]]
parents = [0, 5, 3, 0, 0, 7, 2, 0]

#children = [[3, 4, 7], [], [], [6], [], [1], [2], [5]]
#parents = [0, 5, 6, 0, 0, 7, 3, 0]
#children = [[3, 4, 7], [], [], [2,6], [], [], [], [1,5]]
#parents = [0, 7, 3, 0, 0, 7, 3, 0]

child = children[rank]
parent = parents[rank]
childs = set(child)
neighs, neighs_rcvd, rover_rcvd, finish_rcvd = set(), set(), set(), set()
removed_neighs = set()
removed_childs = set()
states = ['UNDEC', 'INCOV', 'NOTCOV']


for i in range (0,n): #identify neighbors
    if A[rank,i] == 1:
        neighs.add(i)
        
currneighs = neighs.copy()
currchilds = childs.copy()
round_num = 0
max_count = 4
state = UNDEC
finished_childs, finished_all, terminated = False, False, False

while not terminated:
    round_over, neighs_over, childs_over = False, False, False
    neighs_sent = False
    rover_rcvd.clear()
    neighs_rcvd.clear()
    removed_neighs.clear()
    removed_childs.clear()
    
    if rank == 0:
        msg[0], msg[1], msg[2] = rank, ROUND, round_num
        for child in currchilds:
            comm.send(msg, dest=child, tag=ROUND)
        if state==UNDEC:
            msg[1], msg[3] = DATA, state
            for node in currneighs:
                comm.send(msg, dest=node, tag=DATA)
            neighs_sent = True
        else:
            neighs_over = True
            neighs_sent = True
    while not round_over:
        msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        sender, typ, roun, ne_state = msg[0], msg[1], msg[2], msg[3]
        msg[0] = rank
        if typ == ROUND: #active node ROUND recieved
            if len(currchilds) != 0: #intermediate node
                for child in currchilds:
                    comm.send(msg, dest=child, tag=ROUND)
            else: #leaf node
                childs_over = True
            if state != UNDEC: #node already determined
                neighs_over = True
                neighs_sent = True
                if len(childs)==0:
                    childs_over = True
                    msg[1] = ROVER
                    comm.send(msg, dest=parent, tag=ROVER)
                    round_over = True
                else:
                    neighs_sent, neighs_over = True, True
            else: #node undetermined
                if rank > max(currneighs):
                    state = INCOV
                    round_saved = roun
                    if len(currchilds) == 0:
                        childs_over = True
                        finished_all = True
                        msg[1] = FINISHED 
                        comm.send(msg,dest=parent,tag=FINISHED)
                msg[1], msg[3] = DATA, state
                for node in currneighs:
                    comm.send(msg, dest=node, tag=DATA)
                    neighs_sent = True
                if neighs_over and childs_over:
                    if rank != 0:
                        msg[1] = ROVER
                        comm.send(msg, dest=parent, tag=ROVER)
                        round_over = True
        elif typ == DATA: #DATA received
            neighs_rcvd.add(sender)
            if ne_state == INCOV or ne_state == NOTCOV:
                if sender in currneighs:
                    removed_neighs.add(sender)
                    
            if neighs_rcvd == currneighs:
                neighs_over = True
                if neighs_sent:
                    # childs finished?
                    if len(childs)==0 or childs_over:
                        if rank != 0:
                            msg[1] = ROVER
                            comm.send(msg, dest=parent, tag=ROVER)
                            round_over = True
        
        elif typ == ROVER: # ROVER received
            rover_rcvd.add(sender)
            if rover_rcvd == currchilds:
                childs_over = True
                if neighs_over and neighs_sent: #neighs finished
                    round_over = True
                    if rank != 0:
                        msg[1] = ROVER
                        comm.send(msg,dest=parent,tag=ROVER)
        
        elif typ == FINISHED: # a child finished
            finish_rcvd.add(sender)
            removed_childs.add(sender)
            if finish_rcvd == childs:
                finished_childs = True
                if state != UNDEC:
                    finished_all = True
                    if rank != 0:
                        msg[1] = FINISHED
                        comm.send(msg,dest=parent,tag=FINISHED)
                    else:
                        msg[1] = TERMINATE
                        for child in childs:
                            comm.send(msg, dest=child, tag=TERMINATE)
                            round_over = True
                            terminated = True

        else: #TERMINATE received
            if len(childs) != 0:
                for child in childs:
                    comm.send(msg, dest=child, tag=TERMINATE)
            terminated = True
            round_over = True
  
    round_num = round_num + 1
    currneighs -= removed_neighs
    currchilds -= removed_childs
    
    
    #all edges covered?
    if len(currneighs) == 0 and state == UNDEC:
        state = NOTCOV
        round_saved = roun
        if len(currchilds) == 0:
            finished_all = True
            msg[1] = FINISHED
            comm.send(msg,dest=parent,tag=FINISHED)
            
print(" Rank: {}, color: {}".format(rank,round_saved))
