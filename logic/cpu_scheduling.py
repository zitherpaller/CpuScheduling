"""
CPU scheduling calculations (NO window/GUI code in this file).

Keeping the math separate from the screen has two benefits:
  * the algorithms are easy to read and to test on their own
  * adding SJF / Priority / Round Robin later only means adding
    one more function here and one line in ALGORITHMS at the bottom

Every algorithm takes a list of processes and returns TWO things:

  rows     -> one dict per process with its results (start, finish, ...)
  segments -> the Gantt chart as a list of (label, start, end) tuples,
              where label is a process ID or "IDLE" when the CPU waits

A process is a dict like:  {"pid": "P1", "arrival": 0, "burst": 5}
"""
import heapq    # gives us a "heap": a waiting line that hands back the smallest item first


#CHECK FCFS ALGORITHM

def fcfs(processes):
    """First Come, First Served.

    The process that ARRIVES first runs first, and it runs to the end
    (no interruptions). If two processes arrive at the same time, the one
    that was entered first goes first.
    """
    # sorted() keeps the original order for ties ("stable"), which is exactly
    # the tie rule we want.
    order = sorted(processes, key=lambda p: p["arrival"])

    time = 0                 # this is where the the programs start(Current time)
    rows = []
    segments = []

    for p in order:
        # If the CPU is free but the next process hasn't arrived yet,
        # the CPU sits idle until it shows up.
        if time < p["arrival"]:
            segments.append(("IDLE", time, p["arrival"]))
            time = p["arrival"]

        #FOR THE MAIN CALCULATIONS, WE NEED TO CALCULATE THE START TIME, FINISH TIME, TURNAROUND TIME AND WAITING TIME FOR EACH PROCESS
        start = time                          # the first time the process gets the task
        finish = start + p["burst"]           # for completion time
        turnaround = finish - p["arrival"]    # total time from arrival to finish
        waiting = turnaround - p["burst"]     # time spent waiting (not running)

        rows.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": start,
            "finish": finish,
            "turnaround": turnaround,
            "waiting": waiting,
        })
        segments.append((p["pid"], start, finish))
        time = finish                         # the CPU is busy until here

    return rows, segments


#CHECK SJF ALGORITHM

def sjf(processes):
    """Shortest Job First (non-preemptive).

    Whenever the CPU becomes free, look at every process that has ALREADY
    ARRIVED and pick the one with the SMALLEST burst time. It then runs to
    the end (no interruptions, that is what "non-preemptive" means).

    Ties (same burst): the one that arrived earlier goes first; if they
    also arrived together, the one that was entered first goes first.
    """
    # Sort by arrival so we can walk through them in the order they show up.
    # We keep each process's original position (index) for the tie rule.
    arrivals = sorted(enumerate(processes), key=lambda pair: pair[1]["arrival"])

    time = 0
    rows = []
    segments = []
    next_in = 0          # position in `arrivals` of the next process not yet in line
    waiting_line = []    # a "heap": a line that always hands back the SMALLEST item

    while next_in < len(arrivals) or waiting_line:
        # 1) Move everyone who has arrived by now into the waiting line.
        #    Each entry is (burst, arrival, index, process); Python compares the
        #    first item first, so the shortest burst comes out first, and the
        #    next items break ties exactly as described above.
        while next_in < len(arrivals) and arrivals[next_in][1]["arrival"] <= time:
            index, p = arrivals[next_in]
            heapq.heappush(waiting_line, (p["burst"], p["arrival"], index, p))
            next_in += 1

        # 2) Nobody is waiting: the CPU idles until the next process arrives.
        if not waiting_line:
            next_arrival = arrivals[next_in][1]["arrival"]
            segments.append(("IDLE", time, next_arrival))
            time = next_arrival
            continue              # go back and let that process into the line

        # 3) Take the shortest job out of the line and run it to the end.
        burst, arrival, index, p = heapq.heappop(waiting_line)
        start = time
        finish = start + burst
        turnaround = finish - arrival
        waiting = turnaround - burst

        rows.append({
            "pid": p["pid"],
            "arrival": arrival,
            "burst": burst,
            "start": start,
            "finish": finish,
            "turnaround": turnaround,
            "waiting": waiting,
        })
        segments.append((p["pid"], start, finish))
        time = finish

    return rows, segments


#CHECK SRT ALGORITHM

def srt(processes):
    """Shortest Remaining Time (also called SRTF), the PREEMPTIVE version of SJF.

    The CPU always runs the process with the LEAST TIME LEFT. When a new
    process arrives, we compare its burst with what the running process
    still has left; if the newcomer is shorter, it takes the CPU right away
    and the old one waits with its remaining time saved.

    Ties (same remaining time): earlier arrival first, then entered first.
    The running process is not interrupted by an equal one.
    """
    arrivals = sorted(enumerate(processes), key=lambda pair: pair[1]["arrival"])

    time = 0
    next_in = 0
    waiting_line = []       # heap of (remaining, arrival, index, process)
    first_start = {}        # index -> the first time that process got the CPU
    rows = []
    segments = []

    def add_block(label, start, end):
        """Add a Gantt block, joining it to the previous one if it's the same
        process continuing (so P1 running 0-1 then 1-3 shows as one block)."""
        if segments and segments[-1][0] == label and segments[-1][2] == start:
            segments[-1] = (label, segments[-1][1], end)
        else:
            segments.append((label, start, end))

    while next_in < len(arrivals) or waiting_line:
        # 1) Let in everyone who has arrived by now.
        while next_in < len(arrivals) and arrivals[next_in][1]["arrival"] <= time:
            index, p = arrivals[next_in]
            heapq.heappush(waiting_line, (p["burst"], p["arrival"], index, p))
            next_in += 1

        # 2) Nobody is waiting: the CPU idles until the next arrival.
        if not waiting_line:
            next_arrival = arrivals[next_in][1]["arrival"]
            add_block("IDLE", time, next_arrival)
            time = next_arrival
            continue

        # 3) Take the process with the least time left.
        remaining, arrival, index, p = heapq.heappop(waiting_line)
        first_start.setdefault(index, time)      # remember only the FIRST time

        # 4) Run it until it finishes OR until the next process arrives,
        #    whichever comes first (that is the moment someone could interrupt).
        run_until = time + remaining
        if next_in < len(arrivals):
            run_until = min(run_until, arrivals[next_in][1]["arrival"])
        add_block(p["pid"], time, run_until)
        remaining -= run_until - time
        time = run_until

        if remaining > 0:
            # Interrupted: back into the line with its smaller remaining time.
            heapq.heappush(waiting_line, (remaining, arrival, index, p))
        else:
            # Finished: now we can work out its results.
            turnaround = time - arrival
            rows.append({
                "pid": p["pid"],
                "arrival": arrival,
                "burst": p["burst"],
                "start": first_start[index],
                "finish": time,
                "turnaround": turnaround,
                "waiting": turnaround - p["burst"],   # total time NOT running
            })

    return rows, segments


def summarize(rows, segments):
    """Work out the averages and CPU utilization shown under the results."""
    n = len(rows)
    if n == 0:
        return {"avg_waiting": 0.0, "avg_turnaround": 0.0,
                "cpu_utilization": 0.0, "total_time": 0}

    total_time = segments[-1][2]                      # when the last block ends
    busy_time = sum(end - start for label, start, end in segments
                    if label != "IDLE")               # time the CPU really worked
    return {
        "avg_waiting": sum(r["waiting"] for r in rows) / n,
        "avg_turnaround": sum(r["turnaround"] for r in rows) / n,
        "cpu_utilization": busy_time / total_time * 100 if total_time else 0.0,
        "total_time": total_time,
    }


# The screen reads this dictionary to fill its algorithm dropdown.
# To add an algorithm later: write the function above, then add a line here.
ALGORITHMS = {
    "FCFS": fcfs,
    "SJF": sjf,
    "SRT": srt,
}

# One-line explanation shown on the screen for the chosen algorithm.
DESCRIPTIONS = {
    "FCFS": "FCFS - First Come, First Served: whoever arrives first "
            "gets the CPU first and keeps it until done.",
    "SJF": "SJF - Shortest Job First (non-preemptive): when the CPU is free, "
           "the arrived process with the smallest burst time goes next.",
    "SRT": "SRT - Shortest Remaining Time (preemptive SJF): the CPU always runs "
           "the process with the least time left, and a shorter newcomer interrupts.",
}