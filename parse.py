#!/usr/bin/env python3

import sys
import re
from dateparser import parse as dparse

#filename = 'games/h2h/HV-1dafydd-Eucalyx-2011-04-17-2258.sgf'
filename = sys.argv[1]

tokens = {
    'Q': 'Queen',
    'B': 'Beetle',
    'G': 'Grasshopper',
    'S': 'Spider',
    'A': 'Ant',
    'M': 'Mosquito',
    'L': 'Ladybug',
    'P': 'Pillbug'
}

re_action = re.compile(r'^; P(.)\[\d+ (p?(?:dropb|move)) (. )?(.{1,3}) [A-Z] \d+ ([^\]]*)\]')
re_inside = re.compile(r'^.*\[(.*)\].*$')


def gd(txt):
    rem = re_inside.match(txt)
    grs = rem.groups()
    if grs and len(grs) == 1:
        return grs[0].strip()
    else:
        return None


class Player(object):
    def __init__(self, color):
        self.color = color
        self.typ = None
        self.name = None
        self.rank = None
        self.time = None


class Action(object):
    def __init__(self):
        self.player = None
        self.typ = None
        self.orig_token = None
        self.target_token = None
        self.target_pos = None


class Game(object):
    def __init__(self):
        self.typ = None
        self.version = None
        self.date = None
        self.white = Player('w')
        self.black = Player('b')
        self.moves = []
        self.board = {}
        self.opener = ([], [])
        self.winner = None

    def parseMoves(self):
        moves = self.moves

        # player = w, typ = dropb, orig_token = wg1, target_token = bs2, target_pos = r/
        for m in moves:
            #print('{}: {} to {} of {}'.format(m.player, m.orig_token, m.target_pos, m.target_token))

            if m.target_token == '.':
                new_pos = (0, 0, 0)
            else:
                orig_pos = self.board.get(m.orig_token)
                target_pos = self.board.get(m.target_token)  # error checking

                new_x, new_y, new_z = target_pos
                if m.target_pos.startswith('l'):
                    new_x += -1
                    if m.target_pos.endswith('-'):
                        new_x += -1
                elif m.target_pos.startswith('r'):
                    new_x += 1
                    if m.target_pos.endswith('-'):
                        new_x += 1

                if m.target_pos.endswith('d'):
                    new_y += -1
                elif m.target_pos.endswith('u'):
                    new_y += 1

                if m.target_pos == 't-':
                    new_z += 1

                new_pos = (new_x, new_y, new_z)

            self.board[m.orig_token] = new_pos

            #self.printHex()
            #print('\n==============\n')

        #self.printHex()

        self.checkWinner()

    def printHex(self):
        board = self.board

        max_x = max([x[0] for x in board.values()])
        min_x = min([x[0] for x in board.values()])
        max_y = max([x[1] for x in board.values()])
        min_y = min([x[1] for x in board.values()])

        xy = [[None] * (max_x - min_x + 1) for i in range(max_y - min_y + 1)]

        for k, v in board.items():
            xy[max_y - v[1]][v[0] - min_x] = k

        print()
        for i in xy:
            print(''.join([' /   \\ ' if j else ' ' * 7 for j in i]))
            print(''.join(['| {:3} |'.format(j) if j else ' ' * 7 for j in i]))
            print(''.join([' \\   / ' if j else ' ' * 7 for j in i]))
        print()

    def checkWinner(self):
        vals = self.board.values()

        wq_x, wq_y, wq_z = self.board.get('wq')
        wUL = wL = wDL = wUR = wR = wDR = False
        for v in vals:
            if v[0] == wq_x - 1:
                if v[1] == wq_y + 1:
                    wUL = True
                elif v[1] == wq_y - 1:
                    wDL = True
            elif v[0] == wq_x - 2 and v[1] == wq_y:
                wL = True
            elif v[0] == wq_x + 1:
                if v[1] == wq_y + 1:
                    wUR = True
                elif v[1] == wq_y - 1:
                    wDR = True
            elif v[0] == wq_x + 2 and v[1] == wq_y:
                wR = True

        if all(c is True for c in (wUL, wL, wDL, wUR, wR, wDR)):
            #print('Black wins')
            self.winner = self.black
            return

        bq_x, bq_y, bq_z = self.board.get('bq')
        bUL = bL = bDL = bUR = bR = bDR = False
        for v in vals:
            if v[0] == bq_x - 1:
                if v[1] == bq_y + 1:
                    bUL = True
                elif v[1] == bq_y - 1:
                    bDL = True
            elif v[0] == bq_x - 2 and v[1] == bq_y:
                bL = True
            elif v[0] == bq_x + 1:
                if v[1] == bq_y + 1:
                    bUR = True
                elif v[1] == bq_y - 1:
                    bDR = True
            elif v[0] == bq_x + 2 and v[1] == bq_y:
                bR = True

        if all(c is True for c in (bUL, bL, bDL, bUR, bR, bDR)):
            #print('White wins')
            self.winner = self.white
            return

        #print('Tie?')


def parse_game(f):
    game = Game()
    #typ

    for l in f.readlines():
        l = l.strip()

        if l.startswith('SU'):
            line_txt = gd(l)
            if 'hive' in line_txt:
                version = ''
                if 'l' in line_txt:
                    version += 'l'
                if 'm' in line_txt:
                    version += 'm'
                if 'p' in line_txt:
                    version += 'p'
            game.version = version

        elif l.startswith('DT'):
            line_txt = gd(l)
            date = dparse(line_txt)
            game.date = date

        elif l.startswith('P'):
            player = l[:2]
            line_txt = gd(l)

            if player[1] == '0':
                if line_txt.startswith('id'):
                    game.white.name = line_txt[4:-1]
                elif line_txt.startswith('ranking'):
                    game.white.rank = int(line_txt[8:])
                elif line_txt.startswith('time'):
                    game.white.time = line_txt[5:]
                #typ
            elif player[1] == '1':
                if line_txt.startswith('id'):
                    game.black.name = line_txt[4:-1]
                elif line_txt.startswith('ranking'):
                    game.black.rank = int(line_txt[8:])
                elif line_txt.startswith('time'):
                    game.black.time = line_txt[5:]
                #typ

        elif l.startswith('; P') and not any(s in l.lower() for s in ('start', 'done', 'pick')):
            actions = re_action.match(l)
            groups = actions.groups()
            if not groups or len(groups) != 5:
                sys.stdout.write(' ERROR reading move: {}\n'.format(l))
                sys.exit(1)

            action = Action()

            p_color_num = groups[0]
            if p_color_num == '0':
                action.player = 'w'
            elif p_color_num == '1':
                action.player = 'b'

            action.typ = groups[1].lower() if groups[1] is not None else None

            token_type = groups[3].lower() if groups[3] is not None else None
            if token_type:
                if action.typ == 'pdropb':
                    action.orig_token = token_type
                else:
                    color = groups[2].lower() if groups[2] is not None else action.player
                    action.orig_token = color + token_type

            target = groups[4].lower() if groups[4] is not None else None
            if target:
                if target.startswith('/'):
                    action.target_pos = 'ld'
                elif target.startswith('\\'):
                    action.target_pos = 'lu'
                elif target.startswith('-'):
                    action.target_pos = 'l-'
                elif target.endswith('/'):
                    action.target_pos = 'ru'
                elif target.endswith('\\'):
                    action.target_pos = 'rd'
                elif target.endswith('-'):
                    action.target_pos = 'r-'
                elif target == '.':
                    action.target_pos = '--'
                elif action.orig_token[1] == 'b':  # pill?
                    action.target_pos = 't-'

                for ch in ('/', '\\', '-'):
                    target = target.replace(ch, '')
                action.target_token = target

            if any(v is None for v in (action.player, action.typ, action.orig_token, action.target_token, action.target_pos)):
                sys.stdout.write(' ERROR assigning actions: {}\n'.format(l))
                sys.exit(1)

            game.moves.append(action)

    #print(game.typ)
    #print('Version: {}'.format(game.version if game.version else 'Reg'))
    #print('Date: {}'.format(game.date.isoformat()))
    #print('Players - White: {} ({}) --VS-- Black: {} ({})'.format(game.white.name, game.white.rank if game.white.rank else '-', game.black.name, game.black.rank if game.black.rank else '-'))

    game.parseMoves()

if __name__ == 'main':
    with open(filename, 'r') as f:
        parse_game(f)

