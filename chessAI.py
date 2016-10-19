import chess
import chess.uci
import random
import time
from math import *
from operator import itemgetter
from multiprocessing import Pool as ThreadPool, Process, Array, Value, TimeoutError
from ctypes import c_byte, c_int, c_ulonglong, Structure
from os import cpu_count
import copy
import platform

bKposition=[-50,-40,-30,-20,-20,-30,-40,-50,
			-30,-20,-10,-10,-10,-10,-20,-30,
			-30,-10, 20, 30, 30, 20,-10,-30,
			-30,-10, 30, 40, 40, 30,-10,-30,
			-30,-10, 30, 40, 40, 30,-10,-30,
			-30,-10, 20, 30, 30, 20,-10,-30,
			-30,-30,-10,-10,-10,-10,-30,-30,
			-50,-30,-30,-30,-30,-30,-30,-50]
			
knightPos = [-50,-40,-30,-30,-30,-30,-40,-50,
			-40,-20,  0,  0,  0,  0,-20,-40,
			-30,  0, 10, 15, 15, 10,  0,-30,
			-30,  5, 15, 20, 20, 15,  5,-30,
			-30,  0, 15, 20, 20, 15,  0,-30,
			-30,  5, 10, 15, 15, 10,  5,-30,
			-40,-20,  0,  5,  5,  0,-20,-40,
			-50,-40,-30,-30,-30,-30,-40,-50,]

MAX_INT = 100000
MAX_TIME = 10
DEPTH = 4
UPPER = 0
EXACT = 1
LOWER = 2
HAS_KNIGHT = False

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

# grows at about 32k per search
EV_Table = Array(EV_Item, 2097169, lock=False)

# grows at about 11k per search
TT_Table = Array(TT_Item,  524309, lock=False)

#Load evaluation table 
def load_ev(key):
	item = copy.deepcopy(EV_Table[key % len(EV_Table)])
	return item.val if item.key == key else None

#Store evaluation in table
def store_ev(key, val):
	EV_Table[key % len(EV_Table)] = EV_Item(key, val)

#Load transpotition table
def load_tt(key, alpha, beta, depth):
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

#Store transpotition table 
def store_tt(key, score, depth, move, flag):
	m_from = move.from_square if move != None else 0
	m_to = move.to_square if move != None else 0
	TT_Table[key % len(TT_Table)] = TT_Item(key, depth, flag, score, m_from, m_to)

#This function is purely for testing purposes
def randomPlayer(board):
	move = random.choice(list(board.legal_moves))
	return move.uci()

#For testing play against stockfish engine
def stockFish(board, time):
	#Make sure to download a copy of stock fish and place one
	#Version of it in the following relative dir location
	if platform.system() == "Windows":
		engine = chess.uci.popen_engine("stockfish\stockfish-windows")
	else:
		engine = chess.uci.popen_engine("stockfish/stockfish")
	engine.position(board)
	move = engine.go(movetime=time*1000)
	engine.quit()
	return move[0]

def moveThreading(data):
	#data[0] is the move
	#data[1] is the score
	#data[2] is the depth
	#data[3] is the board

	if data[1] == None:
		alpha = -MAX_INT
		beta = MAX_INT
	else:
		alpha = -abs(data[1]) - 5
		beta = abs(data[1]) + 5

	data[3].push(data[0])
	data[1] = -negaScout(data[3], alpha, beta, data[2])
	data[3].pop()

	if data[1] < alpha or data[1] > beta:
		data[3].push(data[0])
		data[1] = -negaScout(data[3], -MAX_INT, MAX_INT, data[2])
		data[3].pop()

	return data

def search(board, start):
	threadData = []
	for i in board.legal_moves:
		threadData.append([i, None, 0, board])

	threads = min(len(threadData), cpu_count()-4)
	pool = ThreadPool(processes=threads)
	moveList = []
	for depth in range(0, 10):
		# set the current depth to search
		for i in range(len(threadData)):
			threadData[i][2] = depth

		result = pool.map_async(moveThreading, threadData)
		
		print(depth)
		try:
			threadData = result.get(MAX_TIME - (time.time() - start))
			threadData = sorted(threadData, key=itemgetter(1), reverse=True)
			moveList = [[item[0], item[1]] for item in threadData]
		except TimeoutError:
			pool.terminate()
			pool.join()
			pool = None
			break

	return moveList

def computerPlayer(board):
	board_copy = board
	
	#start move benchmark
	start = time.time()
	
	#Check if black knight is on board
	if bool(board.pieces(chess.KNIGHT, chess.BLACK)):
		HAS_KNIGHT = True
	else:
		HAS_KNIGHT = False
	
	#Multithreading start
	moveList = search(board, start)
	
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
			if len(moveList) > 1:
				moveList[0][1] = moveList[1][1] - 1 #take away points
				print("THREE_FOLD_REPETITION")
				moveList = sorted(moveList, key=itemgetter(1), reverse=True)
				bestValue = moveList[0][1]
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

def quiescence(board, alpha, beta):
	score = evaluate(board)
	if score >= beta:
		return score
	elif score > alpha:
		alpha = score

	for i in board.legal_moves:
		if not board.is_capture(i):
			continue
		board.push(i)
		score = -quiescence(board, -beta, -alpha)
		board.pop()

		if score >= beta:
			return score
		if score > alpha:
			alpha = score
	return alpha

def isValid(board, move):
	if not move in board.pseudo_legal_moves:
		return False
	board.push(move)
	valid = board.is_valid()
	board.pop()
	return valid

def negaScout(board, alpha, beta, depth):
	if board.result() != "*":
		return evaluate(board)
	if depth == 0:
		return quiescence(board, alpha, beta)

	boundType = UPPER
	item = load_tt(board.zobrist_hash(), alpha, beta, depth)
	if item != None:
		if item[0] != None:
			return item[0]
		elif isValid(board, item[1]):
			board.push(item[1])
			score = -negaScout(board, -beta, -alpha, depth - 1)
			board.pop()

			if score >= beta:
				store_tt(board.zobrist_hash(), score, depth, item[1], LOWER)
				return beta
			elif score > alpha:
				alpha = score
				boundType = EXACT

	b = beta
	c = 0
	bestMove = None
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
		if HAS_KNIGHT:
			ret = heuristicX(board, wR, wN, wK, bK, bN) - heuristicY(board, wR, wN, wK, bK, bN)
		else:
			ret = heuristicX1(board, wR, wN, wK, bK, bN) - heuristicY1(board, wR, wN, wK, bK, bN)
	else:
		if HAS_KNIGHT:
			ret = heuristicY(board, wR, wN, wK, bK, bN) - heuristicX(board, wR, wN, wK, bK, bN)
		else:
			ret = heuristicY1(board, wR, wN, wK, bK, bN) - heuristicX1(board, wR, wN, wK, bK, bN)

	store_ev(board.zobrist_hash(), ret)

	return ret

def heuristicX1(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "1-0" else 0
	if bool(wR): #Check to see if white rook exists
		score += 300 #Has a rook
		
		score += whiteDefRook(board, wR, wK)*2
		score += whiteRookAtk(board, wR, bK)
		
		#Rook attacking around Black King
		if bool( board.attacks(list(bK)[0]).intersection(board.attacks(list(wR)[0])) ):
			score += 5
		
		#defend rook with king
		if bool( board.attacks(list(wK)[0]).intersection(wR) ):
			score += 5
		
		#Rook attacking king
		if bool( board.attacks(list(wR)[0]).intersection(bK) ):
			score += 10
	
	if bool(wN):
		score += 150 #has a Knight
		
		#Knight attacking around Black King
		if bool( board.attacks(list(bK)[0]).intersection(board.attacks(list(wN)[0])) ):
			score += 5
		
		#defend Knight with king
		if bool( board.attacks(list(wK)[0]).intersection(wN) ):
			score += 5
		
		#Knight attacking king
		if bool( board.attacks(list(wN)[0]).intersection(bK) ):
			score += 10
		
	if not bool(bN):
		score += 76
		if not bool(wN):
			score += 75
	if board.is_pinned(chess.BLACK, list(bK)[0]):
		score += 40
	
	if bool( board.attacks(list(bK)[0]).intersection(board.attacks(list(wK)[0])) ):
		score += 10
		
	score += wkMove2bk(wK, bK)*3
	score -= len(board.move_stack)
	score += len(board.attacks(list(wK)[0]))
	
	return score

def heuristicX(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "1-0" else 0
	KnightMoves = None
	KnightMoves = board.attacks(list(wK)[0])
	AroundKing = board.attacks(list(bK)[0])
	if bool(bN):
		x = abs(chess.rank_index(list(wK)[0]) - chess.rank_index(list(bN)[0]))
		y = abs(chess.file_index(list(wK)[0]) - chess.file_index(list(bN)[0]))
		score -= x+y
		KnightMoves = board.attacks(list(bN)[0])
		KnightMoves = KnightMoves.intersection(bN)
		
		if bool(wR):
			x = abs(chess.rank_index(list(wR)[0]) - chess.rank_index(list(bN)[0]))
			y = abs(chess.file_index(list(wR)[0]) - chess.file_index(list(bN)[0]))
			score -= min(x,y)
			AtkingKnight = AtkingKnight.intersection(board.attacks(list(wR)[0])) 
			score += 300
		
		if bool(wN):
			x = abs(chess.rank_index(list(wR)[0]) - chess.rank_index(list(bN)[0]))
			y = abs(chess.file_index(list(wR)[0]) - chess.file_index(list(bN)[0]))
			score -= x+y
			AtkingKnight = AtkingKnight.intersection(board.attacks(list(wN)))
			score += 150
	
	if board.is_pinned(chess.WHITE, list(bK)[0]):
		print("PINNED")
		print(board)
		score += 50
	
	score += len(AroundKing.intersection(AtkingKnight))
	score += 50 if board.is_check() else 0
	score += len(AtkingKnight.intersection(KnightMoves)) * 4
	score -= len(board.move_stack)
	score += len(board.attacks(list(wK)[0]))
	
	return score
	
def heuristicY(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "0-1" else 0
	score += 9001 if board.is_stalemate() else 0
	score += len(board.move_stack)
	score += bKposition[list(bK)[0]]
	score += len(board.attacks(list(bK)[0]))
	
	if bool(bN):
		score += 150
		score += knightPos[list(bN)[0]]
	
	return score

def heuristicY1(board, wR, wN, wK, bK, bN):
	score = 0
	score += 9001 if board.result() == "0-1" else 0
	score += 9001 if board.is_stalemate() else 0
	score += len(board.move_stack)
	score += bKposition[list(bK)[0]]
	score += len(board.attacks(list(bK)[0]))
	
	if bool(bN): 
		score += 150
		score += len(board.attacks(list(bK)[0]).intersection(bN)) * 6
	
	return score
	
def whiteDefRook(board, wr, wk):
	x = chess.rank_index(list(wr)[0]) - chess.rank_index(list(wk)[0])
	y = chess.file_index(list(wr)[0]) - chess.file_index(list(wk)[0])
	return 20-floor((y**2 + x**2)**(1/2))
	
def whiteRookAtk(board, wr, bk):
	x = abs(chess.rank_index(list(wr)[0]) - chess.rank_index(list(bk)[0]))
	y = abs(chess.file_index(list(wr)[0]) - chess.file_index(list(bk)[0]))
	return 8-min(x,y)
	
def wkMove2bk(wk, bk):
	x = chess.rank_index(list(wk)[0]) - chess.rank_index(list(bk)[0])
	y = chess.file_index(list(wk)[0]) - chess.file_index(list(bk)[0])
	return 20 - floor((y**2 + x**2)**(1/2))
