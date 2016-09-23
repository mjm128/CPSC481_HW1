import time
import os

def check4Move(player, moveNum):
	#MoveNum must start at 1 and go up to N
	moveList = []
	if player == "X":
		file = "log_y.txt"
	if player == "Y":
		file = "log_x.txt"
	while True:
		with open(file, "r") as f:	
			#Check of file is empty
			if os.stat(file).st_size == 0:
				time.sleep(2)
				continue
			for line in f:
				moveList.append(line.rstrip())
			if player == "X" and len(moveList) == (moveNum*2):
				break
			if player == "Y" and len(moveList) == (1+((moveNum-1)*2)):
				print(len(moveList))
				break
		#Clear list if move not added yet
		del moveList[:]
		time.sleep(2)
	return moveList[-1]
	
	
print(check4Move("X", 1))