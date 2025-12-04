# Task Implementation Guide
## CO2011 - Symbolic and Algebraic Reasoning in Petri Nets

This document provides detailed explanations for each task implementation.

---

## Task 1: PNML Parsing

### Overview
Parse a standard PNML (Petri Net Markup Language) file and construct an internal representation of the Petri net.

### What is Parsed
1. **Places**: Each place has:
   - `id`: Unique identifier
   - `name`: Optional name (defaults to id)
   - `initialMarking`: Number of tokens (0 or 1 for 1-safe nets)

2. **Transitions**: Each transition has:
   - `id`: Unique identifier
   - `name`: Optional name (defaults to id)

3. **Arcs**: Each arc has:
   - `id`: Unique identifier
   - `source`: Source node ID (place or transition)
   - `target`: Target node ID (place or transition)
   - `weight` (inscription): Token weight (defaults to 1)

### Implementation Details

**File**: `petri_net_analyzer.py`
**Function**: `parse_pnml(file_path: str) -> PetriNet`

**Key Components**:
- Uses `xml.etree.ElementTree` to parse XML
- Handles PNML namespace: `http://www.pnml.org/version-2009/grammar/ptnet`
- Extracts initial markings from `<initialMarking><text>...</text></initialMarking>`
- Extracts arc weights from `<inscription><text>...</text></inscription>`
- Builds internal data structures:
  - `pre_matrix[transition_id][place_id]`: Tokens consumed
  - `post_matrix[transition_id][place_id]`: Tokens produced
  - `place_to_index`: Mapping for efficient access

**Consistency Checks**:
- All arcs reference valid nodes
- Bipartite structure (places ↔ transitions only)
- No duplicate IDs
- Valid initial markings (0 or 1 for 1-safe)

### Usage Example
```python
from petri_net_analyzer import parse_pnml

pn = parse_pnml("test_simple.xml")
print(f"Places: {len(pn.places)}")
print(f"Transitions: {len(pn.transitions)}")
```

---

## Task 2: Explicit Reachability Computation

### Overview
Enumerate all reachable markings from the initial marking using Breadth-First Search (BFS).

### Theoretical Background

**Marking**: A marking M is a vector where M[p] represents the number of tokens in place p. For 1-safe nets, M[p] ∈ {0, 1}.

**Transition Enabled**: A transition t is enabled at marking M if:
- For all pre-places p of t: M[p] ≥ weight(p, t)

**Firing**: When transition t fires at marking M, it produces marking M' where:
- M'[p] = M[p] - pre[t][p] + post[t][p]

**Reachability**: A marking M' is reachable from M₀ if there exists a sequence of transitions that transforms M₀ into M'.

### Implementation Details

**Function**: `explicit_reachability(pn: PetriNet) -> Set[Tuple[int, ...]]`

**Algorithm** (BFS):
```
1. Initialize: queue = [M₀], visited = {M₀}
2. While queue is not empty:
   a. Pop marking M from queue
   b. For each transition t:
      - If t is enabled at M:
        - Fire t to get M'
        - If M' not in visited:
          - Add M' to visited and queue
3. Return visited (all reachable markings)
```

**Data Structures**:
- `Set[Tuple[int, ...]]`: Set of reachable markings (tuples are hashable)
- `deque`: Queue for BFS traversal

**Performance**:
- Time: O(|Reach| × |T|) where |Reach| is number of reachable markings
- Space: O(|Reach|) to store all markings

### Usage Example
```python
reachable = explicit_reachability(pn)
print(f"Found {len(reachable)} reachable markings")
for marking in reachable:
    print(marking)
```

---

## Task 3: Symbolic Reachability using BDD

### Overview
Compute reachable markings symbolically using Binary Decision Diagrams (BDDs). This is the core task (40% weight).

### Theoretical Background

**Binary Decision Diagram (BDD)**: A compact data structure for representing Boolean functions. For Petri nets:
- Each place p corresponds to a Boolean variable x_p
- A marking M corresponds to a valuation: x_p = 1 if M[p] = 1, else 0
- A set of markings corresponds to a Boolean function f(x₁, ..., xₙ)

**Symbolic Image Computation**: Instead of enumerating states, we compute:
- **Current state variables**: x_p for each place p
- **Next state variables**: x'_p for each place p
- **Transition relation**: R(x, x') encodes all possible state transitions
- **Reachability set**: Computed iteratively using fixed-point iteration

**Fixed-Point Algorithm**:
```
1. Reach⁰ = Init (initial marking)
2. For i = 1, 2, ...:
   a. Image = ∃x. (Reach^{i-1}(x) ∧ R(x, x'))
   b. Rename x' → x
   c. Reach^i = Reach^{i-1} ∨ Image
   d. If Reach^i = Reach^{i-1}, stop (fixed point reached)
```

### Implementation Details

**Library**: `dd` (Python BDD library with CUDD backend)
**Installation**: `pip install dd`

**Function**: `symbolic_reachability_bdd(pn: PetriNet) -> Tuple[BDD, BDDManager, Dict]`

**Key Steps**:

1. **Variable Declaration**:
   - Current state: `x_0, x_1, ..., x_{n-1}` for n places
   - Next state: `x_next_0, x_next_1, ..., x_next_{n-1}`

2. **Initial Marking BDD**:
   ```python
   Init = AND_p (x_p if M₀[p]=1 else ¬x_p)
   ```

3. **Transition Relation BDD**:
   For each transition t:
   - **Enabled condition**: AND of all pre-place variables
   - **Update condition**: Encodes M' = fire(t, M)
   - **Transition relation**: R_t = enabled ∧ update
   - **Overall**: R = OR_t R_t

4. **Fixed-Point Iteration**:
   - Compute image: `Image = ∃x. (Reach ∧ R)`
   - Rename variables: `Image' = rename(Image, x' → x)`
   - Update: `Reach = Reach ∨ Image'`
   - Stop when no new states found

**Helper Functions**:
- `build_initial_marking_bdd()`: Constructs BDD for initial marking
- `build_transition_relation_bdd()`: Constructs BDD for all transitions
- `count_bdd_assignments()`: Counts satisfying assignments (reachable markings)

### Usage Example
```python
bdd_result = symbolic_reachability_bdd(pn)
if bdd_result:
    bdd, manager, vars = bdd_result
    count = count_bdd_assignments(manager, bdd, list(vars.values()))
    print(f"Reachable markings: {count}")
```

### Advantages of BDD Approach
- **Compact representation**: Can represent exponentially many states
- **Efficient operations**: Boolean operations are fast on BDDs
- **Scalability**: Better for large state spaces than explicit enumeration

---

## Task 4: Deadlock Detection using ILP + BDD

### Overview
Detect deadlocks by combining Integer Linear Programming (ILP) formulations with BDD-based reachability checking.

### Theoretical Background

**Dead Marking**: A marking M where no transition is enabled.

**Deadlock**: A dead marking that is reachable from the initial marking M₀.

**ILP Formulation**:
- **Variables**: M_p ∈ {0, 1} for each place p
- **Constraints**: For each transition t, at least one pre-place p must have M_p < weight(p, t)
  - For 1-safe nets: This means M_p = 0 for at least one pre-place
- **Objective**: Dummy (we only need feasibility)

**BDD Integration**:
- Use BDD as a membership oracle: check if ILP solution is in Reach(M₀)
- If not, add constraint to exclude it and solve again

### Implementation Details

**Library**: `pulp` (Python ILP library)
**Installation**: `pip install pulp`

**Function**: `deadlock_detection(pn, reachable_markings, bdd_result) -> Optional[Tuple]`

**Methods** (in order of preference):

1. **Explicit Enumeration** (if available):
   - Check each reachable marking for deadlock property
   - Fastest for small state spaces

2. **BDD Enumeration**:
   - Enumerate all reachable markings from BDD
   - Check each for deadlock property

3. **ILP Formulation**:
   ```python
   # Variables
   M[p] ∈ {0, 1} for each place p
   
   # Constraints: Dead marking
   For each transition t:
       sum(1 - M[p] for p in pre(t)) >= 1
       # At least one pre-place has no token
   
   # Solve
   # Then verify: M ∈ Reach(M₀) using BDD
   ```

**Helper Function**: `deadlock_detection_ilp()` implements the ILP formulation

### Usage Example
```python
deadlock = deadlock_detection(pn, reachable_markings, bdd_result)
if deadlock:
    print(f"Deadlock found: {deadlock}")
else:
    print("No deadlock")
```

---

## Task 5: Optimization over Reachable Markings

### Overview
Find a reachable marking that maximizes a linear objective function c^T · M.

### Theoretical Background

**Problem**: Given objective weights c = (c₁, ..., cₙ), find:
```
maximize: c^T · M = Σ c_p · M[p]
subject to: M ∈ Reach(M₀)
```

**ILP Formulation**:
- **Variables**: M_p ∈ {0, 1} for each place p
- **Objective**: maximize Σ c_p · M_p
- **Constraints**: M ∈ Reach(M₀) (checked via BDD)

**Alternative Approach**:
- Enumerate all reachable markings
- Compute objective value for each
- Return maximum

### Implementation Details

**Function**: `optimize_reachable_markings(pn, objective_weights, ...) -> Optional[Tuple]`

**Methods**:

1. **Explicit Enumeration**:
   ```python
   best_value = -∞
   for M in reachable_markings:
       value = sum(c[i] * M[i] for i in range(len(M)))
       if value > best_value:
           best_value = value
           best_marking = M
   ```

2. **BDD Enumeration**: Similar but enumerates from BDD

3. **ILP**:
   ```python
   # Variables
   M[p] ∈ {0, 1}
   
   # Objective
   maximize: sum(c[p] * M[p])
   
   # Solve
   # Verify M ∈ Reach(M₀) using BDD
   ```

### Usage Example
```python
# Maximize sum of tokens in places p1 and p2
weights = [1, 1, 0]  # One weight per place
result = optimize_reachable_markings(pn, weights, reachable_markings, bdd_result)
if result:
    marking, value = result
    print(f"Optimal marking: {marking}, value: {value}")
```

---

## Running the Code

### Installation

```bash
# Install required libraries
pip install dd pulp

# Note: dd requires CUDD library
# On macOS: brew install cudd
# On Ubuntu: sudo apt-get install libcudd-dev
# On Windows: May need to use pre-built wheels or WSL
```

### Basic Usage

```bash
# Run all tasks on a PNML file
python petri_net_analyzer.py test_simple.xml

# With custom objective weights (comma-separated)
python petri_net_analyzer.py test_simple.xml 1,2,3
```

### Test Files

1. **test_simple.xml**: Simple 2-place, 1-transition net
2. **test_deadlock.xml**: Net with a deadlock state
3. **test_cycle.xml**: Net with a cycle (no deadlock)
4. **test_parallel.xml**: Net with parallel execution paths

### Expected Output

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

=== Task 3: Symbolic Reachability Computation (BDD) ===
✓ Found 2 reachable markings
  Computation time: 0.0123 seconds
  Iterations: 2

=== Task 4: Deadlock Detection (ILP + BDD) ===
✓ No deadlock found
  Detection time: 0.0005 seconds

=== Task 5: Optimization over Reachable Markings ===
✓ Optimal marking found: (0, 1)
  Optimal value: 2
  Computation time: 0.0002 seconds
```

---

## Libraries Used

### Required Libraries

1. **xml.etree.ElementTree** (built-in Python)
   - Purpose: Parse PNML XML files
   - No installation needed

2. **dd** (Python BDD library)
   - Purpose: Symbolic reachability computation
   - Installation: `pip install dd`
   - Backend: CUDD (C-based BDD library)
   - Documentation: https://github.com/tulip-control/dd

3. **pulp** (Python ILP library)
   - Purpose: Integer Linear Programming for deadlock detection and optimization
   - Installation: `pip install pulp`
   - Solver: Uses CBC (Coin-or Branch and Cut) by default
   - Documentation: https://github.com/coin-or/pulp

### Optional Dependencies

- **CUDD**: Required by `dd` library
  - macOS: `brew install cudd`
  - Ubuntu/Debian: `sudo apt-get install libcudd-dev`
  - Windows: May require WSL or pre-built wheels

---

## Data Structures

### PetriNet Class
```python
class PetriNet:
    places: Dict[str, Place]           # Place objects by ID
    transitions: Dict[str, Transition] # Transition objects by ID
    arcs: List[Arc]                     # List of all arcs
    place_ids: List[str]                # Ordered list of place IDs
    transition_ids: List[str]           # Ordered list of transition IDs
    place_to_index: Dict[str, int]     # Place ID → index mapping
    pre_matrix: Dict[str, Dict[str, int]]  # pre[transition][place] = weight
    post_matrix: Dict[str, Dict[str, int]] # post[transition][place] = weight
    initial_marking: Tuple[int, ...]    # Initial marking vector
```

### Marking Representation
- **Type**: `Tuple[int, ...]` (immutable, hashable)
- **Length**: Number of places
- **Values**: 0 or 1 (1-safe nets)
- **Example**: `(1, 0, 1)` means tokens in places 0 and 2

---

## Challenges and Solutions

### Challenge 1: BDD Variable Ordering
**Problem**: BDD size depends heavily on variable ordering.

**Solution**: Use natural ordering (place index order). For better performance, could implement dynamic reordering.

### Challenge 2: Transition Relation Encoding
**Problem**: Encoding "M' = fire(t, M)" as a Boolean formula.

**Solution**: For each place p:
- If pre > 0 and post = 0: token consumed (current=1, next=0)
- If pre = 0 and post > 0: token produced (current=0, next=1)
- If pre > 0 and post > 0: token moved (current=1, next=1)
- Otherwise: no change (current = next)

### Challenge 3: BDD Model Counting
**Problem**: Counting satisfying assignments efficiently.

**Solution**: Use BDD's built-in enumeration or implement recursive counting.

### Challenge 4: ILP + BDD Integration
**Problem**: Ensuring ILP solutions are actually reachable.

**Solution**: Use BDD as membership oracle to verify reachability.

---

## Performance Considerations

### Explicit vs Symbolic
- **Explicit (BFS)**: Fast for small state spaces (< 1000 states)
- **Symbolic (BDD)**: Better for large state spaces (can handle millions of states)

### Memory Usage
- **Explicit**: O(|Reach| × |P|) to store all markings
- **Symbolic**: O(BDD nodes) which can be much smaller

### Time Complexity
- **Explicit**: O(|Reach| × |T|)
- **Symbolic**: O(iterations × BDD operations) where iterations ≤ |Reach|

---

## Future Improvements

1. **Variable Reordering**: Implement dynamic BDD variable reordering
2. **Incremental BDD Construction**: Build transition relation incrementally
3. **State Equation**: Use state equation for reachability over-approximation
4. **SMT Solvers**: Use SMT solvers for more complex constraints
5. **Parallel Processing**: Parallelize explicit enumeration for large nets

---

## References

1. Bryant, R. E. (1986). Graph-based algorithms for boolean function manipulation. IEEE Transactions on Computers.
2. Pastor, E., Cortadella, J., & Roig, O. (2001). Symbolic analysis of bounded Petri nets. IEEE Transactions on Computers.
3. Murata, T. (1989). Petri nets: Properties, analysis and applications. Proceedings of the IEEE.

---

## Contact and Support

For questions about the implementation, refer to:
- Assignment document: CO2011 Assignment - Symbolic and Algebraic Reasoning in Petri Nets
- Course forum: BK-eLearning
- Instructor: Dr. Van-Giang Trinh

