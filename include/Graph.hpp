#ifndef GRAPH_HPP
#define GRAPH_HPP

#include <vector>
#include <cmath>
#include <algorithm>



// Generate neighbors for Cycle: s+1, s-1, s+2, s-2...
inline std::vector<std::vector<int>> generate_cycle_neighbors(int n, int k_neighbors) {
    std::vector<std::vector<int>> k_nbrs(n);
    for (int i = 0; i < n; i++) {
        for (int offset = 1; offset <= (k_neighbors + 1) / 2; ++offset) {
            if (k_nbrs[i].size() < (size_t)k_neighbors) 
                k_nbrs[i].push_back((i + offset) % n);
            if (k_nbrs[i].size() < (size_t)k_neighbors) 
                k_nbrs[i].push_back((i - offset + n) % n);
        }
    }
    return k_nbrs;
}

// Generate neighbors for Grid: Right, Left, Down, Up
inline std::vector<std::vector<int>> generate_grid_neighbors(int n, int k_neighbors) {
    std::vector<std::vector<int>> k_nbrs(n);
    int side = (int)std::round(std::sqrt(n));
    if (side * side != n) return k_nbrs; // Safety check

    for (int i = 0; i < n; i++) {
        int r = i / side;
        int c = i % side;
        
        auto add = [&](int nr, int nc) {
             int neighbor = ((nr + side) % side) * side + ((nc + side) % side);
             if (k_nbrs[i].size() < (size_t)k_neighbors) k_nbrs[i].push_back(neighbor);
        };

        add(r, c + 1); 
        add(r, c - 1);
        add(r + 1, c);
        add(r - 1, c);
    }
    return k_nbrs;
}
#endif