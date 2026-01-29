#include "Simulation.hpp" 
#include <algorithm>
#include <cmath>
#include <iostream>
#include <fstream>
#include <unordered_set>

Simulation::Simulation(int n_, double lambda__, int m_, double mu__,
                       const std::string &policy_,
                       const std::string &topology_,
                       const std::vector<std::vector<int>> &dist_,
                       const std::vector<std::vector<int>> &k_nbrs_,
                       int k_, int L_, int qmax_,int max_shards_,
                       int num_clusters_, double comm_cost_,
                       const std::string& trace_file_path)
    : n(n_), lambda_(lambda__), m(m_), mu_(mu__), 
      policy(policy_), topology(topology_),
      dist(dist_), k_nbrs(k_nbrs_), k(k_), L(L_), qmax(qmax_),
      num_clusters(num_clusters_), comm_cost(comm_cost_),
      T(0.0), q(n_, 0), s_time(n_, 1e30), t_arr(0.0), 
      req_dist(0.0), q_mid_hist(qmax_, 0.0), 
      arrivals_recorded(0),
      trace_idx(0), use_trace(false)
{
    rng.seed(123456789ULL);
    // Safety check for shards
    if (max_shards < 1) max_shards = 1;

    // Load Trace if provided
    if (!trace_file_path.empty()) {
        load_trace(trace_file_path);
    }

    // Initial System State
    std::uniform_int_distribution<int> U(0, n - 1);
    int first = U(rng);
    q[first]++;
    
    if (use_trace && !trace_jobs.empty()) {
        s_time[first] = trace_jobs[0].duration;
        t_arr = trace_jobs[0].inter_arrival_time;
        trace_idx = 1; 
    } else {
        s_time[first] = exp_rv(mu_);
        t_arr = exp_rv(n * lambda_);
    }
}

void Simulation::load_trace(const std::string& filepath) {
    std::ifstream infile(filepath);
    if (!infile.good()) {
        std::cerr << "Error: Could not open trace file: " << filepath << "\n";
        use_trace = false;
        return;
    }
    
    // Check/Skip header
    std::string line;
    if (infile.peek() < '0' || infile.peek() > '9') {
        std::getline(infile, line);
    }

    double dt, d;
    while (infile >> dt >> d) {
        trace_jobs.push_back({dt, d});
    }
    
    if (!trace_jobs.empty()) {
        std::cout << "Loaded " << trace_jobs.size() << " jobs from trace.\n";
        use_trace = true;
    } else {
        use_trace = false;
    }
}

double Simulation::exp_rv(double rate) {
    std::uniform_real_distribution<double> U(0.0, 1.0);
    return -std::log(1.0 - U(rng)) / rate;
}

int Simulation::get_cluster_id(int node_index) const {
    if (num_clusters <= 1) return 0;
    int servers_per_cluster = (n + num_clusters - 1) / num_clusters;
    return node_index / servers_per_cluster;
}

double Simulation::calculate_distance(int u, int v) {
    if (u == v) return 0.0;

    // Cluster Logic
    if (topology == "cluster") {
        // 1. Determine Topological Distance (Hops)
        // Same Cluster = 1 Hop 
        // Different Cluster = 2 Hops 
        double hops = (get_cluster_id(u) == get_cluster_id(v)) ? 1.0 : 2.0;

        // 2. Apply Weighting
        double weight = (comm_cost > 1e-9) ? comm_cost : 1.0;

        return hops * weight;
    }

    if (!dist.empty()) return (double)dist[u][v];

    if (topology == "cycle") {
        int d = std::abs(u - v);
        return (double)std::min(d, n - d);
    } 
    else if (topology == "grid") {
        // 1. Find the "Best Fit" Width
        // Start at sqrt(n) and work down to find the largest factor
        int width = (int)std::floor(std::sqrt(n));
        
        while (n % width != 0) {
            width--;
        }
        
        // Safety check: width can't be 0 (though loop above prevents this since 1 divides everything)
        if (width == 0) return 0.0; 

        // 2. Calculate Coordinates based on this Perfect Rectangle
        int r1 = u / width;
        int c1 = u % width;
        
        int r2 = v / width;
        int c2 = v % width;
        
        // 3. Manhattan Distance
        int dr = std::abs(r1 - r2);
        int dc = std::abs(c1 - c2);
        
        return (double)(dr + dc);
    }
    return 0.0;
}
// --- Helper for Multi-Shard Extension ---
// Selects 'count' best nodes from a larger candidate pool
std::vector<int> Simulation::choose_multi_nodes(int s, int count) {
    std::vector<int> candidates;
    
    // Need enough unique candidates to pick 'count' servers
    // We pool (count + k + L) to be safe and ensure diversity
    int target_pool = std::max(count, count + k + L);
    candidates.reserve(target_pool);
    candidates.push_back(s);

    std::uniform_int_distribution<int> U(0, n - 1);
    std::unordered_set<int> used;
    used.insert(s);

    // -- Candidate Generation (Simplified Adapter) --
    // For Multi-Shard, we generally just fill with Spatial or Random 
    // depending on the policy to get enough candidates.
    
    if (policy == "spatialKL" && !k_nbrs.empty()) {
        // Add neighbors first
        for (int v : k_nbrs[s]) {
             if (used.find(v) == used.end()) {
                 used.insert(v);
                 candidates.push_back(v);
             }
        }
    }
    
    // Fill remainder with randoms (works for pot, poKL, weighted fallback)
    while ((int)candidates.size() < target_pool) {
        int r = U(rng);
        if (used.find(r) == used.end()) {
            used.insert(r);
            candidates.push_back(r);
        }
    }

    // -- Sort and Pick Top 'count' --
    auto get_score = [&](int cand) {
        double score = (double)q[cand];
        if (topology == "cluster") score += calculate_distance(s, cand);
        return score;
    };

    if ((int)candidates.size() > count) {
        std::partial_sort(candidates.begin(), 
                          candidates.begin() + count, 
                          candidates.end(),
                          [&](int a, int b) {
                              return get_score(a) < get_score(b);
                          });
        candidates.resize(count);
    }
    return candidates;
}
int Simulation::choose_node(int s) {
    std::vector<int> candidates;
    candidates.reserve(1 + k + L);
    candidates.push_back(s);
    std::uniform_int_distribution<int> U(0, n - 1);

    if (policy == "pot") {
        int r; do { r = U(rng); } while (r == s);
        candidates.push_back(r);
    } 
    else if (policy == "poKL") {
        std::unordered_set<int> used; used.insert(s);
        while ((int)candidates.size() < 1 + k + L) {
            int r = U(rng);
            if (used.find(r) == used.end()) {
                used.insert(r);
                candidates.push_back(r);
            }
        }
    } 
    else if (policy == "spatialKL") {
        if (topology == "cluster") {
            // --- CLUSTER LOGIC (Corrected) ---
            const std::vector<int>& my_cluster_nodes = k_nbrs[s];
            
            // 1. Pick 'k' neighbors from the local cluster
            if (!my_cluster_nodes.empty()) {
                if ((int)my_cluster_nodes.size() <= k) {
                    for (int v : my_cluster_nodes) candidates.push_back(v);
                } else {
                    std::uniform_int_distribution<int> dist_idx(0, my_cluster_nodes.size() - 1);
                    std::unordered_set<int> picked_indices;
                    while ((int)picked_indices.size() < k) {
                        int idx = dist_idx(rng);
                        if (picked_indices.find(idx) == picked_indices.end()) {
                            picked_indices.insert(idx);
                            candidates.push_back(my_cluster_nodes[idx]);
                        }
                    }
                }
            }

            // 2. Pick 'L' global random neighbors
            std::unordered_set<int> used(candidates.begin(), candidates.end());
            int target_size = candidates.size() + L;

            while ((int)candidates.size() < target_size) {
                int r = U(rng);
                if (used.find(r) == used.end()) {
                    used.insert(r);
                    candidates.push_back(r);
                }
            }

        } else {
            // --- GRID / CYCLE LOGIC ---
            for (int v : k_nbrs[s]) candidates.push_back(v);
            std::unordered_set<int> used(candidates.begin(), candidates.end());
            int target = 1 + k_nbrs[s].size() + L;
            while ((int)candidates.size() < target) {
                int r = U(rng);
                if (used.find(r) == used.end()) {
                    used.insert(r);
                    candidates.push_back(r);
                }
            }
        }
        
    }
    // ---------------------------------------------------------
    // HYBRID WEIGHTED POLICY (Corrected)
    // ---------------------------------------------------------
    else if (policy == "weighted") {
        // 1. Define Neighborhood & Weights
        std::vector<int> neighborhood;
        std::vector<double> weights;
        
        neighborhood.reserve(2 * k);
        weights.reserve(2 * k);

        for (int dist = 1; dist <= k; ++dist) {
            int right = (s + dist) % n;
            neighborhood.push_back(right);
            weights.push_back(1.0 / dist); 

            int left = (s - dist + n) % n;
            neighborhood.push_back(left);
            weights.push_back(1.0 / dist); 
        }

        // 2. Pick ONE "Weighted" Candidate
        std::discrete_distribution<int> dist_sampler(weights.begin(), weights.end());
        int idx = dist_sampler(rng);
        int w_node = neighborhood[idx];
        
        candidates.push_back(w_node);

        // 3. Pick 'L' "Global Random" Candidates
        // This ensures statistical diversity (Po3 performance)
        std::unordered_set<int> used;
        used.insert(s);
        used.insert(w_node);

        int randoms_needed = L; 
        while (randoms_needed > 0) {
            int r = U(rng);
            if (used.find(r) == used.end()) {
                used.insert(r);
                candidates.push_back(r);
                randoms_needed--;
            }
        }
    }
    // ---------------------------------------------------------
    

    // --- SELECTION LOGIC ---
    int best = candidates[0];
    double best_score = 1e30;

    for (int cand : candidates) {

        
        double score = (double)q[cand]; 

        if (score < best_score) {
            best_score = score;
            best = cand;
        }
    }
    return best;
}

SimulationResult Simulation::run() {
    int arrivals = 1;
    int max_jobs = use_trace ? trace_jobs.size() : m;
    int warmup = static_cast<int>(max_jobs * 0.2);
    
    std::uniform_int_distribution<int> U(0, n - 1);
    std::uniform_int_distribution<int> U_shards(1, max_shards);
    while (arrivals < max_jobs) {
        // 1. Find the next event (min_service vs t_arr)
        int min_idx = -1;
        double min_service = 1e30;
        for (int i = 0; i < n; i++) {
            if (q[i] > 0 && s_time[i] < min_service) {
                min_service = s_time[i];
                min_idx = i;
            }
        }

        double dt = std::min(t_arr, min_service);
        
        // --- Time-Weighted Histogram Update ---
        // Only record stats after warmup
        if (arrivals > warmup && dt > 0) {
            T += dt;
            // For every queue, add the duration 'dt' to its length bin
            for (int i = 0; i < n; ++i) {
                int len = q[i];
                if (len < qmax) {
                    q_mid_hist[len] += dt;
                } else {
                    q_mid_hist[qmax-1] += dt; // overflow bin
                }
            }
        }

        // Advance clocks
        if (dt > 0) {
             t_arr -= dt;
             for (int i=0; i<n; i++) if(q[i]>0) s_time[i] -= dt;
        }

        if (t_arr <= 1e-9) { // ARRIVAL
            arrivals++;
            

            double job_duration;
            if (use_trace) {
                job_duration = trace_jobs[trace_idx-1].duration; 
            } else {
                job_duration = exp_rv(mu_);
            }

            int s = U(rng);
            // --- MULTI-SHARD LOGIC ---
            int required_shards = 1;
            if (max_shards > 1) {
                required_shards = U_shards(rng);
            }

            // Path A: Single Server (Optimized)
            if (required_shards == 1) {
                int chosen = choose_node(s);
                q[chosen]++;
                if (arrivals > warmup) {
                    req_dist += calculate_distance(s, chosen);
                }
                if (q[chosen] == 1) s_time[chosen] = job_duration;
            }
            // Path B: Multi-Server
            else {
                std::vector<int> targets = choose_multi_nodes(s, required_shards);
                for (int node : targets) {
                    q[node]++;
                    if (arrivals > warmup) {
                        req_dist += calculate_distance(s, node);
                    }
                    if (q[node] == 1) s_time[node] = job_duration;
                }
            }
            // ------------------------
            if (arrivals > warmup) arrivals_recorded++;

            if (use_trace) {
                if (trace_idx < trace_jobs.size()) {
                    t_arr = trace_jobs[trace_idx].inter_arrival_time;
                    trace_idx++;
                } else {
                    t_arr = 1e30; 
                }
            } else {
                t_arr = exp_rv(n * lambda_);
            }

        } 
        else { // SERVICE
            q[min_idx]--;
            if (q[min_idx] == 0) {
                s_time[min_idx] = 1e30;
            } else {
                s_time[min_idx] = exp_rv(mu_); 
            }
        }
    }

    // --- Post-Processing ---
    // Normalize the time-weighted histogram
    // Total time accumulated across all N nodes is T * n
    double total_time_n = T * n;
    
    if (total_time_n > 0) {
        for(double &v : q_mid_hist) v /= total_time_n;
    }
    
    // Calculate Mean Q
    double mean_Q_dist = 0.0;
    for (size_t k = 0; k < q_mid_hist.size(); ++k) {
        mean_Q_dist += k * q_mid_hist[k];
    }

    double mean_W = (lambda_ > 0) ? mean_Q_dist / lambda_ : 0;
    
    return {
        q_mid_hist, 
        req_dist, 
        mean_Q_dist,   
        mean_W, 
        (arrivals_recorded>0 ? req_dist/arrivals_recorded : 0)
    };
}