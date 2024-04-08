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

CLEAR = 0
ADJ = 1
ROW = 2
COL = 3

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

model.A = pyomo.Var(range(17), range(8), range(4), domain=pyomo.Binary)

model.cons = pyomo.ConstraintList()

for c in range(17):
    for r in range(8):
        n = 1 if c in m[r] else 0
        model.cons.add(sum(model.A[c, r, k] for k in range(4)) == n)

def safe_get(c, r, k):
    if c < 0 or 16 < c or r < 0 or 7 < r:
        return 0
    return model.A[c, r, k]

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

def multiplier(c, r):
  return (safe_get(c-1, r, ADJ) + safe_get(c+1, r, ADJ) + safe_get(c, r-1, ADJ) + safe_get(c, r+1, ADJ)) * 1.4 + sum(model.A[x, r, ROW] for x in connectedHorizontal(c, r)) * 1.25 + sum(model.A[c, x, COL] for x in connectedVertical(c, r)) * 1.25

modifiers = sum(
  sum(
    multiplier(c, r) * model.A[c, r, CLEAR]
    for r in range(8)
  )
  for c in range(17)
)

model.obj = pyomo.Objective(
  expr = modifiers,
  sense=pyomo.maximize
)

print(sum(len(x) for x in m))

solver = pyomo.SolverFactory("mindtpy")
solution = solver.solve(model, tee=True, mip_solver='cbc', nlp_solver='ipopt')

print(solution)

for r in range(8):
  s = ""
  for c in range(17):
    sub = ""
    if c in m[r]:
      for k in range(4):
        if model.A[c, r, k].value == 1:
          sub = "CAR0"[k]
    else:
      sub = "E"

    s += sub + " | "
  print(s)

print("Objective: ", modifiers())