import time
import os

def check4Move(player):
	if player == "X":
		file = "log_x.txt"
	if player == "Y":
		file = "log_y.txt"
	while True:
		with open(file, "r") as f:
			lastLine = ""
			if os.stat(file).st_size == 0:
				time.sleep(1)
				continue
			for line in f:
				lastLine = line.rstrip()
			if lastLine[0] != player:
				break
		time.sleep(1)
	return lastLine
	
	
print(check4Move("X"))