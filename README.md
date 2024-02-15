  SE 454 Distributed Computing Project
  Rank-based Vertex Coloring 

The aim of the project
This project implements a distributed computing algorithm for rank-based graph coloring using the MPI (Message Passing Interface) library. 
The algorithm is designed to color nodes in a distributed graph while efficiently communicating with neighboring nodes. 
This algorithm assumes that the root node is the lowest ranked node, thus terminates when the root node is colored. Each rank/node is trying to find a unique color that is not used by its neighbors.

