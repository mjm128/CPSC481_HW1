Objective: Implement min-max algorithm

Problem: Develop software to play a relatively simple chess endgame using a mini-max
algorithm. PlayerX has a rook, knight, and king and PlayerY has only the king and knight. With
more chess pieces, PlayerX has higher chance to win this game. So PlayerX should try to win the
game as quickly as possible avoiding any infinite loop or dead end. On the other hand, PlayerY
should try to delay as long as possible, end in a draw, or even win the game if possible when
PlayerX makes mistakes.

Requirements:
	- Anaconda 4.1.1
	- Python 3.5.2
	- Python-chess (pip install python-chess==0.15.2)