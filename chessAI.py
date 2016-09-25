import chess
import random

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()
	