# Petri Net Analyzer - CO2011 Assignment

**Symbolic and Algebraic Reasoning in Petri Nets**

This project implements a comprehensive Petri net analyzer that performs symbolic and algebraic reasoning on 1-safe Petri nets. The implementation covers five core tasks: PNML parsing, explicit reachability computation, symbolic reachability using Binary Decision Diagrams (BDD), deadlock detection, and optimization over reachable markings.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Implementation Details](#implementation-details)
- [Test Cases](#test-cases)
- [Project Structure](#project-structure)
- [Output Format](#output-format)

---

## Overview

This project addresses five fundamental problems in Petri net analysis:

### Task 1: PNML Parsing (5%)
Parses standard Petri Net Markup Language (PNML) files to extract:
- Places with initial markings
- Transitions
- Arcs with weights
- Structural verification (bipartite property, 1-safe property)
- Internal matrix representations (pre-incidence and post-incidence matrices)

### Task 2: Explicit Reachability (5%)
Computes all reachable markings using breadth-first search (BFS):
- Enumerates the complete state space
- Reports execution time and memory usage
- Uses efficient queue-based state exploration

### Task 3: Symbolic Reachability (40%)
Implements symbolic reachability computation using Binary Decision Diagrams:
- BDD-based fixed-point computation
- Symbolic encoding of transition relations
- Iterative image computation
- Performance comparison with explicit method

### Task 4: Deadlock Detection (20%)
Detects deadlock states (markings where no transition is enabled):
- Integer Linear Programming (ILP) formulation for finding dead markings
- BDD membership oracle for reachability verification
- Multiple detection strategies (explicit, symbolic, ILP-based)

### Task 5: Optimization (20%)
Maximizes a linear objective function over all reachable markings:
- ILP formulation with customizable objective weights
- BDD-based verification of reachability
- Finds optimal marking among reachable states

---

## Requirements

### System Requirements
- Python 3.7 or higher
- CUDD library (for BDD support)

### Python Dependencies
- dd - Binary Decision Diagrams library
- pulp - Integer Linear Programming solver

---

## Installation

### 1. Install Python Dependencies

Using pip:
```bash
pip install dd pulp
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

### 2. Install CUDD Library

**macOS:**
```bash
brew install cudd
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libcudd-dev
```

**Windows:**
CUDD may require Windows Subsystem for Linux (WSL) or pre-built wheels. Alternative: use pyeda instead of dd (requires code modifications).

---

## Usage

### Basic Usage

Run all five tasks on a PNML file:

```bash
python petri_net_analyzer.py <pnml_file>
```

**Example:**
```bash
python petri_net_analyzer.py test_simple.xml
```

### Custom Objective Weights (Task 5)

Specify objective weights for optimization (one weight per place):

```bash
python petri_net_analyzer.py <pnml_file> <weights>
```

**Example:**
```bash
python petri_net_analyzer.py test_manufacturing.xml 1,1,1,1,2,0,3
```

The weights correspond to places in the order they appear in the PNML file.

### Running All Test Cases

Execute the automated test runner to run all test cases:

```bash
python run_all_tests.py
```

This script runs the analyzer on all .xml files in the directory and provides a summary report.

---

## Implementation Details

### Data Structures

#### PetriNet Class
The main data structure representing a Petri net:

```python
class PetriNet:
    places: Dict[str, Place]           # Place ID -> Place object
    transitions: Dict[str, Transition] # Transition ID -> Transition object
    arcs: List[Arc]                    # List of all arcs
    pre_matrix: Dict                   # Pre-incidence matrix
    post_matrix: Dict                  # Post-incidence matrix
    initial_marking: Tuple[int, ...]   # Initial marking vector
```

#### Core Methods
- is_transition_enabled(marking, transition_id) - Checks if a transition can fire at a given marking
- fire_transition(marking, transition_id) - Executes a transition and returns the new marking
- is_dead_marking(marking) - Checks if no transitions are enabled at a marking

### Algorithms

#### Task 2: Explicit Reachability
- **Algorithm**: Breadth-First Search (BFS)
- **Complexity**: O(|R| × |T|) where R = number of reachable markings, T = number of transitions
- **Data Structures**: Set for visited states, deque for exploration queue
- **Termination**: Converges when no new markings are discovered

#### Task 3: Symbolic Reachability
- **Algorithm**: BDD-based fixed-point iteration
- **Variables**: x_p (current state) and x'_p (next state) for each place p
- **Transition Relation**: R(x, x') encodes all transition firing rules
- **Fixed-Point Computation**: Reach* = Reach ∪ Image(Reach) until no new states are added
- **Encoding**: Binary encoding for 1-safe nets (each place requires 1 bit)

#### Task 4: Deadlock Detection
- **Method 1 (Explicit)**: Enumerate all reachable markings and check for dead states
- **Method 2 (ILP)**: Formulate as Integer Linear Program with BDD membership oracle
  - Variables: M_p ∈ {0,1} for each place p
  - Constraints: For each transition t, at least one pre-place has insufficient tokens
  - Verification: Check if candidate marking is reachable using BDD membership oracle

#### Task 5: Optimization
- **Objective**: Maximize c^T M where M is a reachable marking
- **Method**: ILP with linear objective and reachability constraints
- **Verification**: Use BDD membership oracle to ensure optimum is reachable
- **Flexibility**: Supports arbitrary linear objective functions

### Implementation Notes

1. **1-Safe Property**: All test cases assume at most 1 token per place, which simplifies BDD encoding
2. **Matrix Representation**: Pre and post matrices enable efficient enabled/firing checks
3. **BDD Variable Ordering**: Places are ordered by ID to ensure consistent BDD construction
4. **Error Handling**: Robust parsing with validation of PNML structure and consistency checks

---

## Test Cases

The project includes 12 diverse test cases covering fundamental and advanced Petri net patterns.

### Basic Patterns (7 tests)

| File | Places | Transitions | Description |
|------|--------|-------------|-------------|
| test_simple.xml | 2 | 1 | Simplest net - basic token flow |
| test_cycle.xml | 3 | 3 | Cyclic execution - no deadlock |
| test_deadlock.xml | 3 | 2 | Contains reachable deadlock at (0,1,0) |
| test_no_deadlock.xml | 3 | 2 | Deadlock-free by design |
| test_choice.xml | 3 | 2 | Choice/conflict pattern |
| test_synchronization.xml | 3 | 1 | Synchronization barrier pattern |
| 1-safePetriNet.xml | 2 | 1 | Demonstrates 1-safe property |

### Advanced Patterns (5 tests)

| File | Places | Transitions | Description |
|------|--------|-------------|-------------|
| test_parallel_choice.xml | 4 | 4 | Parallel execution with choice |
| test_mutex.xml | 5 | 4 | Mutual exclusion (2 processes) |
| test_free_choice.xml | 5 | 4 | Free choice net (important Petri net class) |
| test_manufacturing.xml | 7 | 6 | Assembly line workflow simulation |
| test_dining_philosophers.xml | 9 | 6 | Classic dining philosophers (3 philosophers) |

**All test cases satisfy the 1-safe property** (maximum 1 token per place).

---

## Project Structure

```
math-modeling/
├── petri_net_analyzer.py    # Main implementation (all 5 tasks)
├── run_all_tests.py          # Automated test runner
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
│
├── test_simple.xml          # Basic test cases
├── test_cycle.xml
├── test_deadlock.xml
├── test_no_deadlock.xml
├── test_choice.xml
├── test_synchronization.xml
├── 1-safePetriNet.xml
│
├── test_parallel_choice.xml # Advanced test cases
├── test_mutex.xml
├── test_free_choice.xml
├── test_manufacturing.xml
└── test_dining_philosophers.xml
```

---

## Output Format

The analyzer produces structured output for each task:

```
===============================
Task 1: Parsing PNML file
===============================
File: test_simple.xml
Places: 2
Transitions: 1
Arcs: 2
Initial marking: (1, 0)

===============================
Task 2: Explicit Reachability
===============================
Reachable markings: 2
Time: 0.0001s
Memory: 240 bytes

===============================
Task 3: Symbolic Reachability (BDD)
===============================
BDD computation complete
Reachable markings: 2
Time: 0.0015s
Iterations: 1

===============================
Task 4: Deadlock Detection
===============================
Deadlock found: (0, 1)
OR
No deadlock found

===============================
Task 5: Optimization
===============================
Objective: [1, 1]
Optimal value: 1
Optimal marking: (1, 0)


---

## References

- **PNML Specification**: ISO/IEC 15909-2
- **BDD Library**: dd Python package (CUDD backend)
- **ILP Solver**: PuLP (Python Linear Programming)
- **Course**: CO2011 - Formal Methods and Software Verification

---

## Author

This implementation was developed as part of the CO2011 assignment on Symbolic and Algebraic Reasoning in Petri Nets.
