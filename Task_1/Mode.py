# Input list of numbers
lists = list(map(int, input().split(" ")))

# FreqData for storing data number and their frequency
freqData ={}

# Append number in freqData if doesn't exist, otherwise adding their frequency by 1
for i in lists:
    if i not in freqData:
        freqData[i] = 1
    else:
        freqData[i] += 1

higher = 0

# Find highest frequency of whole numbers
for i in freqData:
    if freqData[i] > higher:
        higher = freqData[i]

# Print mode from list of numbers
print("Mode : ", end=" ")
for i in freqData:
    if freqData[i] == higher:
        print(i, end=" ")