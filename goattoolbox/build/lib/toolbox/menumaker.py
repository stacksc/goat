import os, sys
if os.name != 'nt':
    try:
       import curses
    except:
        pass
from math import *
from tabulate import tabulate

os.environ['NCURSES_NO_UTF8_ACS'] = '1'

class Menu():

    def __init__(self, options, title, joiner, subtitle):
        self.ATTRIBUTES = {}
        self.OPTIONS = options
        self.TITLE = title
        self.JOINER = joiner # this specifies how to join your strings; i.e. '\t\t'
        self.SUBTITLE = subtitle
        
    def _setup_menu(self, stdscr):

        rows, columns = os.popen('stty size', 'r').read().split()
        screen = curses.initscr()
        screen.clrtoeol()
        screen.erase()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        screen.keypad( 1 )
        highlightText = curses.color_pair( 1 )
        normalText = curses.A_NORMAL
        screen.border(0)
        height, width = stdscr.getmaxyx()

        # title information
        title = self.TITLE
        author = "author: GOAT Team"
        subtitle = self.SUBTITLE
      
        max_row = 15 # max number of rows
        box = curses.newwin( max_row + 2, int(columns) - 2, 2, 1 )
        box.box()

        # decorate the titles and enable color
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.curs_set(0)
        stdscr.addstr(1, 1, title, curses.color_pair(4))
        stdscr.addstr(1, width - len(author) - 2, author, curses.color_pair(4))
        stdscr.addstr(1, int(columns) // 2 - len(subtitle) // 2, subtitle, curses.color_pair(4))

        x = 0
        cursor_x = 0
        cursor_y = 0

        strings = self.OPTIONS
        joinit = self.JOINER
        if not joinit:
            joinit = '\t'
        row_num = len( strings )
        pages = int( ceil( row_num / max_row ) )
        position = 1
        page = 1

        for i in range( 1, max_row + 1 ):
            if row_num == 0:
                box.addstr( 1, 1, "THESE AREN'T STRINGS - PRESS 'Q' TO QUIT", highlightText )
            else:
                size = len(strings[ i - 1]) + 5
                space = " " * size
                if (i == position):
                    box.addstr( i, 2, str( i ) + " - " + f'{joinit}'.join(strings[ i - 1 ]), highlightText)
                else:
                    box.addstr( i, 2, str( i ) + " - " + f'{joinit}'.join(strings[ i - 1 ]), normalText)
                if i == row_num:
                    break

        # Render status bar with subtitle
        statusbarstr = 'PRESS "q" TO QUIT'
        stdscr.attron(curses.color_pair(3))
        height = int(height) - 1
        stdscr.addstr(height-1, 1, statusbarstr)
        stdscr.attroff(curses.color_pair(3))

        screen.refresh()
        box.refresh()
        x = screen.getch()

        while x != 27 and x != ord('q'):
            screen.refresh()
            box.refresh()
            height, width = stdscr.getmaxyx()
            if x == curses.KEY_DOWN:
                cursor_y = cursor_y + 1
                if page == 1:
                    if position < i:
                        position = position + 1
                    else:
                        if pages > 1:
                            page = page + 1
                            position = 1 + ( max_row * ( page - 1 ) )
                elif page == pages:
                    if position < row_num:
                        position = position + 1
                else:
                    if position < max_row + ( max_row * ( page - 1 ) ):
                        position = position + 1
                    else:
                        page = page + 1
                        position = 1 + ( max_row * ( page - 1 ) )
            if x == curses.KEY_UP:
                cursor_y = cursor_y - 1
                if page == 1:
                    if position > 1:
                        position = position - 1
                else:
                    if position > ( 1 + ( max_row * ( page - 1 ) ) ):
                        position = position - 1
                    else:
                        page = page - 1
                        position = max_row + ( max_row * ( page - 1 ) )
            if x == curses.KEY_LEFT or x == curses.KEY_PPAGE:
                cursor_x = cursor_x - 1
                if page > 1:
                    page = page - 1
                    position = 1 + ( max_row * ( page - 1 ) )

            if x == curses.KEY_RIGHT or x == curses.KEY_NPAGE:
                cursor_x = cursor_x + 1
                if page < pages:
                    page = page + 1
                    position = ( 1 + ( max_row * ( page - 1 ) ) )
            if x == ord( "\n" ) and row_num != 0:
                screen.erase()
                return strings[ position - 1]

            box.erase()
            screen.border( 0 )
            box.border( 0 )
        
            for i in range( 1 + ( max_row * ( page - 1 ) ), max_row + 1 + ( max_row * ( page - 1 ) ) ):
                if row_num == 0:
                    box.addstr( 1, 1, "data must be strings",  highlightText )
                else:
                    if ( i + ( max_row * ( page - 1 ) ) == position + ( max_row * ( page - 1 ) ) ):
                        box.addstr( i - ( max_row * ( page - 1 ) ), 2, str( i ) + " - " + f'{joinit}'.join(strings[ i - 1 ]), highlightText )
                    else:
                        box.addstr( i - ( max_row * ( page - 1 ) ), 2, str( i ) + " - " + f'{joinit}'.join(strings[ i - 1 ]), normalText )
                    if i == row_num:
                        break

            # put the title back on refresh
            stdscr.addstr(1, 1, title, curses.color_pair(4))
            stdscr.addstr(2, 1, author, curses.color_pair(4))

            # Render status bar
            statusbarstr = 'PRESS "q" TO QUIT'
            stdscr.attron(curses.color_pair(3))
            height = int(height) - 1
            stdscr.addstr(height-1, 1, statusbarstr)
            stdscr.attroff(curses.color_pair(3))

            # Refresh the screen
            screen.refresh()
            box.refresh()
            x = screen.getch()

    def display(self):
        CHOICE = curses.wrapper(self._setup_menu)
        if CHOICE == "ERROR_DISPLAY":
            print("Oops, your window is too small to display the menu. Please maximize your terminal/client app and try again")
            sys.exit()
        curses.endwin()
        return CHOICE
