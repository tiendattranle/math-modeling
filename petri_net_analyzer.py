"""
Petri Net Analyzer - CO2011 Assignment
Symbolic and Algebraic Reasoning in Petri Nets

This module implements:
1. PNML parsing
2. Explicit reachability computation (BFS)
3. Symbolic reachability using BDD
4. Deadlock detection using ILP + BDD
5. Optimization over reachable markings

Libraries used:
- xml.etree.ElementTree: For PNML parsing
- dd (BDD library with CUDD backend): For symbolic reachability
- pulp: For ILP formulations
"""

import xml.etree.ElementTree as ET
from collections import deque
from typing import Dict, List, Tuple, Set, Optional
import time
import sys

try:
    from dd import autoref as _bdd
    BDD_AVAILABLE = True
except ImportError:
    print("Warning: dd library not found. Install with: pip install dd")
    BDD_AVAILABLE = False
    _bdd = None

try:
    import pulp
    ILP_AVAILABLE = True
except ImportError:
    print("Warning: pulp library not found. Install with: pip install pulp")
    ILP_AVAILABLE = False
    pulp = None


class PetriNet:
    """Represents a 1-safe Petri net."""
    
    def __init__(self):
        self.places: Dict[str, 'Place'] = {}
        self.transitions: Dict[str, 'Transition'] = {}
        self.arcs: List['Arc'] = []
        
        # Internal representation for efficient computation
        self.place_ids: List[str] = []  # Ordered list of place IDs
        self.transition_ids: List[str] = []  # Ordered list of transition IDs
        self.place_to_index: Dict[str, int] = {}  # Map place ID to index
        
        # Pre and post matrices: pre[t][p] = tokens consumed from p by t
        self.pre_matrix: Dict[str, Dict[str, int]] = {}  # pre[transition_id][place_id] = weight
        self.post_matrix: Dict[str, Dict[str, int]] = {}  # post[transition_id][place_id] = weight
        
        # Initial marking as a tuple (0/1 for each place)
        self.initial_marking: Tuple[int, ...] = ()
    
    def build_matrices(self):
        """Build pre and post matrices from arcs."""
        # Initialize matrices
        for tid in self.transition_ids:
            self.pre_matrix[tid] = {pid: 0 for pid in self.place_ids}
            self.post_matrix[tid] = {pid: 0 for pid in self.place_ids}
        
        # Fill matrices from arcs
        for arc in self.arcs:
            if arc.source in self.places and arc.target in self.transitions:
                # Place -> Transition: pre-arc
                if arc.target not in self.pre_matrix:
                    self.pre_matrix[arc.target] = {pid: 0 for pid in self.place_ids}
                self.pre_matrix[arc.target][arc.source] = arc.weight
            elif arc.source in self.transitions and arc.target in self.places:
                # Transition -> Place: post-arc
                if arc.source not in self.post_matrix:
                    self.post_matrix[arc.source] = {pid: 0 for pid in self.place_ids}
                self.post_matrix[arc.source][arc.target] = arc.weight
    
    def is_transition_enabled(self, marking: Tuple[int, ...], transition_id: str) -> bool:
        """Check if a transition is enabled at a given marking."""
        if transition_id not in self.pre_matrix:
            return False
        
        for place_id, weight in self.pre_matrix[transition_id].items():
            if weight > 0:
                place_idx = self.place_to_index[place_id]
                if marking[place_idx] < weight:
                    return False
        return True
    
    def fire_transition(self, marking: Tuple[int, ...], transition_id: str) -> Tuple[int, ...]:
        """Fire a transition and return the new marking."""
        new_marking = list(marking)
        
        # Subtract pre-arc weights
        if transition_id in self.pre_matrix:
            for place_id, weight in self.pre_matrix[transition_id].items():
                if weight > 0:
                    place_idx = self.place_to_index[place_id]
                    new_marking[place_idx] -= weight
        
        # Add post-arc weights
        if transition_id in self.post_matrix:
            for place_id, weight in self.post_matrix[transition_id].items():
                if weight > 0:
                    place_idx = self.place_to_index[place_id]
                    new_marking[place_idx] += weight
        
        return tuple(new_marking)
    
    def is_dead_marking(self, marking: Tuple[int, ...]) -> bool:
        """Check if a marking is dead (no transition is enabled)."""
        for tid in self.transition_ids:
            if self.is_transition_enabled(marking, tid):
                return False
        return True


class Place:
    """Represents a place in a Petri net."""
    def __init__(self, id: str, name: Optional[str] = None, initial_marking: int = 0):
        self.id = id
        self.name = name or id
        self.initial_marking = initial_marking


class Transition:
    """Represents a transition in a Petri net."""
    def __init__(self, id: str, name: Optional[str] = None):
        self.id = id
        self.name = name or id


class Arc:
    """Represents an arc in a Petri net."""
    def __init__(self, id: str, source: str, target: str, weight: int = 1):
        self.id = id
        self.source = source
        self.target = target
        self.weight = weight


def parse_pnml(file_path: str) -> PetriNet:
    """
    Task 1: Parse a PNML file and construct the Petri net representation.
    
    Args:
        file_path: Path to the PNML file
        
    Returns:
        PetriNet object with parsed structure
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # PNML namespace
    ns = {"pnml": "http://www.pnml.org/version-2009/grammar/ptnet"}
    
    net_node = root.find(".//pnml:net", ns)
    if net_node is None:
        raise ValueError("No <net> element found in PNML file")
    
    pn = PetriNet()
    
    # Parse places
    for p in net_node.findall("pnml:place", ns):
        pid = p.get("id")
        if not pid:
            raise ValueError("Place missing id attribute")
        
        name_node = p.find("pnml:name/pnml:text", ns)
        name = name_node.text if name_node is not None else pid
        
        # Parse initial marking
        initial_marking = 0
        marking_node = p.find("pnml:initialMarking/pnml:text", ns)
        if marking_node is not None and marking_node.text:
            try:
                initial_marking = int(marking_node.text.strip())
                if initial_marking < 0 or initial_marking > 1:
                    raise ValueError(f"Place {pid} has invalid initial marking (must be 0 or 1 for 1-safe nets)")
            except ValueError as e:
                raise ValueError(f"Invalid initial marking for place {pid}: {e}")
        
        pn.places[pid] = Place(pid, name, initial_marking)
        pn.place_ids.append(pid)
        pn.place_to_index[pid] = len(pn.place_ids) - 1
    
    # Parse transitions
    for t in net_node.findall("pnml:transition", ns):
        tid = t.get("id")
        if not tid:
            raise ValueError("Transition missing id attribute")
        
        name_node = t.find("pnml:name/pnml:text", ns)
        name = name_node.text if name_node is not None else tid
        
        pn.transitions[tid] = Transition(tid, name)
        pn.transition_ids.append(tid)
    
    # Parse arcs
    for a in net_node.findall("pnml:arc", ns):
        aid = a.get("id")
        source = a.get("source")
        target = a.get("target")
        
        if not aid or not source or not target:
            raise ValueError(f"Arc missing required attributes: id, source, or target")
        
        # Parse arc weight (inscription)
        weight = 1  # Default weight
        inscription_node = a.find("pnml:inscription/pnml:text", ns)
        if inscription_node is not None and inscription_node.text:
            try:
                weight = int(inscription_node.text.strip())
                if weight < 1:
                    raise ValueError(f"Arc {aid} has invalid weight (must be >= 1)")
            except ValueError as e:
                raise ValueError(f"Invalid weight for arc {aid}: {e}")
        
        pn.arcs.append(Arc(aid, source, target, weight))
    
    # Verify consistency
    verify_consistency(pn)
    
    # Build internal matrices
    pn.build_matrices()
    
    # Set initial marking
    pn.initial_marking = tuple(pn.places[pid].initial_marking for pid in pn.place_ids)
    
    print(f"\tPNML file parsed successfully!")
    print(f"\tPlaces: {len(pn.places)}")
    print(f"\tTransitions: {len(pn.transitions)}")
    print(f"\tArcs: {len(pn.arcs)}")
    print(f"\tInitial marking: {pn.initial_marking}")
    
    return pn


def verify_consistency(pn: PetriNet) -> bool:
    """
    Verify the consistency of the Petri net structure.
    
    Checks:
    - All arcs reference valid nodes
    - Bipartite structure (places <-> transitions only)
    - No duplicate IDs
    """
    errors = []
    
    # Collect all valid node IDs
    nodes = set(pn.places.keys()) | set(pn.transitions.keys())
    
    # Check arcs
    for arc in pn.arcs:
        if arc.source not in nodes:
            errors.append(f"Arc {arc.id}: invalid source '{arc.source}'")
        if arc.target not in nodes:
            errors.append(f"Arc {arc.id}: invalid target '{arc.target}'")
        
        # Enforce bipartite structure
        if arc.source in pn.places and arc.target in pn.places:
            errors.append(f"Arc {arc.id}: connects place to place (invalid)")
        if arc.source in pn.transitions and arc.target in pn.transitions:
            errors.append(f"Arc {arc.id}: connects transition to transition (invalid)")
    
    # Check for duplicate IDs
    if len(pn.places) != len(set(pn.places.keys())):
        errors.append("Duplicate place IDs detected")
    if len(pn.transitions) != len(set(pn.transitions.keys())):
        errors.append("Duplicate transition IDs detected")
    
    if errors:
        print("\tInconsistencies found:")
        for e in errors:
            print(f"\t - {e}")
        return False
    
    print("\tPetri net structure is consistent")
    return True


def explicit_reachability(pn: PetriNet) -> Set[Tuple[int, ...]]:
    """
    Task 2: Compute all reachable markings using BFS.
    
    Args:
        pn: PetriNet object
        
    Returns:
        Set of all reachable markings (as tuples)
    """
    print("\n=== Task 2: Explicit Reachability Computation (BFS) ===")
    start_time = time.time()
    
    reachable = set()
    queue = deque([pn.initial_marking])
    reachable.add(pn.initial_marking)
    
    while queue:
        current_marking = queue.popleft()
        
        # Try to fire each transition
        for tid in pn.transition_ids:
            if pn.is_transition_enabled(current_marking, tid):
                new_marking = pn.fire_transition(current_marking, tid)
                
                if new_marking not in reachable:
                    reachable.add(new_marking)
                    queue.append(new_marking)
    
    elapsed_time = time.time() - start_time
    
    print(f"\tFound {len(reachable)} reachable markings")
    print(f"\t  -  {r}" for r in reachable)
    print(f"\tComputation time: {elapsed_time:.4f} seconds")
    print(f"\tMemory: ~{sys.getsizeof(reachable) + sum(sys.getsizeof(m) for m in reachable)} bytes")
    
    return reachable


def symbolic_reachability_bdd(pn: PetriNet) -> Optional[object]:
    """
    Task 3: Compute reachable markings symbolically using BDD.
    
    Args:
        pn: PetriNet object
        
    Returns:
        BDD representing the set of all reachable markings
    """
    if not BDD_AVAILABLE:
        print("\n\tBDD library not available. Install with: pip install dd")
        return None
    
    print("\n=== Task 3: Symbolic Reachability Computation (BDD) ===")
    start_time = time.time()
    
    # Create BDD manager
    bdd_manager = _bdd.BDD()
    
    # Create variables for current state (x_p for each place p)
    current_vars = {}
    for i, pid in enumerate(pn.place_ids):
        var_name = f"x_{i}"
        bdd_manager.declare(var_name)
        current_vars[pid] = var_name
    
    # Create variables for next state (x'_p for each place p)
    next_vars = {}
    for i, pid in enumerate(pn.place_ids):
        var_name = f"x_next_{i}"
        bdd_manager.declare(var_name)
        next_vars[pid] = var_name
    
    # Build initial marking BDD
    init_bdd = build_initial_marking_bdd(bdd_manager, pn, current_vars)
    
    # Build transition relation BDD
    transition_relation = build_transition_relation_bdd(bdd_manager, pn, current_vars, next_vars)
    
    # Compute reachable set iteratively
    reach_bdd = init_bdd
    prev_size = 0
    
    iteration = 0
    while True:
        iteration += 1
        
        # Compute image: ∃x. (Reach(x) ∧ R(x, x'))
        # This gives us all next states reachable in one step
        image = bdd_manager.exist(current_vars.values(), 
                                   bdd_manager.apply('and', reach_bdd, transition_relation))
        
        # Rename next variables back to current variables
        rename_map = {next_vars[pid]: current_vars[pid] for pid in pn.place_ids}
        image_renamed = bdd_manager.let(rename_map, image)
        
        # Check if we found new states
        new_states = bdd_manager.apply('and', image_renamed, 
                                       bdd_manager.apply('not', reach_bdd))
        
        if new_states == bdd_manager.false:
            break
        
        # Update reachable set
        reach_bdd = bdd_manager.apply('or', reach_bdd, image_renamed)
        
        # Count states (for progress)
        count = count_bdd_assignments(bdd_manager, reach_bdd, current_vars.values())
        if count == prev_size:
            break
        prev_size = count
    
    # Count total reachable markings
    total_markings = count_bdd_assignments(bdd_manager, reach_bdd, current_v_vars=list(current_vars.values()))
    
    elapsed_time = time.time() - start_time
    
    print(f"\tFound {total_markings} reachable markings")
    print(f"\tComputation time: {elapsed_time:.4f} seconds")
    print(f"\tIterations: {iteration}")
    
    # Memory usage tracking
    bdd_size = sys.getsizeof(reach_bdd)
    print(f"\tMemory (BDD object): ~{bdd_size} bytes")
    
    # Get BDD statistics if available
    try:
        stats = bdd_manager.statistics()
        if stats and 'n_nodes' in stats:
            print(f"\tBDD node count: {stats['n_nodes']}")
        if stats and 'mem' in stats:
            print(f"\tBDD memory usage: {stats['mem']} bytes")
        elif stats:
            print(f"\tBDD statistics: {stats}")
    except Exception:
        pass  # Statistics not available
    
    return reach_bdd, bdd_manager, current_vars


def build_initial_marking_bdd(bdd_manager, pn: PetriNet, current_vars: Dict[str, str]) -> object:
    """Build BDD for initial marking."""
    clauses = []
    for i, pid in enumerate(pn.place_ids):
        var = current_vars[pid]
        if pn.initial_marking[i] == 1:
            clauses.append(bdd_manager.var(var))
        else:
            clauses.append(bdd_manager.apply('not', bdd_manager.var(var)))
    
    # Conjunction of all place conditions
    result = clauses[0]
    for clause in clauses[1:]:
        result = bdd_manager.apply('and', result, clause)
    
    return result


def build_transition_relation_bdd(bdd_manager, pn: PetriNet, 
                                  current_vars: Dict[str, str], 
                                  next_vars: Dict[str, str]) -> object:
    """Build BDD for transition relation R(x, x')."""
    transition_relations = []
    
    for tid in pn.transition_ids:
        # Build enabled condition: all pre-places have enough tokens
        enabled_conditions = []
        for pid in pn.place_ids:
            place_idx = pn.place_to_index[pid]
            pre_weight = pn.pre_matrix.get(tid, {}).get(pid, 0)
            
            if pre_weight > 0:
                # Need token in current state
                enabled_conditions.append(bdd_manager.var(current_vars[pid]))
        
        if enabled_conditions:
            enabled = enabled_conditions[0]
            for cond in enabled_conditions[1:]:
                enabled = bdd_manager.apply('and', enabled, cond)
        else:
            enabled = bdd_manager.true
        
        # Build update relation: next state = current state - pre + post
        update_conditions = []
        for pid in pn.place_ids:
            place_idx = pn.place_to_index[pid]
            pre_weight = pn.pre_matrix.get(tid, {}).get(pid, 0)
            post_weight = pn.post_matrix.get(tid, {}).get(pid, 0)
            
            current_var = current_vars[pid]
            next_var = next_vars[pid]
            
            if pre_weight > 0 and post_weight == 0:
                # Token consumed: current=1, next=0
                update_conditions.append(
                    bdd_manager.apply('and',
                        bdd_manager.var(current_var),
                        bdd_manager.apply('not', bdd_manager.var(next_var))
                    )
                )
            elif pre_weight == 0 and post_weight > 0:
                # Token produced: current=0, next=1
                update_conditions.append(
                    bdd_manager.apply('and',
                        bdd_manager.apply('not', bdd_manager.var(current_var)),
                        bdd_manager.var(next_var)
                    )
                )
            elif pre_weight > 0 and post_weight > 0:
                # Token moved: current=1, next=1 (no change)
                update_conditions.append(
                    bdd_manager.apply('and',
                        bdd_manager.var(current_var),
                        bdd_manager.var(next_var)
                    )
                )
            else:
                # No change: current=next
                # Encode: (current AND next) OR (NOT current AND NOT next)
                current_var_bdd = bdd_manager.var(current_var)
                next_var_bdd = bdd_manager.var(next_var)
                equiv = bdd_manager.apply('or',
                    bdd_manager.apply('and', current_var_bdd, next_var_bdd),
                    bdd_manager.apply('and', 
                        bdd_manager.apply('not', current_var_bdd),
                        bdd_manager.apply('not', next_var_bdd)
                    )
                )
                update_conditions.append(equiv)
        
        if update_conditions:
            update = update_conditions[0]
            for cond in update_conditions[1:]:
                update = bdd_manager.apply('and', update, cond)
        else:
            update = bdd_manager.true
        
        # Transition relation: enabled AND update
        trans_rel = bdd_manager.apply('and', enabled, update)
        transition_relations.append(trans_rel)
    
    # Union of all transition relations
    if transition_relations:
        result = transition_relations[0]
        for tr in transition_relations[1:]:
            result = bdd_manager.apply('or', result, tr)
    else:
        result = bdd_manager.false
    
    return result


def count_bdd_assignments(bdd_manager, bdd_expr, current_v_vars: List[str]) -> int:
    """Count the number of satisfying assignments for a BDD."""
    if bdd_expr == bdd_manager.false:
        return 0
    if bdd_expr == bdd_manager.true:
        return 2 ** len(current_v_vars)
    
    # Use model counting
    try:
        # Simple enumeration approach for small state spaces
        count = 0
        for model in bdd_manager.pick_iter(bdd_expr, care_vars=current_v_vars):
            count += 1
        return count
    except Exception:
        # Fallback: enumerate all possible assignments
        count = 0
        num_vars = len(current_v_vars)
        for i in range(2 ** num_vars):
            assignment = {}
            for j, var in enumerate(current_v_vars):
                assignment[var] = bool((i >> j) & 1)
            try:
                if bdd_manager.let(assignment, bdd_expr) == bdd_manager.true:
                    count += 1
            except Exception:
                continue
        return count


def deadlock_detection(pn: PetriNet, reachable_markings: Set[Tuple[int, ...]] = None,
                       bdd_result: Tuple = None) -> Optional[Tuple[int, ...]]:
    """
    Task 4: Detect deadlocks using ILP + BDD.
    
    A deadlock is a reachable marking where no transition is enabled.
    
    Args:
        pn: PetriNet object
        reachable_markings: Not used (kept for backward compatibility)
        bdd_result: Tuple (bdd, manager, vars) from symbolic computation
        
    Returns:
        A deadlock marking if found, None otherwise
    """
    print("\n=== Task 4: Deadlock Detection (ILP + BDD) ===")
    start_time = time.time()
    
    # Use ILP for deadlock detection
    if not ILP_AVAILABLE:
        print("\tILP library (pulp) not available. Install with: pip install pulp")
        return None
    
    deadlock = deadlock_detection_ilp(pn, bdd_result)
    
    elapsed_time = time.time() - start_time
    
    if deadlock is not None:
        print(f"\tDeadlock found via ILP: {deadlock}")
        print(f"\tDetection time: {elapsed_time:.4f} seconds")
        return deadlock
    else:
        print(f"\tNo deadlock found")
        print(f"\tDetection time: {elapsed_time:.4f} seconds")
        return None


def deadlock_detection_ilp(pn: PetriNet, bdd_result: Tuple = None) -> Optional[Tuple[int, ...]]:
    """
    Deadlock detection using ILP formulation.
    
    Formulation:
    - Variables: M_p ∈ {0,1} for each place p
    - Constraints:
      1. M is a dead marking: for each transition t, at least one pre-place p has M_p < weight(p,t)
      2. M is reachable: This is checked using BDD membership oracle
    """
    if not ILP_AVAILABLE:
        return None
    
    # Create ILP problem
    prob = pulp.LpProblem("DeadlockDetection", pulp.LpMaximize)
    
    # Variables: M_p for each place
    M = {}
    for pid in pn.place_ids:
        M[pid] = pulp.LpVariable(f"M_{pid}", cat='Binary')
    
    # Dummy objective (we just need feasibility)
    prob += 0
    
    # Constraint: Dead marking - for each transition, at least one pre-place is insufficient
    for tid in pn.transition_ids:
        pre_places = []
        for pid in pn.place_ids:
            weight = pn.pre_matrix.get(tid, {}).get(pid, 0)
            if weight > 0:
                # M_p < weight means M_p = 0 (since weight >= 1 and M_p ∈ {0,1})
                # So we need: M_p = 0 for at least one pre-place
                pre_places.append(1 - M[pid])  # 1 - M_p = 1 if M_p = 0
        
        if pre_places:
            # At least one pre-place has no token
            prob += sum(pre_places) >= 1
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == pulp.LpStatusOptimal:
        # Extract marking
        marking_list = []
        for pid in pn.place_ids:
            val = M[pid].varValue
            marking_list.append(int(val) if val is not None else 0)
        marking = tuple(marking_list)
        
        # Verify reachability using BDD if available
        if bdd_result is not None and BDD_AVAILABLE:
            bdd, bdd_manager, current_vars = bdd_result
            if is_marking_reachable_bdd(bdd_manager, bdd, marking, current_vars, pn):
                return marking
        else:
            # Without BDD, we can't verify reachability, so return None
            # (In practice, we'd need to check against explicit reachable set)
            return None
    
    return None


def is_marking_reachable_bdd(bdd_manager, bdd, marking: Tuple[int, ...], 
                             current_vars: Dict[str, str], pn: PetriNet) -> bool:
    """Check if a marking is in the BDD reachable set."""
    assignment = {}
    for pid in pn.place_ids:
        var = current_vars[pid]
        assignment[var] = bool(marking[pn.place_to_index[pid]])
    
    result = bdd_manager.let(assignment, bdd)
    return result == bdd_manager.true


def optimize_reachable_markings(pn: PetriNet, 
                                objective_weights: List[int],
                                reachable_markings: Set[Tuple[int, ...]] = None,
                                bdd_result: Tuple = None) -> Optional[Tuple[Tuple[int, ...], int]]:
    """
    Task 5: Optimize over reachable markings using ILP.
    
    Maximize c^T * M where M is a reachable marking and c is the objective weight vector.
    
    Args:
        pn: PetriNet object
        objective_weights: List of weights c_p for each place (in order of place_ids)
        reachable_markings: Not used (kept for backward compatibility)
        bdd_result: Tuple (bdd, manager, vars) from symbolic computation
        
    Returns:
        Tuple (optimal_marking, optimal_value) if found, None otherwise
    """
    print("\n=== Task 5: Optimization over Reachable Markings ===")
    start_time = time.time()
    
    if len(objective_weights) != len(pn.place_ids):
        raise ValueError(f"Objective weights length ({len(objective_weights)}) must match number of places ({len(pn.place_ids)})")
    
    # Use ILP for optimization
    if not ILP_AVAILABLE:
        print("\tILP library (pulp) not available. Install with: pip install pulp")
        return None
    
    ilp_result = optimize_reachable_markings_ilp(pn, objective_weights, bdd_result)
    
    elapsed_time = time.time() - start_time
    
    if ilp_result is not None:
        best_marking, best_value = ilp_result
        print(f"\tOptimal marking found: {best_marking}")
        print(f"\tOptimal value: {best_value}")
        print(f"\tComputation time: {elapsed_time:.4f} seconds")
        return (best_marking, best_value)
    else:
        print(f"\tNo reachable marking found")
        print(f"\tComputation time: {elapsed_time:.4f} seconds")
        return None


def optimize_reachable_markings_ilp(pn: PetriNet, 
                                    objective_weights: List[int],
                                    bdd_result: Tuple = None) -> Optional[Tuple[Tuple[int, ...], int]]:
    """
    Optimization using ILP formulation.
    
    Formulation:
    - Variables: M_p ∈ {0,1} for each place p
    - Objective: maximize sum(c_p * M_p)
    - Constraints: M is reachable (checked via BDD membership)
    """
    if not ILP_AVAILABLE:
        return None
    
    # Create ILP problem
    prob = pulp.LpProblem("OptimizeMarkings", pulp.LpMaximize)
    
    # Variables
    M = {}
    for pid in pn.place_ids:
        M[pid] = pulp.LpVariable(f"M_{pid}", cat='Binary')
    
    # Objective
    prob += sum(objective_weights[pn.place_to_index[pid]] * M[pid] for pid in pn.place_ids)
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == pulp.LpStatusOptimal:
        marking_list = []
        for pid in pn.place_ids:
            val = M[pid].varValue
            marking_list.append(int(val) if val is not None else 0)
        marking = tuple(marking_list)
        value = sum(objective_weights[i] * marking[i] for i in range(len(marking)))
        
        # Verify reachability
        if bdd_result is not None and BDD_AVAILABLE:
            bdd, bdd_manager, current_vars = bdd_result
            if is_marking_reachable_bdd(bdd_manager, bdd, marking, current_vars, pn):
                return (marking, value)
        else:
            # Without BDD verification, we can't guarantee reachability
            return None
    
    return None


def main():
    """Main function to run all tasks."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python petri_net_analyzer.py <pnml_file> [objective_weights]")
        print("Example: python petri_net_analyzer.py test_net.xml 1,2,3")
        sys.exit(1)
    
    pnml_file = sys.argv[1]
    
    # Task 1: Parse PNML
    print("=" * 60)
    print("TASK 1: PNML PARSING")
    print("=" * 60)
    try:
        pn = parse_pnml(pnml_file)
    except Exception as e:
        print(f"\tError parsing PNML: {e}")
        sys.exit(1)
    
    # Task 2: Explicit reachability
    reachable_markings = explicit_reachability(pn)
    
    # Task 3: Symbolic reachability with BDD
    bdd_result = symbolic_reachability_bdd(pn)
    
    # Task 4: Deadlock detection
    deadlock = deadlock_detection(pn, reachable_markings, bdd_result)
    
    # Task 5: Optimization
    if len(sys.argv) >= 3:
        try:
            weights = [int(w.strip()) for w in sys.argv[2].split(',')]
            optimize_reachable_markings(pn, weights, reachable_markings, bdd_result)
        except ValueError as e:
            print(f"\tInvalid objective weights: {e}")
    else:
        # Default: maximize sum of all tokens
        default_weights = [1] * len(pn.place_ids)
        optimize_reachable_markings(pn, default_weights, reachable_markings, bdd_result)
    
    print("\n" + "=" * 60)
    print("ALL TASKS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

