number = int(input("Input number : "))

# count all factors of a number
count = 0

# list of all factors of a number
factor = []

# find factor of positive integer
if number > 0:
    for i in range(1, number+1):
        if number % i == 0:
            factor.append(i)

# joining all factors of a number
factorElement = ', '.join(str(x) for x in factor)

# show the number of factors and all the factors element
print(f"{number} has {len(factor)} factors" if len(factor) > 1 else f"{number} has {len(factor)} factor")
print(f"Factors of {number} are {factorElement}" if len(factor) > 1 else f"Factor of {number} is {factorElement}")
