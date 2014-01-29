#! /usr/bin/env python

'''
Created on Oct 3, 2013

@author: Clark Kerr
'''

# imports
import Tkinter
import SOCKETcom
import threading
import Queue
import random
import time
import struct
from math import floor
import math

# Auto-hiding Scrollbar
class autoScrollBar(Tkinter.Scrollbar):
    def saveOptions(self):
        self.options = self.grid_info()

    def set(self, *args):
        Tkinter.Scrollbar.set(self, *args)
        if (float(args[0]) <= 0.0 and float(args[1]) >= 1.0):
            self.grid_forget()
        else:
            self.grid(self.options)
            
# game world
class World(object):
    def __init__(self):
        self.spArray = list()
        self.nsArray = list()
        self.Rows = 0
        self.Cols = 0
        self.Size = 0
        self.nonZeros = 0
        self.g = 1
        self.P = [5,15]
        
    def fromCSV(self, fname):
        f = open(fname)
        
        self.spArray = list()
        self.Marray = list()
        
        try:
            row = -1
            for line in f:
                col = -1
                while len(line):
                    (val, sep, line) = line.partition(',')
                    (_type, sep, strength) = val.partition('-')
                    if _type == "M":
                        self.spArray.append([row, col, _type, int(strength)])
                        self.Marray.append([row,col,_type,int(strength)])
                    if _type == "B":
                        self.spArray.append([row, col, _type, int(strength)])    
                    if _type == "T":
                        self.spArray.append([row, col, _type, int(strength)])
                    col += 1
                row += 1
            self.Rows = row
            self.Cols = col
            self.Size = row * col
            self.nonZeros = len(self.spArray)
            
            self.nsArray = [[('', 0) for j in range(self.Cols)] for i in range(self.Rows)]
            for (row, col, _type, stren) in self.spArray:
                self.nsArray[row][col] = [_type, stren]
        except:
            f.close()
    
    def sendWorld(self, conn):
        # 1. Pack the size of the world, number of occupied squares, and the sparse array representation
        # into a byte string.
        
        # initialize buffer
        worldBuffer = ''
        # pack total size of the game world (rows*columns) and append to the buffer
        temp = struct.pack('>h', self.Size)
        print self.Size
        worldBuffer += temp
        print repr(temp)
        # pack number of occupied squares and append to the buffer
        temp = struct.pack('>h', self.nonZeros)
        print self.nonZeros
        worldBuffer += temp
        print repr(temp)
        # pack each tuple from the sparse array and append to the buffer
        for (row, col, _type, stren) in self.spArray:
            temp = "%.2d%.2d%.2d%.2d" % (row, col, ord(_type), stren)    
            # temp = struct.pack('>hhxch', row, col, _type, stren)
            worldBuffer += temp
            #print repr(temp)
            #print (row, col, _type, stren)
        # 2. send the byte string in one shot to the mbed
        try:
            count = conn.sendData(worldBuffer)
            print count
        except:
            print "sendWorld unsuccessful"  
    
# hint object
class hint(object):
    def __init__(self):
        self.box = None
        self.Ltext = ""
        self.Etext = ""
        self.label = None
        self.Llabel = None
        self.Slabel = None
        self.loc_correct = True
        self.shot_correct = True

# gui
class GUI(Tkinter.Tk):
    # constructor
    def __init__(self):
        # initialize app
        Tkinter.Tk.__init__(self)

        # comm (serial) parameters
        self.buffSize = 8192
        # self.BAUD = 9600
        self.comaddr = "socks/monkeys_socket"
        self.comSocket = SOCKETcom.ComSocket(self.buffSize, self.comaddr)
        self.commDelimiter = '-'
        self.messageDelimiter = ';'
        self.ACK = 'ACK'
        self.pending = Queue.Queue()
        self.conn = None

        # garbage collection
        self.protocol('WM_DELETE_WINDOW', self._windowClose)
        
        # load world
        self.worldnumber = random.choice([0,1,2,3,4])
        self.worldfname = "World%d.csv"%(self.worldnumber+1)
        self.world = World()
        self.world.fromCSV(self.worldfname)
        self.worldObjects = None
        self.cannonball = list()
        self.shotline = None
        self.hints = list()
        self.leftmonkeys = [[13,23],[11,28],[10,21],[1,21],[10,25]]
        self.leftjoints = [[8,27],[3,36],[7,24],[0,21],[9,25]]

        # ui parameters/variables
        self.minCanvasWidth = 200
        self.minCanvasHeight = 200
        self.boxCount = self.world.Rows
        self.gridPad = 3
        
        # graphics parameters
        # monkey colors
        self.Mcolors = {1: "#4D4DFF", 2: "#0000E3", 3: "#6200E3", 4: "#C100E3", 5: "#E300AA"}
        # trunk colors
        self.Tcolors = {1: "#FFA200", 2: "#C98F2A", 3: "#996633", 4: "#785519", 5: "#3E1F00"}
        # branch colors
        self.Bcolors = {1: "#FCF768", 2: "#E0DA1F", 3: "#B0AB0E", 4: "#7DB00E", 5: "#369C06"}
        # color table
        self.colors = {'M': self.Mcolors, 'T': self.Tcolors, 'B': self.Bcolors, 'Cball': 'black'}
            # self.monkeyColor = 'blue'
            # self.treeColor = 'brown'
            # self.branchColor = 'yellow'
            # self.cannonballColor = 'black'

        # set up window
        self._initWindow()
        self._initConsole()

        # draw screen
        self.update_idletasks()
        self._redrawLabels()
        self._redrawGrid()
        self._redrawWorld()
        self.update_idletasks()
        # establish connection
        self.ComSocketNotify()
        
         
        # test some drawing functions
        # intiate animation thread
        # self.releaseDrawThread()

    # fcn to properly close main window
    def _windowClose(self):
        self.comSocket.closeConn()
        self.destroy()

    # fcn to initialize main window
    def _initWindow(self):
        # configure main window
        self.title('ECE2035 - Angry Monkeys')
        self.config(bg='grey', highlightbackground='grey', highlightthickness=0)
        self.resizable(0, 0)

        # configure left panel
        self.leftPanel = Tkinter.Canvas(self, width=40, height=600)
        self.leftPanel.config(bg='grey', highlightthickness=0, highlightbackground='grey', highlightcolor='grey')

        # configure top panel
        self.topPanel = Tkinter.Canvas(self, width=600, height=40)
        self.topPanel.config(bg='grey', highlightthickness=0, highlightbackground='grey', highlightcolor='grey')

        # configure canvas
        self.canvas = Tkinter.Canvas(self, width=600, height=600)
        self.canvas.config(bg='grey', highlightthickness=0, highlightbackground='grey', highlightcolor='grey', bd=5, relief='sunken')
        
        # configure hint panel
        self.hintFrame = Tkinter.Frame(self, width=250, height=600)
        self.hintFrame.config(bg='grey', highlightthickness=0, highlightbackground='grey', highlightcolor='grey')
        
        # construct row/col labels
        self.colHeaders = range(0, self.boxCount)
        self.rowHeaders = range(0, self.boxCount)
        self.rowHeaders.reverse()

        # construct serial text entry
        self.textboxString = Tkinter.StringVar()
        self.textbox = Tkinter.Label(self.canvas, textvariable=self.textboxString, fg='black', highlightthickness=0)

        # construct console button
        self.image = Tkinter.PhotoImage(file='console_temp.gif')
        self.consoleButton = Tkinter.Button(self, image=self.image, relief='raised', bd=2, bg='grey', highlightthickness=0, highlightcolor='grey', highlightbackground='grey', command=self.openConsole)

        # place configured widgets
        self.leftPanel.grid(row=1, column=0, rowspan=1, sticky='nsew')
        self.topPanel.grid(row=0, column=1, sticky='ew')
        self.canvas.grid(row=1, column=1, sticky='nsew')
        self.hintFrame.grid(row=1, column=2, sticky='nsew')
        self.consoleButton.grid(row=0, column=0)

    # fcn to initialize console/terminal
    def _initConsole(self):
        # construct console window
        self.consoleWindow = Tkinter.Toplevel(bg='black')
        self.consoleWindow.title("Terminal")
        self.consoleWindow.withdraw()
        self.consoleWindow.resizable(1, 1)
        self.consoleWindow.grid_columnconfigure(0, weight=1)
        self.consoleWindow.grid_rowconfigure(0, weight=1)

        # construct console
        self.console = Tkinter.Text(self.consoleWindow, bg='black', fg='green', bd=0, highlightthickness=0, highlightcolor='black', height=30, width=90)
        self.console.grid(row=0, column=0, sticky='nsew')

        # construct console's scroll bars
        self.xScroll = autoScrollBar(self.consoleWindow, bg='black', highlightbackground='black', highlightcolor='black', orient='horizontal', command=self.console.xview)
        self.yScroll = autoScrollBar(self.consoleWindow, bg='black', highlightbackground='black', highlightcolor='black', orient='vertical', command=self.console.yview)
        self.console.config(xscrollcommand=self.xScroll.set, yscrollcommand=self.yScroll.set)
        self.xScroll.grid(row=1, column=0, sticky='ew')
        self.yScroll.grid(row=0, column=1, sticky='ns')
        self.xScroll.saveOptions()
        self.yScroll.saveOptions()

        # garbage collection
        self.consoleWindow.protocol('WM_DELETE_WINDOW', self._consoleClose)

    # fcn to properly close the console
    def _consoleClose(self):
        self.consoleButton.config(command=self.openConsole)
        self.consoleWindow.destroy()

    # fcn to redraw gameboard (grid)
    def _redrawGrid(self):
        # draw boxes
        self.canvasWidth = self.canvas.winfo_width()
        self.canvasHeight = self.canvas.winfo_height()
        self.boxSize_x = self.canvasWidth / self.boxCount
        self.boxSize_y = self.canvasHeight / self.boxCount
        self.canvas.delete('all')
        self.gridList = [[] for i in range(self.boxCount)]
        for i in range(self.boxCount):
            for j in range(self.boxCount):
                box_id = self.canvas.create_rectangle(self.gridPad + i * self.boxSize_x, self.gridPad + j * self.boxSize_y, self.gridPad + (i + 1) * self.boxSize_x, self.gridPad + (j + 1) * self.boxSize_y)
                self.gridList[j].append(box_id)

    # fcn to redraw gameboard (labels)
    def _redrawLabels(self):
        # draw column labels
        self.topPanelWidth = self.topPanel.winfo_width()
        self.topPanelHeight = self.topPanel.winfo_height()
        size_x = self.topPanelWidth / self.boxCount
        self.topPanel.delete('all')
        for (i, item) in zip(range(self.boxCount), self.colHeaders):
            self.topPanel.create_text((i + .5) * size_x, self.topPanelHeight / 2, text=item)

        # draw row labels
        self.leftPanelWidth = self.leftPanel.winfo_width()
        self.leftPanelHeight = self.leftPanel.winfo_height()
        size_y = self.leftPanelHeight / self.boxCount
        self.leftPanel.delete('all')
        for (i, item) in zip(range(self.boxCount), self.rowHeaders):
            self.leftPanel.create_text(self.leftPanelWidth / 2, (i + .5) * size_y, text=str(item))
            
    # fcn to redraw World
    def _redrawWorld(self):
        # clear old world
        if self.worldObjects:
            for row in self.worldObjects:
                for element in row:
                    if element:
                        self.canvas.delete(element)
        # clear old shotline
        self.shotline = None
        # clear old ball
        self.cannonball = list()
        # draw new world          
        self.worldObjects = [[None for j in range(self.world.Cols)] for i in range(self.world.Rows)]
        for (j, i, _type, stren) in self.world.spArray:
            if _type == 'M':
                box_id = self.canvas.create_bitmap(self.gridPad + i*self.boxSize_x, self.gridPad + (self.world.Rows-j-1)*self.boxSize_y, bitmap='@monkey.xbm', foreground=self.colors[_type][stren], anchor=Tkinter.NW)
            else:
                box_id = self.canvas.create_rectangle(self.gridPad + i*self.boxSize_x, self.gridPad + (self.world.Rows-j-1)*self.boxSize_y, self.gridPad + (i+1)*self.boxSize_x, self.gridPad + (self.world.Rows-j)*self.boxSize_y, fill=self.colors[_type][stren])
            self.worldObjects[j][i] = box_id

        # clear old hint panel
        self.hintFrame.destroy()
        self.hints = list()
        
        # create new hint frame
        
        self.hintFrame = Tkinter.Frame(self, width=250, height=600)
        self.hintFrame.config(bg='grey', highlightthickness=0, highlightbackground='grey', highlightcolor='grey')
        self.hintFrame.grid(row=1, column=2, sticky='nsew')

        # redraw hint panel

        size_y = self.hintFrame.winfo_height() / self.boxCount
        self.hintTitle = Tkinter.Label(self.hintFrame, text="  Hint:                        ", font=('Arial',16,'underline'), bg='grey')
        self.hintTitleL = Tkinter.Label(self.hintFrame, text="L:", font=('Arial',16,'underline'), bg='grey')
        self.hintTitleS = Tkinter.Label(self.hintFrame, text="S:", font=('Arial',16,'underline'), bg='grey')
        self.hintTitle.grid(row=0, column=0)
        self.hintTitleL.grid(row=0, column=1)
        self.hintTitleS.grid(row=0, column=2)
        
    # fcn to draw user hints
    def _drawHint(self, h_index):
        item = self.hints[h_index]          
        self.hints[h_index].label = Tkinter.Label(self.hintFrame, text=item.Ltext, anchor=Tkinter.W, bg='grey')
        self.hints[h_index].label.grid(row=h_index+1, column=0)
        if item.loc_correct == 'M':
            self.hints[h_index].Llabel = Tkinter.Label(self.hintFrame, bitmap='@monkey.xbm', foreground='blue', background='grey').grid(row=h_index+1, column=1)
        elif item.loc_correct == 'J':
            self.hints[h_index].Llabel = Tkinter.Label(self.hintFrame, text='B', foreground='brown', background='grey').grid(row=h_index+1, column=1)
        else:
            self.hints[h_index].Llabel = Tkinter.Label(self.hintFrame, bitmap='@x.xbm', foreground='red', background='grey').grid(row=h_index+1, column=1)
        if item.shot_correct:
            self.hints[h_index].Slabel = Tkinter.Label(self.hintFrame, bitmap='@check.xbm', foreground='green', background='grey').grid(row=h_index+1, column=2)
        else:
            self.hints[h_index].Slabel = Tkinter.Label(self.hintFrame, bitmap='@x.xbm', foreground='red', background='grey').grid(row=h_index+1, column=2)

            
    # fcn to delete a drawing at a given row, column
    def _dbox(self, row, col):
        box_id = self.worldObjects[row][col]
        if box_id:
            self.canvas.delete(box_id)
            
    # fcn to animate shots        
    def _ushot(self, row, col, delete):
        # if there is no cannonball, or if we aren't deleting, draw a new cannonball
        if not (self.cannonball and delete):
            new = self.canvas.create_oval(self.gridPad + col*self.boxSize_x, self.gridPad + (self.world.Rows - row - 1)*self.boxSize_y, self.gridPad + (col+1)*self.boxSize_x, self.gridPad + (self.world.Rows - row)*self.boxSize_y, fill=self.colors['Cball'])
            self.cannonball.append(new)
        # else, delete the previous cannonballs and move the last cannonball
        elif delete:
            for ball in self.cannonball[:-1]:
                self.canvas.delete(ball)
            self.cannonball = self.cannonball[-1:]
            self.canvas.coords(self.cannonball[0], self.gridPad + col*self.boxSize_x, self.gridPad + (self.world.Rows - row - 1)*self.boxSize_y, self.gridPad + (col+1)*self.boxSize_x, self.gridPad + (self.world.Rows - row)*self.boxSize_y) 
   
    # fcn to change tile color and tile strength
    def _ctile(self, row, col, stren):
            # update tile strength in local array
        element = self.world.nsArray[row][col]
        _type = element[0]
        self.world.nsArray[row][col][1] = stren
        # change color of corresponding canvas object, using the color table, tile type, and new strength value
        if self.worldObjects[row][col]:
            if self.world.nsArray[row][col][0] == 'M':
                self.canvas.itemconfig(self.worldObjects[row][col], foreground=self.colors[_type][stren])
            else:             
                self.canvas.itemconfig(self.worldObjects[row][col], fill=self.colors[_type][stren])
        
    # fcn to test the accuracy of hints sent by mbed
    def _hcheck(self, power, angle, row, col):
        newHint = hint()
        newHint.Ltext = "Row: %2d, Col: %2d, Pow: %2d, Ang: %2d"%(row, col, power, angle)
        if [row,col] == self.leftmonkeys[self.worldnumber]:
            newHint.loc_correct = 'M'
            newHint.Etext += " Targeted the left-most monkey!"
        elif [row,col] == self.leftjoints[self.worldnumber]:
            newHint.loc_correct = 'J'
            newHint.Etext += " Targeted the left-most joint!"
        else:
            newHint.loc_correct = False
            newHint.Etext = " Bad target!"
        newHint.box = self._highlight(row,col)
        x = col
        theta = angle * math.pi / 180
        y = x*math.tan(theta) - self.world.g * 0.5 * (x**2) / (power**2) / ((math.cos(theta))**2)
        if floor(y) != row:
            newHint.shot_correct = False
            newHint.Etext += " Shot Incorrect."
        else:
            newHint.Etext += " Shot Correct!"
        self.hints.append(newHint)
        print newHint.Ltext+newHint.Etext
        self._drawHint(len(self.hints) - 1)
        
    # fcn to highlight a specified tile   
    def _highlight(self, row, col):
        box_id = self.canvas.create_rectangle(self.gridPad + col*self.boxSize_x, self.gridPad + (self.world.Rows-row-1)*self.boxSize_y, self.gridPad + (col+1)*self.boxSize_x, self.gridPad + (self.world.Rows-row)*self.boxSize_y, outline = 'red', width=2)
        return box_id
    
    # fcn to draw shot power/angle graphic    
    def _pupdate(self, power, angle):
        #calculate x,y components given power and angle
        x = math.sqrt(power)*math.cos(angle*(math.pi/180))*2
        y = math.sqrt(power)*math.sin(angle*(math.pi/180))*2
        #update old shotline or create new line
        if self.shotline:
            self.canvas.coords(self.shotline, self.gridPad, self.gridPad + (self.world.Rows)*self.boxSize_y, self.gridPad + x*self.boxSize_x, self.gridPad + (self.world.Rows - y)*self.boxSize_y)
        else:
            self.shotline = self.canvas.create_line(self.gridPad,self.gridPad + (self.world.Rows)*self.boxSize_y,self.gridPad + x*self.boxSize_x,self.gridPad + (self.world.Rows - y)*self.boxSize_y,arrow=Tkinter.LAST,fill='red')
   
    # fcn to calculate hints iteratively
    def _hintIter(self, monkey):
        angle = 45
        dir = 0
        dA = 1
        pow = self.world.P[1]
        x_m = monkey[1]
        y_m = monkey[0]
        
        y = x_m*math.tan(angle*(math.pi/180)) - (self.world.g/2) * (x_m/(pow * math.cos(angle*(math.pi/180))))**2
        if floor(y) < y_m:
            return "Not in range"
        while(floor(y) != y_m and angle >= 0 and angle <= 90):
            if floor(y) < y_m:
                if dir == -1:
                    dA = dA/2
                angle += dA
                theta = angle * (math.pi / 180)
                y = x_m*math.tan(theta) - self.world.g * 0.5 * (x_m**2) / (pow**2) / ((math.cos(theta))**2)
                dir = 1
            else:
                if dir == 1:
                    dA = dA/2
                angle -= dA
                theta = angle * (math.pi / 180)
                y = x_m*math.tan(theta) - self.world.g * 0.5 * (x_m**2) / (pow**2) / ((math.cos(theta))**2)
                dir = -1                
        if floor(y) == y_m:
            return angle
        else:
            return "Angle not found"
        
    # fcn to set up animation thread
    def releaseDrawThread(self):
        # set refresh rate
        self.dt = 0.1
        self.drawThread = threading.Thread(name='process_draw', target=self.processDrawing)
        self.drawThread.daemon = True
        self.drawThread.start()
        self.releaseComThread()
        
     
    # fcn target of the animation thread    
    def processDrawing(self):
#         self._drawTester(self.dt)
#         row = self.leftmonkeys[self.worldnumber][0]
#         col = self.leftmonkeys[self.worldnumber][1]
#         self._hcheck(15, 34, row, col)
#         row = self.leftjoints[self.worldnumber][0]
#         col = self.leftjoints[self.worldnumber][1]
#         self._hcheck(15, 34, row, col)
#         self._hcheck(15, 34, 25, 25)
#         for monkey in self.world.Marray:
#             angle = self._hintIter(monkey)
#             if isinstance(angle, (int, float)):
#                 self._hcheck(15,angle,monkey[0],monkey[1])

        while(True):    
            try:
#                 (command, row, col) = self.pending.get()
#                 if command == self.UPDATE:
#                     self._ushot(row, col)
#                 elif command == self.DELETE:
#                     self._dbox(row, col)
#                 self.update_idletasks()
                time.sleep(self.dt)
            except:
                pass
                          
    #fcn to test drawing
    def _drawTester(self, dt):  
        #test box delete 
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[0]
        self.update_idletasks()
        self._dbox(r,c)
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[4]
        self.update_idletasks()
        self._dbox(r,c)
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[23]
        self.update_idletasks()
        self._dbox(r,c)
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[2]
        self.update_idletasks()
        self._dbox(r,c)
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[12]
        self.update_idletasks()
        self._dbox(r,c)
        time.sleep(dt)
        (r,c,t,s) = self.world.spArray[6]
        self.update_idletasks()
        self._dbox(r,c)
        #test cannon ball redraw
        for i in range(50):
            time.sleep(dt)
            (r,c) = (floor(6*i*dt-.5*(i*dt)**2), floor(5*i*dt))
            bln = not i%12
            self._ushot(r,c,bln)
            self._pupdate(15, (float(i)/49)*45)
            self.update_idletasks()
            print (float(i)/49)*45
                
        
    # fcn to allow user to enter serial port address
    def ComSocketNotify(self):
        self.textbox.config(fg='black')
        self.connect()
        self.textboxString.set('Communication socket listening for clients...\n Start your game engine.')
        # self.textbox.bind("<Button-1>", self._formatTextbox)
        self.textbox.place(relx=0.5, rely=0.5, anchor='center')

    # fcn to reconfigure the textbox upon click
    def _formatTextbox(self, eventData):
        self.textboxString.set("")
        self.textbox.config(fg='black')
        self.textbox.unbind("<Button-1>")
        self.textbox.bind("<Return>", self.getConnectionInfo)

    # fcn to gather serial address
    def getConnectionInfo(self, eventData):
        self.textbox.unbind("<Button-1>")
        self.textbox.place_forget()
        self.SERIALPORTNAME = self.textboxString.get()
        print self.SERIALPORTNAME
        self.connect()

    # fcn to establish connection using specified comm type
    def connect(self):
        try:
            self.connectThread = threading.Thread(name='find_conn', target=self.comSocket.reconnect)
            self.connectThread.daemon = True
            self.connectThread.start()
            self.conn = self.comSocket
            self.releaseComThread()
        except:
            self.ComSocketNotify()

    # fcn to release comm thread
    def releaseComThread(self):
        self.options = {'bomb':self.bomb, 'print':self.printConsole, 'start':self.startNewGame, 'delete': self.deleteBox, 'update': self.updateShot, 'color': self.colorTile, 'hint': self.hintCheck, 'paa': self.paaUpdate}
        self.commThread = threading.Thread(name='process_comm', target=self.processCommPort)
        self.commThread.daemon = True
        self.commThread.start()

    # fcn to process the communication port
    def processCommPort(self):
    # wait for socket to connect

        t0 = time.time()
        while self.connectThread.isAlive():
            time.sleep(0.1)
            t1 = time.time() - t0
            self.textboxString.set('Communication socket listening for clients...\n Start your game engine.\n %d seconds elapsed...'%t1)

        for i in range(2):
            self.textboxString.set('Communication socket established! Game starts in : %d'%(2-i))
            time.sleep(1)    
        
        self.textbox.place_forget()
    
        # loop to recieve messages
        while True:
    
            # try:
            #    item = (self.UPDATE, random.randint(0,self.world.Rows), random.randint(0,self.world.Cols))
            #    self.pending.put(item)
            #    time.sleep(self.dt)
            # except:
            #    pass

            try:
                data = self.conn.receiveData()
                messages = data.split(self.messageDelimiter)
                if messages[0]:
                    print messages

            except: 
                continue
         
            try:
                for msg in messages:
                    formatData = msg.split(self.commDelimiter)
                    if formatData[0]:
                        print formatData
                        self.options[formatData[0]](formatData)
            except:
                pass

            try:
                self.conn.client.send('')
            except IOError as e:
                if e[0] == 32:
                    self.textboxString.set('Connection lost, attempting to reconnect...')
                    self.textbox.place(relx=0.5, rely=0.5, anchor='center')
                    time.sleep(1)
                    self.ComSocketNotify()
                    break
              
    # wrappers to be called by comm thread and parse messages for the updater functions:
           
    def deleteBox(self, message):
        if len(message) == 3:
            try:
                row = int(message[1])
                col = int(message[2])
                self._dbox(row, col)
            except:
                print "deleteBox failed"
        self.conn.sendData(self.ACK)
                
    def updateShot(self, message):
        if len(message) == 4:
            try:
                row = int(message[1])
                col = int(message[2])
                d = bool(int(message[3]))
                self._ushot(row, col, d)
            except:
                print "updateShot failed"
        self.conn.sendData(self.ACK)
                
    def colorTile(self, message):
        try:
            if len(message) == 4:
                row = int(message[1])
                col = int(message[2])
                stren = int(message[3])
                self._ctile(row, col, stren)
        except:
            print "colorTile failed"
        self.conn.sendData(self.ACK)
                
    def hintCheck(self, message):
        if len(message) == 5:
            try:
                power = int(message[3])
                angle = int(message[4])
                row = int(message[1])
                col = int(message[2])
                self._hcheck(power, angle, row, col)
            except:
                print "hintCheck failed"
        self.conn.sendData(self.ACK)
                
    def paaUpdate(self, message):
        if len(message) == 3:
            try:
                power = int(message[1])
                angle = int(message[2])
                self._pupdate(power, angle)
            except:
                print "paaUpdate failed"
        self.conn.sendData(self.ACK)
                
    # fcn to bomb a given coordinate
    def bomb(self, message):
        if (len(message) == 3) and (ord(message[1]) in range(ord('0'), ord(':'))) and (ord(message[2]) in range(ord('0'), ord(':'))):
            self.numBombsUsed += 1
            row_idx = ord(message[1]) - ord('0')
            col_idx = ord(message[2]) - ord('0')
            hit = self._isInShipList(row_idx, col_idx)
            if hit:
                self.canvas.itemconfig(self.gridList[row_idx][col_idx], fill=self.hitColor)
                hit.status = 'inactive'
                if self.shipList[hit.shipListIdx].isSunk():
                    self.conn.sendData('status-sank')
                    print self.allShipsSunk()
                else:
                    self.conn.sendData('status-hit')
            else:
                self.conn.sendData('status-miss')
        else:
            self.conn.sendData('status-err')

    # fcn to print to console
    def printConsole(self, message):
        try:
            self.console.insert('end', '>>' + message[1] + '\n')
        except:
            pass
        self.conn.sendData(self.ACK)

    # fcn to set up the gameboard
    def startNewGame(self, message):
        print "starting new game"
        self._redrawGrid()
        self._redrawWorld()
        self.update_idletasks()
        self.conn.sendData(self.ACK)
        self.world.sendWorld(self.conn)
        self.conn.sendData(self.ACK)

    # fcn to open console/terminal on button click
    def openConsole(self):
        try:
            self.consoleWindow.update()
            self.consoleWindow.deiconify()
        except:
            # re-create console window
            self._initConsole()
            self.consoleWindow.update()
            self.consoleWindow.deiconify()
        # configure button
        self.consoleButton.config(command=self.closeConsole)

    # fcn to close the console/terminal on button click
    def closeConsole(self):
        try:
            self.consoleWindow.withdraw()
        except:
            pass
        # configure button
        self.consoleButton.config(command=self.openConsole)

    # fcn to restrict a string's length
    def stringCap(self, string, length):
        if len(string) <= length:
            return string
        else:
            return string[0:length]

# main loop
if __name__ == "__main__":
    app = GUI()
    app.mainloop()
