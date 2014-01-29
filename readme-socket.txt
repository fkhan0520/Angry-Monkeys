Building and Running the Socket-Based Version of Project 2

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

4. To run the demo, follow the same steps in step 3, but run
      ./demo32
or    ./demo64
depending on whether you have a 32-bit or 64-bit system.

(This demonstrates part of the game animation.  It is incomplete.
For example, it does not propagate changes caused by hitting and
destroying a branch tile to the connected tiles/monkey above.)

If you get a "Permission denied" error, please set the permission
to allow the file to be executed as a program, using the command:
    chmod a+x demo32     or
    chmod a+x demo64

