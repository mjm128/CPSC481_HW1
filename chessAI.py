import chess
import random

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()
	
def computerPlayer(board):
	#Call to get which move is best
	board_copy = board
	moveList = []
	for i in board_copy.legal_moves:
		score = alphaBetaMax(board_copy, float("-inf"), float("inf"), 3)
		moveList.append((i, score))
	
	
	return moveList[0][0]
	
def alphaBetaMax(board, alpha, beta, depth):
	if depth == 0:
		return evaluate(board)
	
	#Iterate through legal moves, DFS.
	for i in board.legal_moves:
		board.push(i)
		score = alphaBetaMin(board, alpha, beta, depth-1)
		board.pop()
		if score >= beta:
			return beta
		if score > alpha:
			alpha = score
	return alpha
	
def alphaBetaMin(board, alpha, beta, depth):
	if depth == 0:
		return evaluate(board)
		
	for i in board.legal_moves:
		board.push(i)
		score = alphaBetaMax(board, alpha, beta, depth-1)
		board.pop()
		if score <= alpha:
			return alpha
		if score < beta:
			beta = score
	return beta
	
def evaluate(board):
	return random.randrange(0,10000)
	