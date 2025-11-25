# Petri Net Analyzer - CO2011 Assignment

Symbolic and Algebraic Reasoning in Petri Nets

## Overview

This project implements a comprehensive Petri net analyzer that performs:
1. **PNML Parsing**: Read and parse standard PNML files
2. **Explicit Reachability**: Enumerate all reachable markings using BFS
3. **Symbolic Reachability**: Compute reachable markings using BDD
4. **Deadlock Detection**: Detect deadlocks using ILP + BDD
5. **Optimization**: Optimize over reachable markings

## Installation

### Prerequisites

- Python 3.7 or higher
- CUDD library (for BDD support)

### Install Python Dependencies

```bash
pip install dd pulp
```

### Install CUDD Library

**macOS:**
```bash
brew install cudd
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libcudd-dev
```

**Windows:**
May require WSL or use pre-built wheels. Alternatively, you can use `pyeda` instead of `dd` (modify imports accordingly).

## Usage

### Basic Usage

Run all tasks on a PNML file:

```bash
python petri_net_analyzer.py <pnml_file>
```

Example:
```bash
python petri_net_analyzer.py test_simple.xml
```

### With Custom Objective Weights

For Task 5 (optimization), specify objective weights:

```bash
python petri_net_analyzer.py test_simple.xml 1,2,3
```

The weights correspond to places in the order they appear in the PNML file.

### Programmatic Usage

```python
from petri_net_analyzer import *

# Parse PNML file
pn = parse_pnml("test_simple.xml")

# Task 2: Explicit reachability
reachable = explicit_reachability(pn)

# Task 3: Symbolic reachability
bdd_result = symbolic_reachability_bdd(pn)

# Task 4: Deadlock detection
deadlock = deadlock_detection(pn, reachable, bdd_result)

# Task 5: Optimization
weights = [1, 2, 3]  # One weight per place
result = optimize_reachable_markings(pn, weights, reachable, bdd_result)
```

## Test Files

The repository includes several test PNML files:

1. **test_simple.xml**: Simple 2-place, 1-transition net
   - Initial: (1, 0)
   - Reachable: (1, 0), (0, 1)
   - No deadlock

2. **test_deadlock.xml**: Net with a deadlock
   - Initial: (1, 0, 0)
   - Deadlock: (0, 1, 0) - transition t2 requires both p2 and p3, but p3 never gets a token

3. **test_cycle.xml**: Net with a cycle
   - Initial: (1, 0, 0)
   - Cycle: p1 → t1 → p2 → t2 → p3 → t3 → p1
   - No deadlock

4. **test_parallel.xml**: Net with parallel execution
   - Initial: (1, 0, 0, 0)
   - Fork-join pattern with parallel paths
   - Multiple reachable states

## Project Structure

```
math-modeling/
├── petri_net_analyzer.py    # Main implementation (all tasks)
├── TASK_GUIDE.md            # Detailed guide for each task
├── README.md                # This file
├── test_simple.xml          # Simple test case
├── test_deadlock.xml        # Deadlock test case
├── test_cycle.xml           # Cycle test case
└── test_parallel.xml         # Parallel execution test case
```

## Libraries Used

### Core Libraries

- **xml.etree.ElementTree** (built-in): PNML parsing
- **dd**: Binary Decision Diagrams for symbolic reachability
- **pulp**: Integer Linear Programming for deadlock detection and optimization

### Library Documentation

- **dd**: https://github.com/tulip-control/dd
- **pulp**: https://github.com/coin-or/pulp

## Task Breakdown

### Task 1: PNML Parsing (5%)
- Parse places, transitions, arcs
- Extract initial markings and arc weights
- Verify consistency

### Task 2: Explicit Reachability (5%)
- BFS-based enumeration
- Time and memory reporting

### Task 3: Symbolic Reachability (40%)
- BDD-based fixed-point computation
- Comparison with explicit method

### Task 4: Deadlock Detection (20%)
- ILP formulation
- BDD membership checking
- Report deadlock if found

### Task 5: Optimization (20%)
- Maximize linear objective over reachable markings
- ILP + BDD approach

### Task 6: Report (10%)
- See TASK_GUIDE.md for theoretical background and implementation details

## Output Format

The program outputs results for each task:

```
============================================================
TASK 1: PNML PARSING
============================================================
✓ Petri net structure is consistent
✓ PNML file parsed successfully!
  Places: 2
  Transitions: 1
  Arcs: 2
  Initial marking: (1, 0)

=== Task 2: Explicit Reachability Computation (BFS) ===
✓ Found 2 reachable markings
  Computation time: 0.0001 seconds
  Memory: ~256 bytes

=== Task 3: Symbolic Reachability Computation (BDD) ===
✓ Found 2 reachable markings
  Computation time: 0.0123 seconds
  Iterations: 2
  BDD node count: 15

=== Task 4: Deadlock Detection (ILP + BDD) ===
✓ No deadlock found
  Detection time: 0.0005 seconds

=== Task 5: Optimization over Reachable Markings ===
✓ Optimal marking found: (0, 1)
  Optimal value: 2
  Computation time: 0.0002 seconds
```

## Troubleshooting

### BDD Library Not Found

If you see "Warning: dd library not found":
```bash
pip install dd
```

If installation fails, you may need to install CUDD first (see Installation section).

### ILP Solver Issues

If pulp can't find a solver:
```bash
# Install CBC solver (default for pulp)
# On macOS:
brew install cbc

# On Ubuntu:
sudo apt-get install coinor-cbc
```

### Memory Issues

For large Petri nets, the explicit method may run out of memory. Use the BDD method instead, which is more memory-efficient.

## Theory and Implementation Details

See **TASK_GUIDE.md** for:
- Theoretical background for each method
- Implementation design and data structures
- Algorithm explanations
- Performance considerations

## Assignment Requirements

This implementation satisfies all assignment requirements:

- ✅ PNML parsing with consistency checks
- ✅ Explicit reachability (BFS)
- ✅ Symbolic reachability (BDD)
- ✅ Deadlock detection (ILP + BDD)
- ✅ Optimization over reachable markings
- ✅ Clear code structure and documentation

## License

This code is for academic use only as part of CO2011 assignment.
Redistribution without permission is prohibited.

## Authors

CO2011 Assignment - Group Implementation

## References

1. Bryant, R. E. (1986). Graph-based algorithms for boolean function manipulation.
2. Pastor, E., Cortadella, J., & Roig, O. (2001). Symbolic analysis of bounded Petri nets.
3. Murata, T. (1989). Petri nets: Properties, analysis and applications.

