#Problem 1
def between(value, low = 0, high = 0.3):
    if (value >= low and value <= high):
        return True 
    else:
        return False

print(between(0.2))

#Problem 2
def rangef(max, step):
    r1 = 0
    while True:
        if (r1 > max):
            break
        yield r1
        r1 += step

for i in rangef(5, 0.5): 
    print(i, end = ' ')


#Problem 3
from copy import deepcopy 

alist = list(rangef(1, 0.25))
print(alist)

blist = deepcopy(alist)
blist.reverse()
alist.extend(blist)
print(alist)

alist.sort(key = lambda x: between(x))
print(alist)


#Problem 4
clist = [n for n in range(17) if ((n % 2.0 == 0) or (n % 3.0 == 0))]
print(clist)