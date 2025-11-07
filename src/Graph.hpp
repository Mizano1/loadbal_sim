#ifndef GRAPH_HPP
#define GRAPH_HPP

#include <vector>
#include <queue>
#include <cmath>
#include <algorithm>
#include <random>

using std::vector;

// Build a cycle graph: 0-1-2-...-n-1-0
inline vector<vector<int>> build_cycle_graph(int n) {
    vector<vector<int>> g(n);
    for (int i = 0; i < n; i++) {
        int nxt = (i + 1) % n;
        int prv = (i - 1 + n) % n;
        g[i].push_back(nxt);
        g[i].push_back(prv);
    }
    return g;
}

// Build a 2D grid of size sqrt(n) x sqrt(n), periodic
// n must be a perfect square for this simple version
inline vector<vector<int>> build_grid_graph(int n) {
    int side = (int)std::sqrt((double)n);
    vector<vector<int>> g(n);
    for (int r = 0; r < side; r++) {
        for (int c = 0; c < side; c++) {
            int id = r * side + c;
            int up = ((r - 1 + side) % side) * side + c;
            int down = ((r + 1) % side) * side + c;
            int left = r * side + (c - 1 + side) % side;
            int right = r * side + (c + 1) % side;
            g[id].push_back(up);
            g[id].push_back(down);
            g[id].push_back(left);
            g[id].push_back(right);
        }
    }
    return g;
}

// Compute all-pairs shortest paths on an unweighted graph using BFS from each node
inline vector<vector<int>> all_pairs_shortest_paths(const vector<vector<int>> &g) {
    int n = (int)g.size();
    vector<vector<int>> dist(n, vector<int>(n, 1e9));
    for (int s = 0; s < n; s++) {
        std::queue<int> q;
        dist[s][s] = 0;
        q.push(s);
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : g[u]) {
                if (dist[s][v] > dist[s][u] + 1) {
                    dist[s][v] = dist[s][u] + 1;
                    q.push(v);
                }
            }
        }
    }
    return dist;
}

// For each node, get nodes within <= k hops. If more than k, sample exactly k.
inline vector<vector<int>> get_k_hop_neighbors(
    const vector<vector<int>> &dist,
    int k,
    std::mt19937_64 &rng
) {
    int n = (int)dist.size();
    vector<vector<int>> k_nbrs(n);
    for (int s = 0; s < n; s++) {
        vector<int> cand;
        for (int v = 0; v < n; v++) {
            if (v == s) continue;
            if (dist[s][v] > 0 && dist[s][v] <= k) {
                cand.push_back(v);
            }
        }
        if ((int)cand.size() > k) {
            std::shuffle(cand.begin(), cand.end(), rng);
            cand.resize(k);
        }
        k_nbrs[s] = cand;
    }
    return k_nbrs;
}

#endif
