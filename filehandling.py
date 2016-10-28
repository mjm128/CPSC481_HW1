import time
import os
import chess

def check4Move(player, N):
	#MoveNum must start at 1 and go up to N
	lastMove = None
	duration = .5
	if player == "X":
		file = "log_y.txt"
	if player == "Y":
		file = "log_x.txt"
	while True:
		with open(file, "r") as f:	
			#Check of file is empty
			if os.stat(file).st_size == 0:
				time.sleep(duration)
			else:
				for line in f:
					lastMove = line
				if lastMove.split(' ')[0] == str(N):
					return lastMove.rstrip('\n')
		time.sleep(duration) 
	
def emptyLogFiles():
	if os.path.getsize("log_x.txt") > 1:
		print("Cleared log files")
		with open("log_x.txt", "w") as f:
			f.seek(0)
			f.truncate()
		with open("log_y.txt", "w") as f:
			f.seek(0)
			f.truncate()