#!/usr/bin/env python3
"""
Temporal Cloaking for Location Privacy in IoT Smart Cities
============================================================
This implementation demonstrates temporal cloaking for protecting
user trajectory privacy by generalizing location updates within
temporal windows.

Author: Naga Sai Dattu
Date: February 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict, Tuple, Set, Any
import random
from datetime import datetime, timedelta
import json
import csv
from collections import defaultdict
import os
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
import argparse


# ======================================================================
# Trajectory Simulator
# ======================================================================

class TrajectorySimulator:
    """
    Simulates user mobility in a smart city environment.
    Generates realistic trajectories with configurable movement patterns.
    """
    
    def __init__(self, 
                 city_size: Tuple[float, float] = (10.0, 10.0),
                 num_users: int = 30,
                 simulation_duration_hours: float = 24.0,
                 update_interval_minutes: float = 1.0):
        """
        Initialize trajectory simulator.
        
        Args:
            city_size: (width, height) of city area in km
            num_users: Number of users to simulate
            simulation_duration_hours: Total simulation time
            update_interval_minutes: Time between location updates
        """
        self.city_size = city_size
        self.num_users = num_users
        self.duration_hours = simulation_duration_hours
        self.update_interval = update_interval_minutes
        
        # Generate points of interest (common destinations)
        self.poi = self._generate_points_of_interest()
        
        # User trajectories: {user_id: [(x, y, timestamp), ...]}
        self.trajectories = {}
        
        # User attributes
        self.user_homes = {}
        self.user_workplaces = {}
        self.user_routines = {}
        
    def _generate_points_of_interest(self) -> List[Tuple[float, float]]:
        """Generate realistic points of interest in the city."""
        poi = [
            (2.0, 2.0),   # Residential area 1
            (8.0, 2.0),   # Residential area 2
            (5.0, 5.0),   # City center
            (2.0, 8.0),   # Shopping district
            (8.0, 8.0),   # Business district
            (1.0, 5.0),   # Park
            (9.0, 5.0),   # Stadium
        ]
        return poi
    
    def _assign_user_attributes(self):
        """Assign home, work locations and routines to users."""
        for user_id in range(self.num_users):
            # Assign home (biased towards residential areas)
            if random.random() < 0.7:
                home_idx = random.choice([0, 1])  # Residential areas
            else:
                home_idx = random.randint(0, len(self.poi)-1)
            
            # Add some randomness around POI
            home_x = self.poi[home_idx][0] + random.uniform(-0.5, 0.5)
            home_y = self.poi[home_idx][1] + random.uniform(-0.5, 0.5)
            home_x = max(0, min(self.city_size[0], home_x))
            home_y = max(0, min(self.city_size[1], home_y))
            self.user_homes[user_id] = (home_x, home_y)
            
            # Assign workplace (different from home)
            work_idx = random.choice([2, 3, 4])  # Commercial areas
            work_x = self.poi[work_idx][0] + random.uniform(-0.5, 0.5)
            work_y = self.poi[work_idx][1] + random.uniform(-0.5, 0.5)
            work_x = max(0, min(self.city_size[0], work_x))
            work_y = max(0, min(self.city_size[1], work_y))
            self.user_workplaces[user_id] = (work_x, work_y)
            
            # Assign routine type
            routine_types = ['commuter', 'mobile_worker', 'shopper', 'student', 'retired']
            weights = [0.4, 0.2, 0.15, 0.15, 0.1]
            self.user_routines[user_id] = random.choices(routine_types, weights=weights)[0]
    
    def _generate_movement_pattern(self, user_id: int) -> List[Tuple[float, float, datetime]]:
        """
        Generate trajectory based on user routine.
        
        Returns:
            List of (x, y, timestamp) points
        """
        routine = self.user_routines[user_id]
        home = self.user_homes[user_id]
        work = self.user_workplaces[user_id]
        
        # Total number of updates
        total_minutes = int(self.duration_hours * 60)
        num_updates = total_minutes // self.update_interval
        
        trajectory = []
        current_time = datetime(2026, 1, 1, 6, 0)  # Start at 6 AM
        
        if routine == 'commuter':
            # Home -> Work -> Home pattern
            for i in range(num_updates):
                hour = current_time.hour + current_time.minute / 60
                
                if 6 <= hour < 9:  # Morning commute
                    # Linear interpolation from home to work
                    progress = (hour - 6) / 3  # 3-hour commute window
                    progress = min(1.0, max(0.0, progress))
                    x = home[0] + (work[0] - home[0]) * progress
                    y = home[1] + (work[1] - home[1]) * progress
                    
                elif 9 <= hour < 17:  # At work (with some movement)
                    x = work[0] + random.uniform(-0.2, 0.2)
                    y = work[1] + random.uniform(-0.2, 0.2)
                    
                elif 17 <= hour < 20:  # Evening commute
                    progress = (hour - 17) / 3  # 3-hour commute window
                    progress = min(1.0, max(0.0, progress))
                    x = work[0] + (home[0] - work[0]) * progress
                    y = work[1] + (home[1] - work[1]) * progress
                    
                else:  # At home (with some movement)
                    x = home[0] + random.uniform(-0.1, 0.1)
                    y = home[1] + random.uniform(-0.1, 0.1)
                
                # Add noise and bound to city
                x += random.uniform(-0.05, 0.05)
                y += random.uniform(-0.05, 0.05)
                x = max(0, min(self.city_size[0], x))
                y = max(0, min(self.city_size[1], y))
                
                trajectory.append((x, y, current_time))
                current_time += timedelta(minutes=self.update_interval)
                
        elif routine == 'mobile_worker':
            # Multiple locations throughout day
            locations = [home, work, 
                        (random.uniform(2, 8), random.uniform(2, 8)),
                        (random.uniform(2, 8), random.uniform(2, 8))]
            
            current_loc_idx = 0
            time_at_location = 0
            location_duration = random.uniform(1, 4)  # Hours
            
            for i in range(num_updates):
                hour = current_time.hour + current_time.minute / 60
                
                # Change location if stayed long enough
                if time_at_location >= location_duration:
                    current_loc_idx = (current_loc_idx + 1) % len(locations)
                    time_at_location = 0
                    location_duration = random.uniform(1, 4)
                
                # Current target location
                target = locations[current_loc_idx]
                
                # Add movement toward target
                if i > 0:
                    prev_x, prev_y, _ = trajectory[-1]
                    dx = target[0] - prev_x
                    dy = target[1] - prev_y
                    distance = np.sqrt(dx*dx + dy*dy)
                    
                    if distance > 0.1:  # Move toward target
                        step = min(0.05, distance)
                        x = prev_x + (dx / distance) * step
                        y = prev_y + (dy / distance) * step
                    else:  # At target, small random movement
                        x = target[0] + random.uniform(-0.1, 0.1)
                        y = target[1] + random.uniform(-0.1, 0.1)
                else:
                    x, y = home
                
                x += random.uniform(-0.05, 0.05)
                y += random.uniform(-0.05, 0.05)
                x = max(0, min(self.city_size[0], x))
                y = max(0, min(self.city_size[1], y))
                
                trajectory.append((x, y, current_time))
                current_time += timedelta(minutes=self.update_interval)
                time_at_location += self.update_interval / 60
                
        else:  # Random waypoint for other routines
            current_x, current_y = home
            target_x, target_y = home
            
            for i in range(num_updates):
                hour = current_time.hour + current_time.minute / 60
                
                # Change target occasionally
                if i % (60 // self.update_interval) == 0:  # Every hour
                    if random.random() < 0.3:
                        target_x = random.uniform(0, self.city_size[0])
                        target_y = random.uniform(0, self.city_size[1])
                    else:
                        # Stay near POI
                        poi_idx = random.randint(0, len(self.poi)-1)
                        target_x = self.poi[poi_idx][0] + random.uniform(-1, 1)
                        target_y = self.poi[poi_idx][1] + random.uniform(-1, 1)
                
                # Move toward target
                dx = target_x - current_x
                dy = target_y - current_y
                distance = np.sqrt(dx*dx + dy*dy)
                
                if distance > 0.05:
                    step = min(0.03, distance)
                    current_x += (dx / distance) * step
                    current_y += (dy / distance) * step
                
                # Add noise
                x = current_x + random.uniform(-0.02, 0.02)
                y = current_y + random.uniform(-0.02, 0.02)
                x = max(0, min(self.city_size[0], x))
                y = max(0, min(self.city_size[1], y))
                
                trajectory.append((x, y, current_time))
                current_time += timedelta(minutes=self.update_interval)
        
        return trajectory
    
    def generate_trajectories(self):
        """Generate trajectories for all users."""
        print("Generating user trajectories...")
        self._assign_user_attributes()
        
        for user_id in range(self.num_users):
            self.trajectories[user_id] = self._generate_movement_pattern(user_id)
        
        print(f"Generated {self.num_users} trajectories")
        print(f"Each trajectory has {len(self.trajectories[0])} location updates")
        return self.trajectories


# ======================================================================
# Temporal Cloaking Algorithm
# ======================================================================

class TemporalCloakingAlgorithm:
    """
    Implements temporal cloaking for trajectory privacy protection.
    Groups location updates within temporal windows and generalizes them.
    """
    
    def __init__(self, 
                 window_size_minutes: float = 15.0,
                 k_anonymity: int = 5,
                 spatial_threshold_km: float = 1.0):
        """
        Initialize temporal cloaking algorithm.
        
        Args:
            window_size_minutes: Size of temporal window
            k_anonymity: Minimum users per spatiotemporal region
            spatial_threshold_km: Maximum distance for grouping users
        """
        self.window_size = window_size_minutes
        self.k = k_anonymity
        self.spatial_threshold = spatial_threshold_km
        
        # Cloaked trajectories: {user_id: [(x, y, timestamp), ...]}
        self.cloaked_trajectories = {}
        
        # Statistics
        self.stats = {
            'windows_processed': 0,
            'users_per_window': [],
            'spatial_errors': [],
            'temporal_errors': [],
            'k_achieved': []
        }
    
    def _create_temporal_windows(self, start_time: datetime, end_time: datetime) -> List[Tuple[datetime, datetime]]:
        """Create non-overlapping temporal windows."""
        windows = []
        current = start_time
        
        while current < end_time:
            window_end = current + timedelta(minutes=self.window_size)
            windows.append((current, window_end))
            current = window_end
        
        return windows
    
    def _find_users_in_window(self, 
                             trajectories: Dict[int, List[Tuple]],
                             window_start: datetime,
                             window_end: datetime) -> Dict[int, Tuple[float, float, datetime]]:
        """
        Find all users and their locations within a time window.
        
        Returns:
            {user_id: (x, y, timestamp)} for users with updates in window
        """
        users_in_window = {}
        
        for user_id, trajectory in trajectories.items():
            # Find location closest to window midpoint
            window_mid = window_start + (window_end - window_start) / 2
            
            closest_point = None
            min_time_diff = float('inf')
            
            for x, y, timestamp in trajectory:
                time_diff = abs((timestamp - window_mid).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_point = (x, y, timestamp)
            
            # Include if within window (with tolerance)
            if min_time_diff <= (self.window_size * 60 / 2):  # Within half window
                users_in_window[user_id] = closest_point
        
        return users_in_window
    
    def _cluster_users_spatially(self, 
                                users: Dict[int, Tuple[float, float, datetime]],
                                threshold: float) -> List[Set[int]]:
        """
        Cluster users based on spatial proximity.
        
        Returns:
            List of clusters (sets of user IDs)
        """
        if not users:
            return []
        
        # Create distance matrix
        user_ids = list(users.keys())
        locations = [users[uid][:2] for uid in user_ids]  # (x, y)
        
        clusters = []
        unassigned = set(user_ids)
        
        while unassigned:
            # Start new cluster with first unassigned user
            current = next(iter(unassigned))
            cluster = {current}
            unassigned.remove(current)
            
            # Find all users within threshold
            changed = True
            while changed:
                changed = False
                to_add = set()
                
                for uid in unassigned:
                    u_x, u_y = users[uid][:2]
                    
                    # Check distance to any user in cluster
                    for cid in cluster:
                        c_x, c_y = users[cid][:2]
                        distance = np.sqrt((u_x - c_x)**2 + (u_y - c_y)**2)
                        
                        if distance <= threshold:
                            to_add.add(uid)
                            changed = True
                            break
                
                cluster.update(to_add)
                unassigned -= to_add
            
            clusters.append(cluster)
        
        return clusters
    
    def _ensure_k_anonymity(self, clusters: List[Set[int]]) -> List[Set[int]]:
        """
        Ensure each cluster has at least k users.
        Merge small clusters with nearest neighbors.
        """
        if not clusters:
            return []
        
        # Sort clusters by size
        clusters = sorted(clusters, key=lambda c: len(c), reverse=True)
        
        valid_clusters = []
        small_clusters = []
        
        # Separate valid and small clusters
        for cluster in clusters:
            if len(cluster) >= self.k:
                valid_clusters.append(cluster)
            else:
                small_clusters.append(cluster)
        
        # Try to merge small clusters
        merged = set()
        for small_cluster in small_clusters:
            if not small_cluster:
                continue
                
            # Try to merge with any valid cluster
            merged_successfully = False
            for i, valid_cluster in enumerate(valid_clusters):
                # Merge if total size >= k
                if len(valid_cluster) + len(small_cluster) >= self.k:
                    valid_clusters[i] = valid_cluster.union(small_cluster)
                    merged.update(small_cluster)
                    merged_successfully = True
                    break
            
            if not merged_successfully:
                # Merge with another small cluster
                for other_small in small_clusters:
                    if other_small == small_cluster:
                        continue
                    if len(small_cluster) + len(other_small) >= self.k:
                        new_cluster = small_cluster.union(other_small)
                        valid_clusters.append(new_cluster)
                        merged.update(small_cluster)
                        merged.update(other_small)
                        break
        
        # Remove merged clusters
        valid_clusters = [c for c in valid_clusters if not c.issubset(merged)]
        
        return valid_clusters
    
    def _compute_generalized_location(self, 
                                     cluster: Set[int],
                                     users: Dict[int, Tuple[float, float, datetime]]) -> Tuple[float, float, datetime]:
        """
        Compute generalized location for a cluster.
        Returns centroid and average timestamp.
        """
        if not cluster:
            return (0, 0, datetime.now())
        
        x_sum, y_sum = 0, 0
        time_sum = 0
        count = 0
        
        for user_id in cluster:
            if user_id in users:
                x, y, timestamp = users[user_id]
                x_sum += x
                y_sum += y
                time_sum += timestamp.timestamp()
                count += 1
        
        if count == 0:
            return (0, 0, datetime.now())
        
        centroid_x = x_sum / count
        centroid_y = y_sum / count
        
        # Average timestamp
        avg_timestamp = datetime.fromtimestamp(time_sum / count)
        
        return (centroid_x, centroid_y, avg_timestamp)
    
    def apply_temporal_cloaking(self, trajectories: Dict[int, List[Tuple]]):
        """
        Apply temporal cloaking to all trajectories.
        
        Args:
            trajectories: Original trajectories from simulator
        """
        print(f"\nApplying temporal cloaking...")
        print(f"  Window size: {self.window_size} minutes")
        print(f"  k-anonymity: {self.k}")
        print(f"  Spatial threshold: {self.spatial_threshold} km")
        
        # Initialize cloaked trajectories
        for user_id in trajectories:
            self.cloaked_trajectories[user_id] = []
        
        # Find time range
        all_times = []
        for traj in trajectories.values():
            for _, _, timestamp in traj:
                all_times.append(timestamp)
        
        start_time = min(all_times)
        end_time = max(all_times)
        
        # Create temporal windows
        windows = self._create_temporal_windows(start_time, end_time)
        self.stats['windows_processed'] = len(windows)
        
        # Process each window
        for window_idx, (window_start, window_end) in enumerate(windows):
            # Find users in this window
            users_in_window = self._find_users_in_window(trajectories, window_start, window_end)
            
            if not users_in_window:
                continue
            
            # Cluster users spatially
            clusters = self._cluster_users_spatially(users_in_window, self.spatial_threshold)
            
            # Ensure k-anonymity
            clusters = self._ensure_k_anonymity(clusters)
            
            # Compute generalized locations for each cluster
            for cluster in clusters:
                gen_x, gen_y, gen_time = self._compute_generalized_location(cluster, users_in_window)
                
                # Assign generalized location to all users in cluster
                for user_id in cluster:
                    self.cloaked_trajectories[user_id].append((gen_x, gen_y, gen_time))
            
            # Update statistics
            self.stats['users_per_window'].append(len(users_in_window))
            if clusters:
                cluster_sizes = [len(c) for c in clusters]
                self.stats['k_achieved'].extend(cluster_sizes)
        
        # Sort cloaked trajectories by time
        for user_id in self.cloaked_trajectories:
            self.cloaked_trajectories[user_id].sort(key=lambda x: x[2])
        
        print(f"  Processed {len(windows)} temporal windows")
        print(f"  Average users per window: {np.mean(self.stats['users_per_window']):.1f}")
        if self.stats['k_achieved']:
            print(f"  Average k achieved: {np.mean(self.stats['k_achieved']):.1f}")
        
        return self.cloaked_trajectories


# ======================================================================
# Privacy-Utility Analyzer
# ======================================================================

class PrivacyUtilityAnalyzer:
    """Analyzes privacy-utility tradeoffs for temporal cloaking."""
    
    @staticmethod
    def calculate_spatial_error(original: Tuple[float, float], 
                                cloaked: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between points."""
        return np.sqrt((original[0] - cloaked[0])**2 + 
                      (original[1] - cloaked[1])**2)
    
    @staticmethod
    def calculate_temporal_error(original_time: datetime, 
                                cloaked_time: datetime) -> float:
        """Calculate time difference in minutes."""
        return abs((cloaked_time - original_time).total_seconds() / 60)
    
    @staticmethod
    def match_trajectory_points(original_traj: List[Tuple],
                               cloaked_traj: List[Tuple]) -> List[Tuple[int, int]]:
        """
        Match points between original and cloaked trajectories.
        Returns list of (orig_idx, cloaked_idx) pairs.
        """
        matches = []
        
        # Simple temporal matching (closest in time)
        for i, (orig_x, orig_y, orig_time) in enumerate(original_traj):
            closest_idx = -1
            min_time_diff = float('inf')
            
            for j, (cloaked_x, cloaked_y, cloaked_time) in enumerate(cloaked_traj):
                time_diff = abs((cloaked_time - orig_time).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_idx = j
            
            if closest_idx >= 0:
                matches.append((i, closest_idx))
        
        return matches
    
    def analyze_trajectories(self,
                            original_trajectories: Dict[int, List[Tuple]],
                            cloaked_trajectories: Dict[int, List[Tuple]]) -> Dict[str, Any]:
        """
        Analyze privacy-utility tradeoff.
        
        Returns:
            Dictionary with analysis results
        """
        print("\nAnalyzing privacy-utility tradeoff...")
        
        results = {
            'spatial_errors': [],
            'temporal_errors': [],
            'trajectory_lengths': [],
            'compression_ratios': [],
            'user_stats': {}
        }
        
        for user_id in original_trajectories:
            if user_id not in cloaked_trajectories:
                continue
            
            orig_traj = original_trajectories[user_id]
            cloaked_traj = cloaked_trajectories[user_id]
            
            if not orig_traj or not cloaked_traj:
                continue
            
            # Match points between trajectories
            matches = self.match_trajectory_points(orig_traj, cloaked_traj)
            
            # Calculate errors for matched points
            user_spatial_errors = []
            user_temporal_errors = []
            
            for orig_idx, cloaked_idx in matches:
                if orig_idx < len(orig_traj) and cloaked_idx < len(cloaked_traj):
                    orig_x, orig_y, orig_time = orig_traj[orig_idx]
                    cloaked_x, cloaked_y, cloaked_time = cloaked_traj[cloaked_idx]
                    
                    spatial_err = self.calculate_spatial_error((orig_x, orig_y), 
                                                              (cloaked_x, cloaked_y))
                    temporal_err = self.calculate_temporal_error(orig_time, cloaked_time)
                    
                    user_spatial_errors.append(spatial_err)
                    user_temporal_errors.append(temporal_err)
            
            if user_spatial_errors:
                results['user_stats'][user_id] = {
                    'mean_spatial_error': np.mean(user_spatial_errors),
                    'median_spatial_error': np.median(user_spatial_errors),
                    'max_spatial_error': np.max(user_spatial_errors),
                    'mean_temporal_error': np.mean(user_temporal_errors),
                    'compression_ratio': len(cloaked_traj) / len(orig_traj)
                }
                
                results['spatial_errors'].extend(user_spatial_errors)
                results['temporal_errors'].extend(user_temporal_errors)
                results['compression_ratios'].append(len(cloaked_traj) / len(orig_traj))
                results['trajectory_lengths'].append(len(orig_traj))
        
        # Summary statistics
        if results['spatial_errors']:
            results['summary'] = {
                'mean_spatial_error_km': np.mean(results['spatial_errors']),
                'median_spatial_error_km': np.median(results['spatial_errors']),
                'std_spatial_error_km': np.std(results['spatial_errors']),
                'mean_temporal_error_min': np.mean(results['temporal_errors']),
                'median_temporal_error_min': np.median(results['temporal_errors']),
                'mean_compression_ratio': np.mean(results['compression_ratios']),
                'privacy_gain': 1 / np.mean(results['compression_ratios']) if np.mean(results['compression_ratios']) > 0 else 0
            }
        
        print(f"  Mean spatial error: {results['summary']['mean_spatial_error_km']:.3f} km")
        print(f"  Mean temporal error: {results['summary']['mean_temporal_error_min']:.2f} min")
        print(f"  Compression ratio: {results['summary']['mean_compression_ratio']:.3f}")
        
        return results


# ======================================================================
# Visualization
# ======================================================================

class TemporalCloakingVisualizer:
    """Visualization tools for temporal cloaking results."""
    
    @staticmethod
    def ensure_results_folder():
        """Create results folder if it doesn't exist."""
        if not os.path.exists("results"):
            os.makedirs("results")
    
    @staticmethod
    def plot_trajectory_comparison(original_trajectories: Dict[int, List[Tuple]],
                                  cloaked_trajectories: Dict[int, List[Tuple]],
                                  num_users_to_plot: int = 5):
        """
        Plot original vs. cloaked trajectories for selected users.
        """
        TemporalCloakingVisualizer.ensure_results_folder()
        
        # Select random users to plot
        all_users = list(original_trajectories.keys())
        selected_users = random.sample(all_users, min(num_users_to_plot, len(all_users)))
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot original trajectories
        ax1 = axes[0]
        colors = plt.cm.Set1(np.linspace(0, 1, len(selected_users)))
        
        for i, user_id in enumerate(selected_users):
            traj = original_trajectories[user_id]
            if not traj:
                continue
            
            x_vals = [point[0] for point in traj]
            y_vals = [point[1] for point in traj]
            
            # Plot trajectory
            ax1.plot(x_vals, y_vals, color=colors[i], alpha=0.6, linewidth=2, 
                    label=f'User {user_id}')
            
            # Plot start and end points
            if len(traj) > 0:
                ax1.scatter(x_vals[0], y_vals[0], color=colors[i], s=100, 
                           marker='o', edgecolors='black', zorder=5)
                ax1.scatter(x_vals[-1], y_vals[-1], color=colors[i], s=100,
                           marker='s', edgecolors='black', zorder=5)
        
        ax1.set_title('Original Trajectories', fontsize=14, fontweight='bold')
        ax1.set_xlabel('X (km)')
        ax1.set_ylabel('Y (km)')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 10)
        
        # Plot cloaked trajectories
        ax2 = axes[1]
        
        for i, user_id in enumerate(selected_users):
            if user_id not in cloaked_trajectories:
                continue
            
            traj = cloaked_trajectories[user_id]
            if not traj:
                continue
            
            x_vals = [point[0] for point in traj]
            y_vals = [point[1] for point in traj]
            times = [point[2] for point in traj]
            
            # Plot trajectory
            ax2.plot(x_vals, y_vals, color=colors[i], alpha=0.6, linewidth=2, 
                    label=f'User {user_id}')
            
            # Plot generalized points
            scatter = ax2.scatter(x_vals, y_vals, color=colors[i], s=50, 
                                 alpha=0.8, zorder=5)
            
            # Add time labels for some points
            if len(traj) > 0:
                for j in range(0, len(traj), max(1, len(traj)//3)):
                    time_str = times[j].strftime("%H:%M")
                    ax2.annotate(time_str, (x_vals[j], y_vals[j]),
                                textcoords="offset points", xytext=(0,10),
                                ha='center', fontsize=8)
        
        ax2.set_title('Cloaked Trajectories (Temporal Cloaking)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('X (km)')
        ax2.set_ylabel('Y (km)')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right')
        ax2.set_xlim(0, 10)
        ax2.set_ylim(0, 10)
        
        plt.tight_layout()
        plt.savefig('results/trajectory_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return fig
    
    @staticmethod
    def plot_temporal_analysis(analyzer_results: Dict[str, Any]):
        """
        Plot temporal analysis of cloaking results.
        """
        TemporalCloakingVisualizer.ensure_results_folder()
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Spatial error distribution
        ax1 = axes[0, 0]
        if 'spatial_errors' in analyzer_results and analyzer_results['spatial_errors']:
            ax1.hist(analyzer_results['spatial_errors'], bins=50, alpha=0.7,
                    color='steelblue', edgecolor='black')
            ax1.axvline(np.mean(analyzer_results['spatial_errors']), 
                       color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(analyzer_results["spatial_errors"]):.3f} km')
            ax1.set_xlabel('Spatial Error (km)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Spatial Error Distribution')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # Temporal error distribution
        ax2 = axes[0, 1]
        if 'temporal_errors' in analyzer_results and analyzer_results['temporal_errors']:
            ax2.hist(analyzer_results['temporal_errors'], bins=50, alpha=0.7,
                    color='darkorange', edgecolor='black')
            ax2.axvline(np.mean(analyzer_results['temporal_errors']), 
                       color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(analyzer_results["temporal_errors"]):.1f} min')
            ax2.set_xlabel('Temporal Error (minutes)')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Temporal Error Distribution')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Compression ratio
        ax3 = axes[1, 0]
        if 'compression_ratios' in analyzer_results and analyzer_results['compression_ratios']:
            ax3.hist(analyzer_results['compression_ratios'], bins=30, alpha=0.7,
                    color='forestgreen', edgecolor='black')
            ax3.axvline(np.mean(analyzer_results['compression_ratios']), 
                       color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(analyzer_results["compression_ratios"]):.3f}')
            ax3.set_xlabel('Compression Ratio (cloaked/original)')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Trajectory Compression Distribution')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # Error correlation
        ax4 = axes[1, 1]
        if ('spatial_errors' in analyzer_results and 'temporal_errors' in analyzer_results and
            analyzer_results['spatial_errors'] and analyzer_results['temporal_errors']):
            min_len = min(len(analyzer_results['spatial_errors']), 
                         len(analyzer_results['temporal_errors']))
            ax4.scatter(analyzer_results['spatial_errors'][:min_len],
                       analyzer_results['temporal_errors'][:min_len],
                       alpha=0.5, s=10)
            ax4.set_xlabel('Spatial Error (km)')
            ax4.set_ylabel('Temporal Error (min)')
            ax4.set_title('Spatial vs Temporal Error Correlation')
            ax4.grid(True, alpha=0.3)
            
            # Add correlation coefficient
            if min_len > 1:
                corr = np.corrcoef(analyzer_results['spatial_errors'][:min_len],
                                  analyzer_results['temporal_errors'][:min_len])[0, 1]
                ax4.text(0.05, 0.95, f'Correlation: {corr:.3f}',
                        transform=ax4.transAxes, fontsize=10,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('Temporal Cloaking Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('results/temporal_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return fig
    
    @staticmethod
    def plot_privacy_utility_tradeoff(tradeoff_results: List[Dict[str, Any]]):
        """
        Plot privacy-utility tradeoff for different parameters.
        """
        TemporalCloakingVisualizer.ensure_results_folder()
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Extract data
        window_sizes = [r['window_size'] for r in tradeoff_results]
        k_values = [r['k_value'] for r in tradeoff_results]
        spatial_errors = [r['mean_spatial_error'] for r in tradeoff_results]
        temporal_errors = [r['mean_temporal_error'] for r in tradeoff_results]
        compression_ratios = [r['compression_ratio'] for r in tradeoff_results]
        privacy_gains = [r['privacy_gain'] for r in tradeoff_results]
        
        # Spatial error vs window size
        ax1 = axes[0, 0]
        scatter1 = ax1.scatter(window_sizes, spatial_errors, c=k_values, 
                              cmap='viridis', s=100, alpha=0.7)
        ax1.set_xlabel('Window Size (minutes)')
        ax1.set_ylabel('Mean Spatial Error (km)')
        ax1.set_title('Spatial Error vs Window Size')
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter1, ax=ax1, label='k-value')
        
        # Temporal error vs window size
        ax2 = axes[0, 1]
        scatter2 = ax2.scatter(window_sizes, temporal_errors, c=k_values,
                              cmap='plasma', s=100, alpha=0.7)
        ax2.set_xlabel('Window Size (minutes)')
        ax2.set_ylabel('Mean Temporal Error (minutes)')
        ax2.set_title('Temporal Error vs Window Size')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=ax2, label='k-value')
        
        # Privacy-utility tradeoff
        ax3 = axes[1, 0]
        for i, (window, k) in enumerate(zip(window_sizes, k_values)):
            ax3.scatter(spatial_errors[i], privacy_gains[i], s=100,
                       c=[window], cmap='cool', alpha=0.7,
                       label=f'W={window}, k={k}' if i % 3 == 0 else "")
        
        ax3.set_xlabel('Spatial Error (km)')
        ax3.set_ylabel('Privacy Gain (1/compression)')
        ax3.set_title('Privacy-Utility Tradeoff Space')
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='upper left', fontsize=8)
        
        # 3D tradeoff visualization
        from mpl_toolkits.mplot3d import Axes3D
        ax4 = fig.add_subplot(224, projection='3d')
        scatter4 = ax4.scatter(window_sizes, k_values, spatial_errors,
                              c=temporal_errors, cmap='hot', s=100, alpha=0.7)
        ax4.set_xlabel('Window Size (min)')
        ax4.set_ylabel('k-value')
        ax4.set_zlabel('Spatial Error (km)')
        ax4.set_title('3D Tradeoff Analysis')
        plt.colorbar(scatter4, ax=ax4, label='Temporal Error (min)')
        
        plt.suptitle('Temporal Cloaking: Privacy-Utility Tradeoff Analysis', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('results/privacy_utility_tradeoff.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return fig


# ======================================================================
# Main Simulation
# ======================================================================

def run_temporal_cloaking_simulation(num_users: int = 30,
                                    window_size: float = 15.0,
                                    k_value: int = 5,
                                    simulation_duration: float = 24.0):
    """
    Run complete temporal cloaking simulation.
    
    Args:
        num_users: Number of users to simulate
        window_size: Temporal window size in minutes
        k_value: k-anonymity parameter
        simulation_duration: Simulation duration in hours
    """
    print("=" * 70)
    print("TEMPORAL CLOAKING FOR LOCATION PRIVACY IN IOT SMART CITIES")
    print("=" * 70)
    
    # Step 1: Generate trajectories
    print("\n1. Generating User Trajectories...")
    simulator = TrajectorySimulator(
        city_size=(10.0, 10.0),
        num_users=num_users,
        simulation_duration_hours=simulation_duration,
        update_interval_minutes=1.0
    )
    original_trajectories = simulator.generate_trajectories()
    
    # Step 2: Apply temporal cloaking
    print("\n2. Applying Temporal Cloaking...")
    cloaking_algorithm = TemporalCloakingAlgorithm(
        window_size_minutes=window_size,
        k_anonymity=k_value,
        spatial_threshold_km=1.0
    )
    cloaked_trajectories = cloaking_algorithm.apply_temporal_cloaking(original_trajectories)
    
    # Step 3: Analyze results
    print("\n3. Analyzing Privacy-Utility Tradeoff...")
    analyzer = PrivacyUtilityAnalyzer()
    analysis_results = analyzer.analyze_trajectories(original_trajectories, cloaked_trajectories)
    
    # Step 4: Visualize results
    print("\n4. Generating Visualizations...")
    visualizer = TemporalCloakingVisualizer()
    
    # Plot trajectory comparison
    fig1 = visualizer.plot_trajectory_comparison(
        original_trajectories, cloaked_trajectories, num_users_to_plot=5
    )
    
    # Plot temporal analysis
    fig2 = visualizer.plot_temporal_analysis(analysis_results)
    
    # Prepare results for saving
    results = {
        'simulation_parameters': {
            'num_users': num_users,
            'window_size_minutes': window_size,
            'k_anonymity': k_value,
            'simulation_duration_hours': simulation_duration,
            'city_size': simulator.city_size
        },
        'algorithm_statistics': cloaking_algorithm.stats,
        'analysis_results': analysis_results,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save results to JSON
    with open('results/temporal_cloaking_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save trajectory data to CSV
    with open('results/trajectory_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'trajectory_type', 'x', 'y', 'timestamp'])
        
        for user_id, traj in original_trajectories.items():
            for x, y, timestamp in traj:
                writer.writerow([user_id, 'original', x, y, timestamp])
        
        for user_id, traj in cloaked_trajectories.items():
            for x, y, timestamp in traj:
                writer.writerow([user_id, 'cloaked', x, y, timestamp])
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to 'results/' folder:")
    print("  - trajectory_comparison.png")
    print("  - temporal_analysis.png")
    print("  - temporal_cloaking_results.json")
    print("  - trajectory_data.csv")
    
    # Print summary
    if 'summary' in analysis_results:
        summary = analysis_results['summary']
        print(f"\nSummary Statistics:")
        print(f"  Spatial Error: {summary['mean_spatial_error_km']:.3f} km (mean)")
        print(f"  Temporal Error: {summary['mean_temporal_error_min']:.1f} min (mean)")
        print(f"  Compression Ratio: {summary['mean_compression_ratio']:.3f}")
        print(f"  Privacy Gain: {summary['privacy_gain']:.2f}x")
    
    return original_trajectories, cloaked_trajectories, results


def run_parameter_sweep():
    """Run simulation with different parameters to analyze tradeoffs."""
    print("\n" + "=" * 70)
    print("PARAMETER SWEEP ANALYSIS")
    print("=" * 70)
    
    parameter_combinations = [
        {'window': 5, 'k': 2},
        {'window': 10, 'k': 3},
        {'window': 15, 'k': 5},
        {'window': 30, 'k': 8},
        {'window': 60, 'k': 10},
    ]
    
    tradeoff_results = []
    
    for params in parameter_combinations:
        print(f"\nTesting: Window={params['window']}min, k={params['k']}")
        
        # Run simulation
        simulator = TrajectorySimulator(
            city_size=(10.0, 10.0),
            num_users=30,
            simulation_duration_hours=12.0,  # Shorter for speed
            update_interval_minutes=1.0
        )
        original_trajectories = simulator.generate_trajectories()
        
        cloaking_algorithm = TemporalCloakingAlgorithm(
            window_size_minutes=params['window'],
            k_anonymity=params['k'],
            spatial_threshold_km=1.0
        )
        cloaked_trajectories = cloaking_algorithm.apply_temporal_cloaking(original_trajectories)
        
        analyzer = PrivacyUtilityAnalyzer()
        analysis_results = analyzer.analyze_trajectories(original_trajectories, cloaked_trajectories)
        
        if 'summary' in analysis_results:
            result = {
                'window_size': params['window'],
                'k_value': params['k'],
                'mean_spatial_error': analysis_results['summary']['mean_spatial_error_km'],
                'mean_temporal_error': analysis_results['summary']['mean_temporal_error_min'],
                'compression_ratio': analysis_results['summary']['mean_compression_ratio'],
                'privacy_gain': analysis_results['summary']['privacy_gain']
            }
            tradeoff_results.append(result)
    
    # Plot tradeoff analysis
    visualizer = TemporalCloakingVisualizer()
    visualizer.plot_privacy_utility_tradeoff(tradeoff_results)
    
    # Save tradeoff results
    with open('results/parameter_sweep_results.json', 'w') as f:
        json.dump(tradeoff_results, f, indent=2)
    
    print(f"\nParameter sweep complete. Results saved to 'results/parameter_sweep_results.json'")
    
    return tradeoff_results


# ======================================================================
# Main Entry Point
# ======================================================================

def main():
    """Main entry point for the temporal cloaking simulation."""
    parser = argparse.ArgumentParser(description='Temporal Cloaking Simulation for IoT Smart Cities')
    parser.add_argument('--users', type=int, default=30,
                       help='Number of users to simulate (default: 30)')
    parser.add_argument('--window', type=float, default=15.0,
                       help='Temporal window size in minutes (default: 15)')
    parser.add_argument('--k', type=int, default=5,
                       help='k-anonymity parameter (default: 5)')
    parser.add_argument('--duration', type=float, default=24.0,
                       help='Simulation duration in hours (default: 24)')
    parser.add_argument('--sweep', action='store_true',
                       help='Run parameter sweep analysis')
    
    args = parser.parse_args()
    
    if args.sweep:
        run_parameter_sweep()
    else:
        run_temporal_cloaking_simulation(
            num_users=args.users,
            window_size=args.window,
            k_value=args.k,
            simulation_duration=args.duration
        )


if __name__ == "__main__":
    main()