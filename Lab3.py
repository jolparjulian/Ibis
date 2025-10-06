import random

random.seed()

guess = 0
maxTurns = 12
codeLen = 4
numCorPlace = [None] * codeLen
numWrongPlace = [None] * codeLen
numWrongPlaceCorChecker = [False] * codeLen

correct = []
for i in range(codeLen):
    correct.append(str(random.randint(1, 6)))

print("Guess a sequence of 4 values from 1-6")
print("\u25CB = one element is in the code but in the wrong place")
print("\u25CF = one element is in the code but in the correct place")

print("ans: " + str(correct))

for turnCount in range(1, maxTurns + 1):
    print("\nGuess a sequence of 4 values from 1-6")
    while True:
        guess = input(f'Guess {turnCount} of {maxTurns}: ')
        if (len(guess) != 4) or not guess.isdigit():
            print("Not a valid input")
            continue
        for el in guess:
            if int(el) not in range(1, 7):
                print("Not a valid input")
                continue
        break

    for j in range(codeLen):
        if (int(correct[j]) == int(guess[j])):
            numCorPlace[j] = True
        else:
            numCorPlace[j] = False
    
    numWrongPlace = [False] * codeLen
    numWrongPlaceCorChecker = [False] * codeLen
    for h in range(codeLen):
        for k in range(codeLen):
            if (int(guess[h]) == int(correct[k]) and (not numCorPlace[h]) and (not numWrongPlaceCorChecker[k])):
                numWrongPlace[h] = True
                numWrongPlaceCorChecker[k] = True


    ansString = ""
    for m in numCorPlace:
        if m:
            ansString += "\u25CF"
    for n in numWrongPlace:
        if n:
            ansString += "\u25CB"
    
    print(ansString)

    if (numCorPlace == [True] * codeLen):
        print("Correct - you win!")
        break

if (numCorPlace != [True] * codeLen):
    print(f"The code was {"".join(correct)}")