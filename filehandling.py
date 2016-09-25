import time
import os

def check4Move(player, moveNum):
	#MoveNum must start at 1 and go up to N
	moveList = []
	duration = 2
	if player == "X":
		file = "log_y.txt"
	if player == "Y":
		file = "log_x.txt"
	while True:
		with open(file, "r") as f:	
			#Check of file is empty
			if os.stat(file).st_size == 0:
				time.sleep(duration)
				continue
			for line in f:
				#Add all lines of the file to a list
				moveList.append(line.rstrip())
			if player == "X" and len(moveList) == (moveNum*2):
				break
			if player == "Y" and len(moveList) == (1+((moveNum-1)*2)):
				break
		del moveList[:] #Clear list if move not added yet
		time.sleep(duration) 
	return moveList[-1] #Return last element of the list
	
def emptyLogFiles():
	with open("log_x.txt", "w") as f:
		f.seek(0)
		f.truncate()
	with open("log_y.txt", "w") as f:
		f.seek(0)
		f.truncate()