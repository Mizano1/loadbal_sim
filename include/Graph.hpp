#ifndef GRAPH_HPP
#define GRAPH_HPP

#include <vector>
#include <cmath>
#include <algorithm>

// Generate neighbors for Cycle: s+1, s-1, s+2, s-2...
// Each node is connected to k/2 neighbors on the left and k/2 on the right.
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
    
    // 1. Calculate Best Fit Width
    int width = (int)std::floor(std::sqrt(n));
    while (width > 0 && n % width != 0) {
        width--;
    }
    
    // --- PRIME CHECK ---
    // If width reached 1, it means n has no factors other than 1 and itself.
    // This results in a 1 x N line, not a 2D grid.
    if (width == 1 && n > 1) {
        // You can either return empty (to signal failure) 
        // or throw an exception depending on your error handling preference.
        std::cerr << "Error: N=" << n << " is prime. Cannot form a rectangular grid." << std::endl;
        return k_nbrs; 
    }
    // -------------------

    int height = n / width; 

    for (int i = 0; i < n; i++) {
        int r = i / width;
        int c = i % width;
        
        auto add = [&](int nr, int nc) {
            // Strict Boundary Check (Non-Toroidal)
            if (nr >= 0 && nr < height && nc >= 0 && nc < width) {
                int neighbor = nr * width + nc;
                if (k_nbrs[i].size() < (size_t)k_neighbors) {
                    k_nbrs[i].push_back(neighbor);
                }
            }
        };

        add(r, c + 1); // Right
        add(r, c - 1); // Left
        add(r + 1, c); // Down
        add(r - 1, c); // Up
    }
    return k_nbrs;
}

// Generate neighbors for Clusters
// Each node is connected to all other nodes within its own cluster.
// Used for "spatialKL" policy within a cluster topology.
inline std::vector<std::vector<int>> generate_cluster_neighbors(int n, int num_clusters) {
    std::vector<std::vector<int>> k_nbrs(n);
    if (num_clusters <= 0) return k_nbrs;

    int servers_per_cluster = (n + num_clusters - 1) / num_clusters; // Ceil division

    for (int i = 0; i < n; i++) {
        int my_cluster = i / servers_per_cluster;
        
        // Calculate the range of node IDs in this cluster
        int start_node = my_cluster * servers_per_cluster;
        int end_node = std::min(start_node + servers_per_cluster, n);

        // Add all other nodes in the cluster as neighbors
        for (int candidate = start_node; candidate < end_node; candidate++) {
            if (candidate != i) {
                k_nbrs[i].push_back(candidate);
            }
        }
    }
    return k_nbrs;
}

#endif