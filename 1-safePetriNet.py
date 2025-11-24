import xml.etree.ElementTree as ET

class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []

class Place:
    def __init__(self, id, name=None):
        self.id = id
        self.name = name

class Transition:
    def __init__(self, id, name=None):
        self.id = id
        self.name = name

class Arc:
    def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target

def verify_consistency(pn):
    errors = []

    # 1. Collect all valid node IDs
    nodes = set(pn.places.keys()) | set(pn.transitions.keys())

    # 2. Check arcs refer to real nodes
    for arc in pn.arcs:
        if arc.source not in nodes:
            errors.append(f"Arc {arc.id}: invalid source '{arc.source}'")
        if arc.target not in nodes:
            errors.append(f"Arc {arc.id}: invalid target '{arc.target}'")

        # 3. Enforce bipartite structure
        if (arc.source in pn.places and arc.target in pn.places):
            errors.append(f"Arc {arc.id}: connects place to place (invalid)")
        if (arc.source in pn.transitions and arc.target in pn.transitions):
            errors.append(f"Arc {arc.id}: connects transition to transition (invalid)")

    # 4. Check duplicate IDs (should not happen if using dict)
    if len(pn.places) != len(set(pn.places.keys())):
        errors.append("Duplicate place IDs detected")
    if len(pn.transitions) != len(set(pn.transitions.keys())):
        errors.append("Duplicate transition IDs detected")

    # 5. Check isolated transitions (optional)
    for tid in pn.transitions:
        connected = any(a.source == tid or a.target == tid for a in pn.arcs)
        if not connected:
            errors.append(f"Transition {tid} is isolated")

    if errors:
        print("Inconsistencies found:")
        for e in errors:
            print("   -", e)
        return False

    print("Petri net structure is consistent.")
    return True


def parse_pnml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {"pnml": "http://www.pnml.org/version-2009/grammar/ptnet"}

    net_node = root.find(".//pnml:net", ns)
    if net_node is None:
        raise ValueError("Không tìm thấy <net> trong PNML")

    pn = PetriNet()

    # --- Parse places ---
    for p in net_node.findall("pnml:place", ns):
        pid = p.get("id")
        name_node = p.find("pnml:name/pnml:text", ns)
        name = name_node.text if name_node is not None else pid
        pn.places[pid] = Place(pid, name)

    # --- Parse transitions ---
    for t in net_node.findall("pnml:transition", ns):
        tid = t.get("id")
        name_node = t.find("pnml:name/pnml:text", ns)
        name = name_node.text if name_node is not None else tid
        pn.transitions[tid] = Transition(tid, name)

    # --- Parse arcs ---
    for a in net_node.findall("pnml:arc", ns):
        aid = a.get("id")
        source = a.get("source")
        target = a.get("target")
        pn.arcs.append(Arc(aid, source, target))

    # --- Validation ---
    verify_consistency(pn)

    print("PNML hợp lệ và đã được phân tích thành công!")
    print(f"  Places: {len(pn.places)}")
    print(f"  Transitions: {len(pn.transitions)}")
    print(f"  Arcs: {len(pn.arcs)}")

    return pn

file_path = "1-safePetriNet.xml"

parse_pnml(file_path)
