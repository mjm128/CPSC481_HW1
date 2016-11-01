#!/usr/bin/env python3

import chess, chessAI

STARTING_BOARD = '2n1k3/8/8/8/8/8/8/4K1NR w - - 0 0'

def moveListToStr(moveList):
	l = [item[0].uci() + '(' + str(item[1]) + ')' for item in moveList]
	return ', '.join(l)

def analyze_findMove(board, args):
	# do an initial search and discard the results
	# as they will be useless because of searhc instability
	chessAI.computerPlayer(board)

	depth, move, moveList = chessAI.computerPlayer(board)
	if args == '':
		move = moveList[0][0]
		score = moveList[0][1]
	else:
		try:
			findMove = chess.Move.from_uci(args)
			if not chessAI.isValid(board, findMove):
				print("illegal move: " + args)
				return None
			found = False
			for item in moveList:
				if item[0] == findMove:
					found = True
					move = item[0]
					score = item[1]
					break
			if not found:
				print("move not found")
				return None
		except ValueError:
			print("invalid move: " + args)
			return None

	print("depth : " + str(depth))
	print("values: " + moveListToStr(moveList))
	print()

	return depth, move, score

def analyze(b, args):
	if args != '':
		try:
			move = chess.Move.from_uci(args)
			if not chessAI.isValid(b, move):
				print("illegal move: " + args)
				return
		except ValueError:
			print("invalid move: " + args)
			return

	# copy board so we don't apply the moves to the board passed in
	board = b.copy()

	# do an initial search and discard the results
	# as they will be useless because of search instability
	depth, m, moveList = chessAI.computerPlayer(board)
	if args == '':
		move = moveList[0][0]

	depth, m, moveList = chessAI.computerPlayer(board)
	print(board)
	print("depth : " + str(depth))
	print("values: " + moveListToStr(moveList))
	print()

	save_depth = chessAI.MAX_DEPTH
	chessAI.MAX_DEPTH = depth

	while chessAI.MAX_DEPTH > 0:
		board.push(move)
		if board.result() != "*":
			break
		depth, move, moveList = chessAI.computerPlayer(board)
		print(board)
		print("depth : " + str(depth))
		print("values: " + moveListToStr(moveList))
		print()
	
		chessAI.MAX_DEPTH -= 1

	chessAI.MAX_DEPTH = save_depth

def runCmd(board):
	line = input(">>> ")
	parts = line.split(' ', 1)
	if len(parts) == 2:
		cmd = parts[0]
		args = parts[1]
	else:
		cmd = parts[0]
		args = ''

	if cmd == "quit":
		return False
	elif cmd == "reset":
		board.set_fen(STARTING_BOARD)
		print(board)
	elif cmd == "print":
		print(board)
		print("moves: " + str([item.uci() for item in board.move_stack]))
		print("fen  : " + board.fen())
	elif cmd == "hash":
		print(board.zobrist_hash())
	elif cmd == "limits":
		print("depth: " + str(chessAI.MAX_DEPTH))
		print("time : " + str(chessAI.MAX_TIME))
	elif cmd == "settime":
		try:
			chessAI.MAX_TIME = int(args)
			print(chessAI.MAX_TIME)
		except ValueError:
			print("invalid time: " + args)
	elif cmd == "setdepth":
		try:
			chessAI.MAX_DEPTH = int(args)
		except:
			print("invalid depth: " + args)
	elif cmd == "setboard":
		board.set_fen(args)
		print(board)
	elif cmd == "undo":
		try:
			board.pop()
		except IndexError:
			pass
		print(board)
	elif cmd == "move":
		try:
			move = chess.Move.from_uci(args)
			if chessAI.isValid(board, move):
				board.push(move)
				print(board)
			else:
				print("Illegal move: " + args)
		except ValueError:
			print("Invalid move: " + args)
	elif cmd == "analyze":
		analyze(board, args)
	elif cmd == "go":
		depth, move, moveList = chessAI.computerPlayer(board)
		board.push(move)
		print(board)
		print('depth : ' + str(depth))
		print('move  : ' + move.uci())
		print('values: ' + moveListToStr(moveList))
	else:
		print('invalid command: ' + cmd)

	return True

def main():
	board = chess.Board(STARTING_BOARD)
	while runCmd(board):
		pass

if __name__ == "__main__":
	main()
