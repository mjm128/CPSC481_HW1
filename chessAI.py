import chess
import random
import time
from math import *
from operator import itemgetter
from multiprocessing import Pool as ThreadPool
from os import cpu_count

bKposition=[0, 1, 2, 2, 2, 2, 1, 0,
			1, 1, 3, 3, 3, 3, 1, 1,
			2, 3, 4, 4, 4, 4, 3, 2,
			2, 3, 4, 5, 5, 4, 3, 2,
			2, 3, 4, 5, 5, 4, 3, 2,
			2, 3, 4, 4, 4, 4, 3, 2,
			1, 1, 3, 3, 3, 3, 1, 1,
			0, 1, 2, 2, 2, 2, 1, 0]

MAX_INT = 100000
DEPTH = 4

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()

def moveThreading(data):
	#data[0] is the move
	#data[1] is the board
	data[1].push(data[0])
	score = -negaScout(data[1], -MAX_INT, MAX_INT, DEPTH)
	data[1].pop()
	return (data[0], score)
		
def computerPlayer(board):
	#Call to get which move is best
	board_copy = board
	moveList = []
	
	#start move benchmark
	start = time.time()
	
	#Multithreading start
	threadData = []
	threads = min(len(board_copy.legal_moves), (cpu_count()-1))
	pool = ThreadPool(processes=threads)
	
	for i in board_copy.legal_moves:
		threadData.append((i, board_copy))
	
	moveList = pool.map(moveThreading, threadData)
	
	#end multithreading
	pool.close()
	pool.join()
	
	#Output move benchmark time
	if board.turn == chess.WHITE:
		with open("time_x.txt", "a+") as f:
			f.write(str(time.time() - start) + "\n")
	if board.turn == chess.BLACK:
		with open("time_y.txt", "a+") as f:
			f.write(str(time.time() - start) + "\n")
	
	#Get the best score from moves
	moveList = sorted(moveList, key=itemgetter(1), reverse=True)
	bestValue = moveList[0][1]
			
	#Check for 3 fold repetition move
	if (board.turn == chess.WHITE):
		for (i, v) in enumerate(moveList):
			board_copy.push(v[0])
			if board_copy.can_claim_threefold_repetition():
				moveList[i] = (v[0], v[1]-10) #Takeaway 10 points
				print("THREE_FOLD_REPETITION")
				board_copy.pop()
				break
			board_copy.pop()
	if (board.turn == chess.BLACK):
		for i in moveList:
			board_copy.push(i[0])
			if board_copy.can_claim_threefold_repetition() and i[1] == bestValue:
				board_copy.pop()
				return (i[0]) #Return threefold repition move
			board_copy.pop()
	
	#Get index range of best moves
	index = len(moveList)
	for (i, v) in enumerate(moveList):
		if v[1] != bestValue:
			index = i
			break
	
	print(moveList)
	time.sleep(1)
	return moveList[random.randrange(0, index)][0] #Return random best move
	
def negaScout(board, alpha, beta, depth):
	if depth == 0 or board.result() != "*":
		return evaluate(board)

	b = beta
	c = 0
	for i in board.legal_moves:
		board.push(i)
		score = -negaScout(board, -b, -alpha, depth - 1)
		board.pop()
		if score > alpha and score < beta and c > 0:
			board.push(i)
			score = -negaScout(board, -beta, -alpha, depth - 1)
			board.pop()
		alpha = max(alpha, score)
		if alpha >= beta:
			return alpha
		b = alpha + 1
		c += 1
	return alpha
	
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
	if len(wR) > 0: #Check to see if white rook exists
		score += whiteDefRook(board, wR, wK)*2
		score += whiteRookAtk(board, wR, bK)
		
	score += wkMove2bk(wK, bK)*3
	score -= len(board.move_stack)
	score += len(board.attacks(list(wK)[0]))	

	score += len(wN) * 150
	score += len(wR) * 300
	
	return score

def heuristicY(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "0-1" else 0
	score += 9001 if board.is_stalemate() else 0
	score += len(bN) * 150
	score += len(board.move_stack)
	score += bKposition[list(bK)[0]]
	score += len(board.attacks(list(bK)[0]))
	
	return score
	
def whiteDefRook(board, wr, wk):
	score = 0
	guard = board.attackers(chess.WHITE, list(wk)[0])
	if len(guard) > 0:
			score = 50 #King gaurding Rook
	x = chess.rank_index(list(wr)[0]) - chess.rank_index(list(wk)[0])
	y = chess.file_index(list(wr)[0]) - chess.file_index(list(wk)[0])
	return score + (20-floor((y**2 + x**2)**(1/2)))
	
def whiteRookAtk(board, wr, bk):
	x = abs(chess.rank_index(list(wr)[0]) - chess.rank_index(list(bk)[0]))
	y = abs(chess.file_index(list(wr)[0]) - chess.file_index(list(bk)[0]))
	return max(x,y)
	
def wkMove2bk(wk, bk):
	x = chess.rank_index(list(wk)[0]) - chess.rank_index(list(bk)[0])
	y = chess.file_index(list(wk)[0]) - chess.file_index(list(bk)[0])
	return 20 - floor((y**2 + x**2)**(1/2))