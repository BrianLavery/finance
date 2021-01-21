a = 1
b = 1.2
c = 3.7
d = 5.0

print(a)

print(a%1)
print(b%1)
print(c%1)
print(d%1)

if a%1 != 0 or a<0:
    print("a is not a positive integer")
if b%1 != 0 or b<0:
    print("b is not a positive integer")
if c%1 != 0 or c<0:
    print("c is not a positive integer")
if d%1 != 0 or d<0:
    print("d is not a positive integer")