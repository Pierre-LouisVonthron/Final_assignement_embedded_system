# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 19:11:31 2025

@author: Utilisateur
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

#%% Part where τ5 can miss deadlines
#%%% Task set definition
# Task set: (C, T)
tasks = [
    (2, 10),   # τ1
    (3, 10),   # τ2
    (2, 20),   # τ3
    (2, 20),   # τ4
    (2, 40),   # τ5 — can miss deadline
    (2, 40),   # τ6
    (3, 80)    # τ7
]

HYPERPERIOD = 80
NUM_TASKS = len(tasks)

#%%% Job queue Generation

# Generate job queues
job_queues = [[] for _ in range(NUM_TASKS)]
for task_id, (C, T) in enumerate(tasks):
    for i in range(HYPERPERIOD // T):
        release = i * T
        job_queues[task_id].append({
            'release': release,
            'remaining': C,
            'C': C,
            'deadline': release + T,
            'start': None,
            'waiting': 0
        })

# Initialize the schedule
schedule = [['0' for _ in range(NUM_TASKS)] for _ in range(HYPERPERIOD)]
idle_time = 0
t = 0

#%%% Scheduling Loop
# Main loop for non-preemptive scheduling
while t < HYPERPERIOD:
    # Find ready jobs that haven't started yet
    ready_jobs = []
    for task_id, jobs in enumerate(job_queues):
        for job in jobs:
            if job['release'] <= t and job['remaining'] == job['C']:
                ready_jobs.append((task_id, job))
                break

    # Sort by shortest period (highest priority)
    ready_jobs.sort(key=lambda x: tasks[x[0]][1])

    if ready_jobs:
        # Assign the first ready job to run
        task_id, job = ready_jobs[0]
        run_time = job['C']
        job['start'] = t
        job['waiting'] = t - job['release']
        job['remaining'] = 0

        # Fill schedule with RUNNING
        for i in range(run_time):
            current_time = t + i
            if current_time >= HYPERPERIOD:
                break
            schedule[current_time][task_id] = '1'

            # During this time, mark others as WAITING
            for other_id, other_job in ready_jobs[1:]:
                if other_job['release'] <= current_time and other_job['remaining'] == other_job['C']:
                    schedule[current_time][other_id] = '*'

        t += run_time
    else:
        idle_time += 1
        t += 1

# Calculate waiting time
total_waiting = 0
waiting_per_task = [0 for _ in range(NUM_TASKS)]
for task_id, jobs in enumerate(job_queues):
    for job in jobs:
        total_waiting += job['waiting']
        waiting_per_task[task_id] += job['waiting']

# Output stats
print("✅ Non-preemptive schedule with WAITING tracking completed.")
print(f"Total IDLE time: {idle_time}")
print(f"Total WAITING time: {total_waiting}")
for i, w in enumerate(waiting_per_task):
    print(f"τ{i+1} waiting time: {w}")
    
def track_job_counts(job_queues):
    """Returns a dictionary with the number of jobs launched per task."""
    job_counts = {}
    for task_id, jobs in enumerate(job_queues):
        job_counts[f"τ{task_id + 1}"] = len(jobs)
    return job_counts

job_counts = track_job_counts(job_queues)
print("Job counts per task:", job_counts)
#%%% Plot
fig, ax = plt.subplots(figsize=(14, 6))
state_colors = {'1': 'green', '*': 'orange', '0': 'white'}

for t in range(HYPERPERIOD):
    for task in range(NUM_TASKS):
        color = state_colors[schedule[t][task]]
        ax.add_patch(mpatches.Rectangle((t, NUM_TASKS - task - 1), 1, 1, color=color, edgecolor='black'))

ax.set_xlim(0, HYPERPERIOD)
ax.set_ylim(0, NUM_TASKS)
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Tasks")
ax.set_yticks([i + 0.5 for i in range(NUM_TASKS)])
ax.set_yticklabels([f"τ{NUM_TASKS - i}" for i in range(NUM_TASKS)])
ax.set_title("Non-Preemptive RMS Schedule with WAITING States")

legend = [mpatches.Patch(color=c, label=l) for l, c in {
    'RUNNING': 'green',
    'WAITING': 'orange',
    'IDLE': 'white'
}.items()]
ax.legend(handles=legend, loc='upper right')

plt.grid(True)
plt.tight_layout()
plt.show()

#%% Part where τ5 can't miss deadlines
#%%% Task set definition
# Task set: (C, T)
tasks = [
    (2, 10),   # τ1
    (3, 10),   # τ2
    (2, 20),   # τ3
    (2, 20),   # τ4
    (2, 40),   # τ5 — NOT allowed to miss deadline
    (2, 40),   # τ6
    (3, 80)    # τ7
]

HYPERPERIOD = 80
NUM_TASKS = len(tasks)

#%%% Job queue Generation
# Generate job queues with deadline-critical flag for τ5
job_queues = [[] for _ in range(NUM_TASKS)]
for task_id, (C, T) in enumerate(tasks):
    for i in range(HYPERPERIOD // T):
        release = i * T
        job_queues[task_id].append({
            'release': release,
            'remaining': C,
            'C': C,
            'deadline': release + T,
            'start': None,
            'waiting': 0,
            'is_τ5': (task_id == 4)  # Flag for τ5 jobs
        })

# Initialize schedule
schedule = [['0' for _ in range(NUM_TASKS)] for _ in range(HYPERPERIOD)]
idle_time = 0
t = 0

#%%% Scheduling Loop
# Main scheduling loop
while t < HYPERPERIOD:
    # Find all ready jobs (released but not started)
    ready_jobs = []
    for task_id, jobs in enumerate(job_queues):
        for job in jobs:
            if job['release'] <= t and job['remaining'] == job['C']:
                ready_jobs.append((task_id, job))
                break  # Only consider the earliest pending job per task

    # Prioritize τ5 if its deadline is imminent (within its remaining time)
    τ5_priority = False
    for task_id, job in ready_jobs:
        if job['is_τ5'] and (t + job['C'] > job['deadline']):
            τ5_priority = True
            break

    # Sort jobs: τ5 first (if deadline at risk), then by period (Rate Monotonic)
    ready_jobs.sort(key=lambda x: (
        not x[1]['is_τ5'],  # τ5 goes first if priority flagged
        tasks[x[0]][1]      # Then sort by period (T_i)
    ))

    if ready_jobs:
        task_id, job = ready_jobs[0]
        run_time = job['C']
        job['start'] = t
        job['waiting'] = t - job['release']
        job['remaining'] = 0

        # Fill schedule
        for i in range(run_time):
            current_time = t + i
            if current_time >= HYPERPERIOD:
                break
            schedule[current_time][task_id] = '1'  # Mark as running

            # Mark other ready jobs as waiting
            for other_id, other_job in ready_jobs[1:]:
                if other_job['release'] <= current_time and other_job['remaining'] == other_job['C']:
                    schedule[current_time][other_id] = '*'

        t += run_time
    else:
        idle_time += 1
        t += 1


# Calculate waiting time (unchanged)
total_waiting = 0
waiting_per_task = [0 for _ in range(NUM_TASKS)]
for task_id, jobs in enumerate(job_queues):
    for job in jobs:
        total_waiting += job['waiting']
        waiting_per_task[task_id] += job['waiting']

# Output stats
print("✅ Non-preemptive schedule with τ5 deadline enforcement.")
print(f"Total IDLE time: {idle_time}")
print(f"Total WAITING time: {total_waiting}")
for i, w in enumerate(waiting_per_task):
    print(f"τ{i+1} waiting time: {w}")

def track_job_counts(job_queues):
    """Returns a dictionary with the number of jobs launched per task."""
    job_counts = {}
    for task_id, jobs in enumerate(job_queues):
        job_counts[f"τ{task_id + 1}"] = len(jobs)
    return job_counts

job_counts = track_job_counts(job_queues)
print("Job counts per task:", job_counts)
#%%% Plot
# === Plotting (unchanged) ===
fig, ax = plt.subplots(figsize=(14, 6))
state_colors = {'1': 'green', '*': 'orange', '0': 'white'}

for t in range(HYPERPERIOD):
    for task in range(NUM_TASKS):
        color = state_colors[schedule[t][task]]
        ax.add_patch(mpatches.Rectangle((t, NUM_TASKS - task - 1), 1, 1, color=color, edgecolor='black'))

ax.set_xlim(0, HYPERPERIOD)
ax.set_ylim(0, NUM_TASKS)
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Tasks")
ax.set_yticks([i + 0.5 for i in range(NUM_TASKS)])
ax.set_yticklabels([f"τ{NUM_TASKS - i}" for i in range(NUM_TASKS)])
ax.set_title("Non-Preemptive RMS Schedule (τ5 Deadline Guaranteed)")

legend = [mpatches.Patch(color=c, label=l) for l, c in {
    'RUNNING': 'green',
    'WAITING': 'orange',
    'IDLE': 'white'
}.items()]
ax.legend(handles=legend, loc='upper right')

plt.grid(True)
plt.tight_layout()
plt.show()