Angry-Monkeys
=============

A remake of the popular mobile game on Python/C++ made for an ECE 2035 project.

Setup: 

1. You'll need to get the library used for the socket communications:
sudo apt-get install happycoders-libsocket
sudo apt-get install happycoders-libsocket-dev
sudo cp /usr/lib/happycoders/* /usr/lib/

You do not need to worry about this message:
"cp: cannot stat `/usr/lib/happycoders/*.so.0.*': No such file or directory"

2. To compile the .cpp files and link the socket library:
g++ -lnsl -lsocket main.cpp -o main

You may need to install g++ (C++ compiler):
sudo apt-get install g++

3. To run the game:
a) be sure that the C executable (main) is in the same directory as P2_main.py
b) Open two terminal sessions and change to the directorty that contains
   the executable and P2_main.py in each terminal.
c) In one terminal, run
         python P2_main.py
   This will pop up the GUI and run the front-end process that will
   listen for communication from the back-end process.
d) In the other terminal, run the main executable:
         ./main
   This will establish a link with the front-end and it will clear the
   terminal screen, summarize the keystroke commands, and wait for the
   user to hit a keystroke which it then responds to (using code that
   you will write).

Gameplay:

Z - Fire
X/C - Aim
V - Toggle shot power
