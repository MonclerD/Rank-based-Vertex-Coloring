from mpi4py import MPI
import numpy as np 

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n = comm.Get_size()

# States
UNDEC = 0
INCOV = 1
NOTCOV = 2

# Message types
ROUND = 0
DATA = 1
ROVER = 2
FINISHED = 3
TERMINATE = 4

msg = np.array([-1, -1, -1, -1])

# Adjacency matrix
A = np.array([[0,0,0,1,1,0,0,1],
              [0,0,0,0,0,1,0,1],
              [0,0,0,1,1,0,1,0], 
              [1,0,1,0,1,0,1,0],
              [1,0,1,1,0,1,0,1],
              [0,1,0,0,1,0,0,1],
              [0,0,1,1,0,0,0,0],
              [1,1,0,0,1,1,0,0]], dtype=int)

# Spanning tree structure
msg = [-1, -1, -1, -1]
children = [[3, 4, 7], [], [6], [2], [], [1], [], [5]]
parents = [0, 5, 3, 0, 0, 7, 2, 0]

# Initialize variables
child = children[rank]
parent = parents[rank]
childs = set(child)
neighs, neighs_rcvd, rover_rcvd, finish_rcvd = set(), set(), set(), set()
removed_neighs = set()
removed_childs = set()

# Identify neighbors
for i in range(n):
    if A[rank,i] == 1:
        neighs.add(i)
        
currneighs = neighs.copy()
currchilds = childs.copy()
round_num = 0
max_count = n - 1
state = UNDEC
finished_childs, finished_all, terminated = False, False, False

# Main algorithm loop
while not terminated:
    round_over, neighs_over, childs_over = False, False, False
    neighs_sent = False
    rover_rcvd.clear()
    neighs_rcvd.clear()
    removed_neighs.clear()
    removed_childs.clear()
    
    # Root node logic
    if rank == 0:
        msg = [rank, ROUND, round_num, -1]
        for child in currchilds:
            comm.send(msg, dest=child, tag=ROUND)
        if state == UNDEC:
            msg[1], msg[3] = DATA, state
            for node in currneighs:
                comm.send(msg, dest=node, tag=DATA)
            neighs_sent = True
        else:
            neighs_over = True
            neighs_sent = True
    
    # Main communication loop
    while not round_over:
        msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        sender, typ, roun, ne_state = msg[0], msg[1], msg[2], msg[3]
        msg[0] = rank
        if typ == ROUND:
            if len(currchilds) != 0:
                for child in currchilds:
                    comm.send(msg, dest=child, tag=ROUND)
            else:
                childs_over = True
            if state != UNDEC:
                neighs_over = True
                neighs_sent = True
                if len(childs) == 0:
                    childs_over = True
                    msg[1] = ROVER
                    comm.send(msg, dest=parent, tag=ROVER)
                    round_over = True
                else:
                    neighs_sent, neighs_over = True, True
            else:
                if rank > max(currneighs):
                    state = INCOV
                    round_saved = max_count - round_num
                    if len(currchilds) == 0:
                        childs_over = True
                        finished_all = True
                        msg[1] = FINISHED 
                        comm.send(msg, dest=parent, tag=FINISHED)
                msg[1], msg[3] = DATA, state
                for node in currneighs:
                    comm.send(msg, dest=node, tag=DATA)
                    neighs_sent = True
                if neighs_over and childs_over:
                    if rank != 0:
                        msg[1] = ROVER
                        comm.send(msg, dest=parent, tag=ROVER)
                        round_over = True
        elif typ == DATA:
            neighs_rcvd.add(sender)
            if ne_state == INCOV or ne_state == NOTCOV:
                if sender in currneighs:
                    removed_neighs.add(sender)
            if neighs_rcvd == currneighs:
                neighs_over = True
                if neighs_sent:
                    if len(childs) == 0 or childs_over:
                        if rank != 0:
                            msg[1] = ROVER
                            comm.send(msg, dest=parent, tag=ROVER)
                            round_over = True
        elif typ == ROVER:
            rover_rcvd.add(sender)
            if rover_rcvd == currchilds:
                childs_over = True
                if neighs_over and neighs_sent:
                    round_over = True
                    if rank != 0:
                        msg[1] = ROVER
                        comm.send(msg, dest=parent, tag=ROVER)
        elif typ == FINISHED:
            finish_rcvd.add(sender)
            removed_childs.add(sender)
            if finish_rcvd == childs:
                finished_childs = True
                if state != UNDEC:
                    finished_all = True
                    if rank != 0:
                        msg[1] = FINISHED
                        comm.send(msg, dest=parent, tag=FINISHED)
                    else:
                        msg[1] = TERMINATE
                        for child in childs:
                            comm.send(msg, dest=child, tag=TERMINATE)
                            round_over = True
                            terminated = True
        elif typ == TERMINATE:
            if len(childs) != 0:
                for child in childs:
                    comm.send(msg, dest=child, tag=TERMINATE)
            terminated = True
            round_over = True
    round_num += 1
    currneighs -= removed_neighs
    currchilds -= removed_childs
    if len(currneighs) == 0 and state == UNDEC:
        state = NOTCOV
        round_saved = max_count - round_num
        if len(currchilds) == 0:
            finished_all = True
            msg[1] = FINISHED
            comm.send(msg, dest=parent, tag=FINISHED)

print(" Rank: {}, Color: {}".format(rank, round_saved))
