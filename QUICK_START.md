# Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: CUDD Library (Usually NOT Needed!)

**✅ Good News for Anaconda/Conda Users:**
If you're using **Anaconda** or **Conda** (like you are with `(base) nguyencolece@192`), the `dd` library **already includes CUDD support**! You don't need to install CUDD separately.

**How to verify:**
```bash
python -c "from dd import autoref as bdd; bm = bdd.BDD(); print('BDD works! CUDD is included.')"
```

If this works, **you can skip Step 2 entirely!** ✅

**Only if you get CUDD errors** (rare, usually only on Linux without Anaconda):

**macOS:**
```bash
# CUDD is NOT available in Homebrew
# The dd library in Anaconda/Conda includes CUDD, so you don't need this
# If you're not using Anaconda and get errors, you may need to compile from source
```

**Ubuntu/Debian (only if NOT using Anaconda):**
```bash
sudo apt-get install libcudd-dev
```

**Summary:**
- ✅ **Anaconda/Conda users**: CUDD is already included in `dd` → Skip Step 2!
- ⚠️ **Standard Python users**: May need to install CUDD separately (see above)

### Step 3: Verify Installation

```bash
# Test both libraries
python -c "import dd; import pulp; print('All libraries installed!')"

# Test BDD specifically (verifies CUDD is working)
python -c "from dd import autoref as bdd; bm = bdd.BDD(); bm.declare('x'); print('BDD with CUDD works!')"
```

If both commands work, you're ready to go! ✅

## Running the Code

### Basic Example

```bash
python petri_net_analyzer.py test_simple.xml
```

### With Custom Objective Weights

```bash
python petri_net_analyzer.py test_simple.xml 1,2,3
```

### Test All Examples

```bash
# Simple net (2 states, no deadlock)
python petri_net_analyzer.py test_simple.xml

# Net with deadlock
python petri_net_analyzer.py test_deadlock.xml

# Net with cycle (no deadlock)
python petri_net_analyzer.py test_cycle.xml

# Net with parallel execution
python petri_net_analyzer.py test_parallel.xml
```

## Understanding the Output

### Task 1: PNML Parsing
- Shows number of places, transitions, arcs
- Displays initial marking
- Verifies consistency

### Task 2: Explicit Reachability
- Number of reachable markings
- Computation time
- Memory usage

### Task 3: Symbolic Reachability (BDD)
- Number of reachable markings (should match Task 2)
- Computation time (usually faster for large nets)
- Number of iterations
- BDD node count

### Task 4: Deadlock Detection
- Reports if deadlock found
- Shows the deadlock marking if found
- Detection time

### Task 5: Optimization
- Optimal marking found
- Optimal objective value
- Computation time

## Common Issues

### Issue: "dd library not found"
**Solution:** `pip install dd` (CUDD is usually bundled, no need to install separately)

### Issue: "CUDD not found" when using dd
**Solution:** 
- ✅ **If using Anaconda/Conda**: CUDD is already included in `dd` - this error shouldn't happen
  - Verify: `python -c "from dd import autoref as bdd; bm = bdd.BDD(); print('OK')"`
  - If this works, CUDD is included and you can ignore the error
- ⚠️ **If using standard Python**: You may need to install CUDD from source (complex, rarely needed)

### Issue: "pulp library not found"
**Solution:** `pip install pulp`

### Issue: BDD tasks not working
**Solution:** 
- ✅ **Anaconda/Conda users**: CUDD is included in `dd` - no need to check separately
  - Just verify: `python -c "from dd import autoref as bdd; bm = bdd.BDD(); print('OK')"`
- ⚠️ **Standard Python users**: 
  - Verify CUDD: `brew list cudd` (macOS) or `dpkg -l | grep cudd` (Ubuntu)
  - Try reinstalling: `pip uninstall dd && pip install dd`

### Issue: ILP solver not found
**Solution:**
- Pulp includes CBC solver by default
- If issues persist, install CBC separately:
  - macOS: `brew install cbc`
  - Ubuntu: `sudo apt-get install coinor-cbc`

## Next Steps

1. **Read TASK_GUIDE.md** for detailed explanations of each task
2. **Read README.md** for complete documentation
3. **Modify test files** to test your own Petri nets
4. **Experiment** with different objective weights for optimization

## Getting Help

- Check TASK_GUIDE.md for implementation details
- Review error messages carefully
- Verify all dependencies are installed
- Test with provided test files first

## File Structure

```
math-modeling/
├── petri_net_analyzer.py    # Main code (all tasks)
├── requirements.txt          # Python dependencies
├── README.md                 # Full documentation
├── TASK_GUIDE.md            # Detailed task explanations
├── QUICK_START.md           # This file
└── test_*.xml               # Test PNML files
```

Good luck with your assignment! 🚀

