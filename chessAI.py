import chess
import random
from math import *
from operator import itemgetter

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()
	
def computerPlayer(board):
	#Call to get which move is best
	board_copy = board
	moveList = []
	bestMoves = []
	depth = 5
	if len(board.move_stack) <= 3:
		depth = 5
	for i in board_copy.legal_moves:
		board_copy.push(i)
		score = alphaBetaMin(board_copy, float("-inf"), float("inf"), depth)
		board_copy.pop()
		moveList.append((i, score))
	
	#Get the best score from moves
	moveList = sorted(moveList, key=itemgetter(1), reverse=True)
	bestValue = moveList[0][1]
	index = len(moveList)
	for (i, v) in enumerate(moveList):
		if v[1] != bestValue:
			index = i
			break
	print(moveList)
	return moveList[random.randrange(0, index)][0] #Return random best move
	
def alphaBetaMax(board, alpha, beta, depth):
	if depth == 0 or board.is_checkmate() or board.is_stalemate():
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
	if depth == 0 or board.is_checkmate() or board.is_stalemate():
		return -evaluate(board)
		
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
	wR = board.pieces(chess.ROOK, chess.WHITE)
	wN = board.pieces(chess.KNIGHT, chess.WHITE)
	wK = board.pieces(chess.KING, chess.WHITE)
	bK = board.pieces(chess.KING, chess.BLACK)
	bN = board.pieces(chess.KNIGHT, chess.BLACK)
	if board.turn == chess.WHITE:
		return heuristicX(board, wR, wN, wK, bK, bN) - heuristicY(board, wR, wN, wK, bK, bN)
	else:
		return heuristicY(board, wR, wN, wK, bK, bN) - heuristicX(board, wR, wN, wK, bK, bN)

def heuristicX(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "1-0" else 0
	score += whiteDefRook(board, wR, wK)
	score += whiteRookAtk(board, wR, bK)
	if len(wR) > 0:
		score -= len(board.move_stack)
		score += len(board.attacks(list(wK)[0]))
	
	score += len(wN) * 150
	score += len(wR) * 300
	
	return score

def heuristicY(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "0-1" else 0
	score += len(bN) * 150
	
	return score
	
def whiteDefRook(board, wr, wk):
	score = 0
	guard = board.attackers(chess.WHITE, list(wk)[0])
	for squares in guard:
		if squares == list(wk)[0]:
			score = 50 #King gaurding Rook
	x = abs(chess.rank_index(list(wr)[0]) - chess.rank_index(list(wk)[0]))
	y = abs(chess.file_index(list(wr)[0]) - chess.file_index(list(wk)[0]))
	return score -min(x,y)
	return 0
	
def whiteRookAtk(board, wr, bk):
	x = abs(chess.rank_index(list(wr)[0]) - chess.rank_index(list(bk)[0]))**2
	y = abs(chess.file_index(list(wr)[0]) - chess.file_index(list(bk)[0]))**2
	return -min(x,y)
	return 0