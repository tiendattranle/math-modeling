# Petri Net Analyzer - CO2011 Assignment

**Symbolic and Algebraic Reasoning in Petri Nets**

This project implements a comprehensive Petri net analyzer with 5 core tasks:
1. PNML parsing
2. Explicit reachability computation (BFS)
3. Symbolic reachability using Binary Decision Diagrams (BDD)
4. Deadlock detection using ILP + BDD
5. Optimization over reachable markings

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Test Files](#test-files)
- [Project Structure](#project-structure)
- [Implementation Details](#implementation-details)
- [Output Format](#output-format)
- [Troubleshooting](#troubleshooting)

---

## Features

### ✓ Task 1: PNML Parsing (5%)
- Parse standard PNML files
- Extract places, transitions, arcs with weights
- Verify structural consistency (bipartite, 1-safe)
- Build internal matrices for efficient computation

### ✓ Task 2: Explicit Reachability (5%)
- BFS-based enumeration of all reachable markings
- Time and memory reporting
- Efficient state exploration using queues

### ✓ Task 3: Symbolic Reachability (40%)
- BDD-based fixed-point computation
- Symbolic transition relation encoding
- Iterative image computation
- Performance comparison with explicit method

### ✓ Task 4: Deadlock Detection (20%)
- ILP formulation for dead markings
- BDD membership oracle for reachability checking
- Multiple detection strategies (explicit, symbolic, ILP)

### ✓ Task 5: Optimization (20%)
- Maximize linear objective over reachable markings
- ILP + BDD verification approach
- Customizable objective weights

---

## Requirements

### System Requirements
- Python 3.7 or higher
- CUDD library (for BDD support)

### Python Libraries
- `dd` - Binary Decision Diagrams
- `pulp` - Integer Linear Programming

---

## Installation

### 1. Install Python Dependencies

```bash
pip install dd pulp
```

Or use the requirements file:

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
May require WSL or pre-built wheels. Alternatively, use `pyeda` instead of `dd` (requires code modifications).

---

## Usage

### Basic Usage

Run all 5 tasks on a PNML file:

```bash
python petri_net_analyzer.py <pnml_file>
```

**Example:**
```bash
python petri_net_analyzer.py test_simple.xml
```

### With Custom Objective Weights (Task 5)

Specify objective weights for optimization (one weight per place):

```bash
python petri_net_analyzer.py <pnml_file> <weights>
```

**Example:**
```bash
python petri_net_analyzer.py test_manufacturing.xml 1,1,1,1,2,0,3
```

Weights correspond to places in the order they appear in the PNML file.

### Run All Tests

Use the automated test runner to execute all test cases:

```bash
python run_all_tests.py
```

This will run the analyzer on all `.xml` files in the directory and provide a summary report.

---

## Test Files

The project includes **12 diverse test cases** covering all major Petri net patterns.

### Basic Patterns (7 tests)
| File | Places | Transitions | Description |
|------|--------|-------------|-------------|
| `test_simple.xml` | 2 | 1 | Simplest net - basic token flow |
| `test_cycle.xml` | 3 | 3 | Cyclic execution - no deadlock |
| `test_deadlock.xml` | 3 | 2 | Contains deadlock at (0,1,0) |
| `test_no_deadlock.xml` | 3 | 2 | Deadlock-free design |
| `test_choice.xml` | 3 | 2 | Choice/conflict pattern |
| `test_synchronization.xml` | 3 | 1 | Synchronization barrier |
| `1-safePetriNet.xml` | 2 | 1 | 1-safe property demo |

### Advanced Patterns (5 tests)
| File | Places | Transitions | Description |
|------|--------|-------------|-------------|
| `test_parallel_choice.xml` | 4 | 4 | Parallel execution + choice |
| `test_mutex.xml` | 5 | 4 | Mutual exclusion (2 processes) |
| `test_free_choice.xml` | 5 | 4 | Free choice net (important class) |
| `test_manufacturing.xml` | 7 | 6 | Assembly line workflow |
| `test_dining_philosophers.xml` | 9 | 6 | Classic CS problem (3 philosophers) |

**All tests are 1-safe** (max 1 token per place)

For detailed test descriptions, see [TEST_CATALOG.md](TEST_CATALOG.md).

---

## Project Structure

```
math-modeling/
├── petri_net_analyzer.py    # Main implementation (all 5 tasks)
├── run_all_tests.py          # Automated test runner
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── TASK_GUIDE.md            # Detailed task explanations
├── TEST_CATALOG.md          # Complete test case documentation
├── IMPLEMENTATION_SUMMARY.md # Design decisions and algorithms
├── QUICK_START.md           # Quick start guide
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

## Implementation Details

### Data Structures

#### PetriNet Class
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
- `is_transition_enabled()` - Check if transition can fire
- `fire_transition()` - Execute transition, return new marking
- `is_dead_marking()` - Check if no transitions are enabled

### Algorithms

**Task 2: Explicit Reachability**
- Algorithm: Breadth-First Search (BFS)
- Complexity: O(|R| × |T|) where R = reachable markings, T = transitions
- Data structure: Set for visited states, deque for queue

**Task 3: Symbolic Reachability**
- Algorithm: BDD-based fixed-point iteration
- Variables: x_p (current state), x'_p (next state) for each place p
- Relation: R(x, x') encodes all transition relations
- Fixed-point: Reach* = Reach ∪ Image(Reach) until convergence

**Task 4: Deadlock Detection**
- Method 1: Enumerate reachable markings, check dead state
- Method 2: ILP formulation with BDD membership oracle
- Constraint: ∀t ∈ T, ∃p ∈ •t : M(p) < weight(p,t)

**Task 5: Optimization**
- Objective: max c^T M where M ∈ Reachable
- Method: Enumerate and evaluate OR ILP with BDD verification

For more details, see [TASK_GUIDE.md](TASK_GUIDE.md).

---

## Output Format

The analyzer produces clear, formatted output for each task:

```
