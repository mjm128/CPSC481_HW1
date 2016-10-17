import chess
import chess.uci
import random
import time
from math import *
from operator import itemgetter
from multiprocessing import Pool as ThreadPool, Array, Value
from ctypes import c_byte, c_int, c_ulonglong, Structure
from os import cpu_count
import copy

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
UPPER = 0
EXACT = 1
LOWER = 2

class TT_Item(Structure):
	_fields_ = [
		('key', c_ulonglong),
		('depth', c_int),
		('flag', c_byte),
		('score', c_int),
		('m_from', c_byte),
		('m_to', c_byte)
	]

class EV_Item(Structure):
	_fields_ = [
		('key', c_ulonglong),
		('val', c_int)
	]

EV_Table = Array(EV_Item, 16 * 1000000)
TT_Table = Array(TT_Item, 16 * 1000000)
BEST_SCORE = Value(c_int, -MAX_INT)

def load_ev(key):
	with EV_Table.get_lock():
		item = copy.deepcopy(EV_Table[key % len(EV_Table)])
	return item.val if item.key == key else None

def store_ev(key, val):
	with EV_Table.get_lock():
		EV_Table[key % len(EV_Table)] = EV_Item(key, val)

def load_tt(key, alpha, beta, depth):
	with TT_Table.get_lock():
		item = copy.deepcopy(TT_Table[key % len(TT_Table)])
	if item.key != key:
		return None
	move = chess.Move(item.m_from, item.m_to)
	if item.depth < depth:
		return [None, move]
	elif item.flag == UPPER:
		return [alpha, move] if item.score < alpha else [None, move]
	elif item.flag == EXACT:
		return [item.score, move]
	else:
		return [beta, move] if item.score >= beta else [None, move]

def store_tt(key, score, depth, move, flag):
	m_from = move.from_square if move != None else 0
	m_to = move.to_square if move != None else 0
	with TT_Table.get_lock():
		TT_Table[key % len(TT_Table)] = TT_Item(key, depth, flag, score, m_from, m_to)

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()

#For testing play against stockfish engine
def stockFish(board, time):
	#Make sure to download a copy of stock fish and place one
	#Version of it in the following relative dir location
	engine = chess.uci.popen_engine("stockfish\stockfish")
	engine.position(board)
	move = engine.go(movetime=time*1000)
	return move[0]

def moveThreading(data):
	#data[0] is the move
	#data[1] is the score
	#data[2] is the depth
	#data[3] is the board
	with BEST_SCORE.get_lock():
		best = BEST_SCORE.value

	data[3].push(data[0])
	data[1] = -negaScout(data[3], -abs(best), MAX_INT, data[2])
	data[3].pop()

	with BEST_SCORE.get_lock():
		BEST_SCORE.value = max(best, data[1])

	return data

def search(board):
	# reset lower starting search window
	BEST_SCORE.value = -MAX_INT

	threadData = []
	for i in board.legal_moves:
		threadData.append([i, 0, 0, board])

	threads = min(len(board.legal_moves), cpu_count() - 1)
	for depth in range(0, DEPTH + 1):
		# set the current depth to search
		for i in range(len(threadData)):
			threadData[i][2] = depth
		pool = ThreadPool(processes=threads)
		threadData = pool.map(moveThreading, threadData)
		pool.close()
		pool.join()
		threadData = sorted(threadData, key=itemgetter(1), reverse=True)

	moveList = []
	for item in threadData:
		moveList.append((item[0], item[1]))
	return moveList

def computerPlayer(board):
	#Call to get which move is best
	board_copy = board
	
	#start move benchmark
	start = time.time()
	
	#Multithreading start
	moveList = search(board)
	
	#Output move benchmark time
	if board.turn == chess.WHITE:
		with open("time_x.txt", "a+") as f:
			f.write(str(time.time() - start) + "\n")
	if board.turn == chess.BLACK:
		with open("time_y.txt", "a+") as f:
			f.write(str(time.time() - start) + "\n")
	
	#Get the best score from moves
	bestValue = moveList[0][1]
			
	#Check for 3 fold repetition move
	if (board.turn == chess.WHITE):
		board_copy.push(moveList[0][0])
		if board_copy.can_claim_threefold_repetition():
			moveList[0][1] = moveList[0][1] - 50 #take away 50 points
			print("THREE_FOLD_REPETITION")
			moveList = sorted(moveList, key=itemgetter(1), reverse=True)
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

	item = load_tt(board.zobrist_hash(), alpha, beta, depth)
	if item != None and item[0] != None:
		return item[0]

	b = beta
	c = 0
	bestMove = None
	boundType = UPPER
	for i in board.legal_moves:
		board.push(i)
		score = -negaScout(board, -b, -alpha, depth - 1)
		board.pop()
		if score > alpha and score < beta and c > 0:
			board.push(i)
			score = -negaScout(board, -beta, -alpha, depth - 1)
			board.pop()
		if score > alpha:
			boundType = EXACT
			bestMove = i
			alpha = score
			if alpha >= beta:
				boundType = LOWER
				break
		b = alpha + 1
		c += 1

	store_tt(board.zobrist_hash(), alpha, depth, bestMove, boundType)

	return alpha
	
def evaluate(board):
	val = load_ev(board.zobrist_hash())
	if val != None:
		return val

	wR = board.pieces(chess.ROOK, chess.WHITE)
	wN = board.pieces(chess.KNIGHT, chess.WHITE)
	wK = board.pieces(chess.KING, chess.WHITE)
	bK = board.pieces(chess.KING, chess.BLACK)
	bN = board.pieces(chess.KNIGHT, chess.BLACK)
	if board.turn == chess.WHITE:
		ret = heuristicX(board, wR, wN, wK, bK, bN) - heuristicY(board, wR, wN, wK, bK, bN)
	else:
		ret = heuristicY(board, wR, wN, wK, bK, bN) - heuristicX(board, wR, wN, wK, bK, bN)

	store_ev(board.zobrist_hash(), ret)

	return ret

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