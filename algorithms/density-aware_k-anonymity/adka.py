import networkx as nx
import matplotlib.pyplot as plt
import random

# -----------------------------
# Create graph
# -----------------------------
G = nx.grid_2d_graph(5, 5)   # 5x5 city grid graph
G = nx.convert_node_labels_to_integers(G)

# -----------------------------
# Random users
# -----------------------------
user_locations = {node: 0 for node in G.nodes()}

for _ in range(30):
    n = random.choice(list(G.nodes()))
    user_locations[n] += 1

print("Users per node:", user_locations)

# -----------------------------
# ADKA functions
# -----------------------------
def compute_density(node, depth=1):
    visited = {node}
    queue = [(node, 0)]
    count = user_locations[node]

    while queue:
        current, d = queue.pop(0)
        if d == depth:
            continue

        for neigh in G.neighbors(current):
            if neigh not in visited:
                visited.add(neigh)
                queue.append((neigh, d + 1))
                count += user_locations[neigh]

    return count


def select_k(density):
    if density < 4:
        return 10
    elif density < 10:
        return 5
    else:
        return 2


def expand_region(start_node, k):
    region = {start_node}
    queue = [start_node]
    user_count = user_locations[start_node]

    while user_count < k:
        current = queue.pop(0)
        for neigh in G.neighbors(current):
            if neigh not in region:
                region.add(neigh)
                queue.append(neigh)
                user_count += user_locations[neigh]
                if user_count >= k:
                    break

    return region

# -----------------------------
# MULTIPLE RUNS (EXPERIMENT)
# -----------------------------
runs = 20

density_list = []
k_list = []
region_size_list = []

print("\nRunning ADKA for multiple users...\n")

for i in range(runs):
    target = random.choice(list(G.nodes()))
    density = compute_density(target)
    k = select_k(density)
    region = expand_region(target, k)

    density_list.append(density)
    k_list.append(k)
    region_size_list.append(len(region))

    print(f"Run {i+1}: Target={target}, Density={density}, k={k}, Region size={len(region)}")

# -----------------------------
# Plot results
# -----------------------------
plt.figure()
plt.scatter(density_list, k_list)
plt.xlabel("Density")
plt.ylabel("Selected k")
plt.title("ADKA: Density vs Selected k")
plt.grid(True)
plt.show()

plt.figure()
plt.scatter(k_list, region_size_list)
plt.xlabel("Selected k")
plt.ylabel("Region Size (nodes)")
plt.title("ADKA: k vs Region Size")
plt.grid(True)
plt.show()



# -----------------------------
# VISUALIZE ONE SAMPLE RUN
# -----------------------------
sample_target = random.choice(list(G.nodes()))
sample_density = compute_density(sample_target)
sample_k = select_k(sample_density)
sample_region = expand_region(sample_target, sample_k)

print("\nSample visualization run:")
print("Target:", sample_target)
print("Density:", sample_density)
print("k:", sample_k)
print("Region:", sample_region)

pos = nx.spring_layout(G)

nx.draw(G, pos, with_labels=True, node_color='lightblue')
nx.draw_networkx_nodes(G, pos,
                       nodelist=list(sample_region),
                       node_color='red')
plt.title("Sample ADKA Anonymized Region")
plt.show()
