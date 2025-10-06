x = 0.5
sum1 = 0

for i in range(1, 6):
	sum1 += ((-1) ** (i - 1)) * ((x - 1) ** i) / i

print(f'f({x}) ~= {sum1:10.9f} with {i} terms')

j = 1;
newSum = 0
diff = 1
while (abs(diff) >= 10**-7):
	diff = ((-1) ** (j - 1)) * ((x - 1) ** j) / j
	newSum += diff
	j += 1

print(f'f({x}) ~= {newSum:10.9f} with {j} terms')