# Declare empty list that contain student and their mark
studentList = []

# Input student name and their mark
for i in range(int(input("Number of student : "))):
    info = list(input().split(" "))
    studentList.append(info)

# Reverse order from highest mark
studentList.sort(key=lambda x: x[1], reverse=True)

# Print 3 highest student if possible
for i in range(3 if len(studentList) >= 3 else len(studentList)):
    print(f"Rank {i+1} : {studentList[i][0]}")
