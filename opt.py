import pyomo.environ as pyomo

m = [
    {0,1,2,15,16},
    {0,1,2,3,4,16,15,14,13,12,11,10},
    {3,4,5,6,11,15,14},
    {0,1,2,3,4,5,6,11,14,15,16},
    {0,1,2,3,5,6,7,11,12,13,14,15,16},
    {0,1,2,6,7,8,9,10,11,12,15,16},
    {0,1,2,3,6,7,8,9,10,11,12,15,16},
    {0,1,2,3,4,5,6,7,10,11,12,13,14,15,16}
]

# we have a 3d matrix of 17 * 8 * 3 (for three choices)

ADJ = 0
ROW = 1
COL = 2

MODS = range(3)
COLUMNS = range(17)
ROWS = range(8)

# A[i, k, k] is binary

# only one modifier
# \sum{i=0}^{16} \sum{j=0}^{7} \sum{k=0}^{3} A[i, j, k] = 1

# objective is to maximize effect:
# \sum_{i=0}^{16} \sum_{j=0}^{7}:
#   (
#     (A[i-1, j, ADJ] + A[i+1, j, ADJ] + A[i, j-1, ADJ] + A[i, j+1, ADJ]) * 1.4 +
#     \sum_{c \in connectedHorizontal(i, j) where c != i} A[c, j, ROW] * 1.25 +
#     \sum_{c \in connectedVertical(i, j) where c != j} A[i, c, COL] * 1.25
#   ) * A[i, j, CLEAR]

model = pyomo.ConcreteModel()

model.A = pyomo.Var(COLUMNS, ROWS, MODS, domain=pyomo.Binary)

CELLS = [(c, r) for c in COLUMNS for r in ROWS]

ACTIVE_CELLS = [(c, r) for r, cols in enumerate(m) for c in cols]

model.cons = pyomo.ConstraintList()

for c, r in CELLS:
    if c in m[r]:
        model.cons.add(sum(model.A[c, r, k] for k in MODS) <= 1)
    else:
        model.cons.add(sum(model.A[c, r, k] for k in MODS) == 0)

def in_bounds(c, r):
    return c in COLUMNS and r in ROWS

def safe_get(c, r, k):
    if in_bounds(c, r):
        return model.A[c, r, k]
    return 0

def connected(xs, start, cont):
  curr = start
  build = []
  while True:
    if curr not in xs:
      return build
    
    build.append(curr)
    curr = cont(curr)
  
  return build

def connectedHorizontal(c, r):
  left = connected(m[r], c-1, lambda x: x - 1)
  right = connected(m[r], c+1, lambda x: x + 1)
  return left + right

def connectedVertical(c, r):
  rows = set([row_idx for row_idx, row in enumerate(m) if c in row])
  up = connected(rows, r-1, lambda x: x - 1)
  down = connected(rows, r+1, lambda x: x + 1)
  return up + down

def adj(c, r): 
  return (safe_get(c-1, r, ADJ) + safe_get(c+1, r, ADJ) + safe_get(c, r-1, ADJ) + safe_get(c, r+1, ADJ)) * 0.4

def row(c, r):
  print("row", c, r, connectedHorizontal(c, r))
  return sum(model.A[x, r, ROW] for x in connectedHorizontal(c, r)) * 0.25

def col(c, r):
  print("col", c, r, connectedVertical(c, r))
  return sum(model.A[c, x, COL] for x in connectedVertical(c, r)) * 0.25

def multiplier(c, r):
  return 1 + adj(c, r) + row(c, r) + col(c, r)

def non_mod(c, r):
  return 1 - sum(model.A[c, r, k] for k in MODS)

def active_non_mod(c, r):
  if in_bounds(c, r) and c in m[r]:
    return non_mod(c, r)
  else:
    return 0

# any adj must have more than 2 non-modifiers
for c, r in ACTIVE_CELLS:
  model.cons.add(active_non_mod(c-1, r) + active_non_mod(c+1, r) + active_non_mod(c, r-1) + active_non_mod(c, r+1) >= 3 * model.A[c, r, ADJ])

# connected direction must have more than 4 non-modifiers
for c, r in ACTIVE_CELLS:
  model.cons.add(sum(active_non_mod(x, r) for x in connectedHorizontal(c, r)) >= 5 * model.A[c, r, ROW])
  model.cons.add(sum(active_non_mod(c, y) for y in connectedVertical(c, r)) >= 5 * model.A[c, r, COL])

# big M variable
M = 2.8
model.w = pyomo.Var(COLUMNS, ROWS, domain=pyomo.NonNegativeReals)

for c, r in ACTIVE_CELLS:
  model.cons.add(model.w[c, r] <= multiplier(c, r))
  model.cons.add(model.w[c, r] <= M * (1 - model.A[c, r, ADJ] - model.A[c, r, ROW] - model.A[c, r, COL]))

model.obj = pyomo.Objective(
  expr = sum(model.w[c, r] for c, r in ACTIVE_CELLS),
  sense=pyomo.maximize
)

solver = pyomo.SolverFactory("cbc")
model.pprint()
solution = solver.solve(model, tee=True)

#print(solution)

for r in ROWS:
  s = ""
  for c in COLUMNS:
    sub = ""
    if c in m[r]:
      for k in MODS:
        if model.A[c, r, k].value == 1:
          sub = "ARC"[k]

      if sub == "":
        sub = "N"
    else:
      sub = "E"

    s += sub + " | "
  print(s)

#print("Objective: ", modifiers())
