
//includes
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <time.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <termios.h>

//defines
#define BAUDRATE            9600
#define BUFFSIZE            8192
#define GRAVITY             1.0
#define PHIGH               10
#define PLOW                5
#define PI                  3.141592653589793238462643f
#define ACK                 "ACK"
#define ACK_TIMEOUT         5
#define COM_ADDR	        "socks/monkeys_socket"
#define UNIX_PATH_MAX       100

// A tile represents a pixel in the game world. It has a strength and a type
typedef struct Tile{
    int strength;
    char type;
} Tile;

//function prototypes
int  invert(int value);
void startGame(void);
int  waitForAck(void);
char get_pb_zxcvqr(void);
void pb1_hit_callback(void);
void pb2_hit_callback(void);
void pb3_hit_callback(void);
void pb4_hit_callback(void);
void getworld (int**world, unsigned char *World);
void updateShot(int row, int column, int del);
void colorTile(int row, int column, int strength);
void deleteTile(int row, int column);
void paaUpdate(int power, int angle);
void hint(int row, int column, int power, int angle);
void run_test_trajectory(int *world);
void fired(Tile *newWorld, int *world);
void findMonkey(int *branchLoc, Tile *newWorld);
void findHint(int row, int col, int *branchLoc, Tile *newWorld, int l, int r);
void propagateDamage(int row, int col, Tile *newWorld);
int pathToBranch(int row, int col, Tile *newWorld, int l, int r, int u, int d);

// Global variables for push buttons
char volatile power=PHIGH, angle=45, fire;
int connection_fd;

//main
int main() {
    START:    
    //variables
    unsigned char World[BUFFSIZE];

    //socket connection
    struct sockaddr_un address;
    int socket_fd;
    socklen_t address_length;
    pid_t child;

    socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd < 0){
        printf("socket() failed\n");
        return 1;
    }

    memset(&address, 0, sizeof(struct sockaddr_un));
    address.sun_family = AF_UNIX;
    snprintf(address.sun_path, UNIX_PATH_MAX, COM_ADDR);
    address_length = sizeof(address);
    connect(socket_fd, (struct sockaddr *) &address, address_length);
    connection_fd=socket_fd;

    struct timeval timeout;
    timeout.tv_sec = ACK_TIMEOUT;
    timeout.tv_usec = 0;
    setsockopt(connection_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
  
    /******** Project 2 *********/    
    //loop
    while(1) {
        //synchronize front end display  
        startGame();                            

        //receive World
        recv(connection_fd,World,BUFFSIZE,0); 
        sleep(1);
        fflush(stdout);    
        printf("received\n");
        
        //get world that will be used for your work
        int *world;
        getworld(&world, World);
        int size = sqrt(world[0]); // getting size of world
        
        // Creating (kinda) 2D array of structs to represent world. 
        Tile *newWorld = (Tile *) malloc(world[0] * sizeof(Tile));
        int r;
        for(r = 0; r <world[1]; r++){
			Tile insert;
			insert.type = world[r*4+4];
			insert.strength = world[r*4+5];
			newWorld[world[r*4+2] * size + world[r*4+3]] = insert;
		}
		
		// branchLoc[] will contain the coordinates of the hint (and a flag for recursion) 
		int branchLoc[3];
		// findMonkey finds the left-most monkey and the proper branch tile for a hint
		findMonkey(branchLoc, newWorld);
		
		// Calculating trajectory for hint below
		int A, Ymonk, keepGoing;
		double rad, vel;
		keepGoing = 2;
		vel = PHIGH;
		while(keepGoing){
			for(A = 90; A >= 0; A--){
				rad = A*PI/180.0;
				Ymonk = tan(rad)*branchLoc[1] - .5*(GRAVITY/(pow(vel, 2)))*pow((1/cos(rad)), 2)*pow(branchLoc[1], 2);
				if(Ymonk == branchLoc[0]){
					goto Hint;
				}
			}
			vel = PLOW;
			keepGoing--;
		}
		
		// Hint is outputted
		Hint:
		hint(branchLoc[0], branchLoc[1], vel, A);
		
		
		
		
        //clear the terminal
        fflush(stdout);
        rewind(stdout);
        printf("\033[2J\033[1;1H");
        printf("Angry Monkeys\n");
        printf("Push the buttons.\n");
        printf("Z - fire cannon\nX - decrease angle    C - increase angle\nV - toggle power\nR - reset    Q - quit\n");
    
        int i, num_cannon=10;
	    char pb;
        
        //get pb
        while(1){
            // the get_pb_zxcvqr() function returns the character of the next keyboard button pressed
            pb=get_pb_zxcvqr();
            // and then based on that character, you can do something useful!
            if(pb=='z'){
                    printf("Z was pressed: FIRE!!!\n");
                    pb4_hit_callback();
                    // fired() contains all the logic for the cannonball flying through the world
					fired(newWorld, world);
            } else if(pb=='x'){
                    printf("X was pressed: decreasing angle\n");
                    pb3_hit_callback(); 
                    if(power==PHIGH)
                            printf("Angle:%d PHIGH\n", angle);
                    else
                            printf("Angle:%d PLOW\n", angle);
                    
            } else if(pb=='c'){
                    printf("C was pressed: increasing angle\n");
                    pb2_hit_callback(); 
                    if(power==PHIGH)
                            printf("Angle:%d PHIGH\n", angle);
                    else
                            printf("Angle:%d PLOW\n", angle); 
            } else if(pb=='v'){
                    printf("V was pressed: toggling power\n");
                    pb1_hit_callback(); 
                    if(power==PHIGH)
                            printf("Angle:%d PHIGH\n", angle);
                    else
                            printf("Angle:%d PLOW\n", angle); 
            } else if(pb=='q'){
	            printf("EXIT\n");
                    free(world);
                    close(socket_fd);
		    exit(1);
            }  else if(pb=='r'){
                    printf("RESTART\n");
                    free(world);
                    close(socket_fd);
                    goto START;		    
            }  else {
	            printf("testing\n");
		    printf("string1: %s\nstring2: %s\n", "hello", "world");
		    printf("int: %d, int: %d\n", world[2], world[3]); 
                    printf("Shots left:%d\n", num_cannon);
                    if(power==PHIGH)
                            printf("Angle:%d PHIGH\n", angle);
                    else
                            printf("Angle:%d PLOW\n", angle);
            }
            paaUpdate(power, angle);
        }
        

        free(world);  
        close(socket_fd);
    }
    //end loop

}

void fired(Tile *newWorld, int *world){
	int X = 0;
	int Y = 0;
	int Yx = 0;
	int t = 0;
	double Vx = power * cos((double)angle*PI/180.0);
	double Vy = power * sin((double)angle*PI/180.0);
	int size = sqrt(world[0]);
	
	if(Vx >= 1){
		for(X = 0; X < size; X++){
			Yx = (Vy/Vx)*X - .5*GRAVITY*((X*X)/(Vx*Vx)); // Y in terms of X
			if(Yx < 0) break; // if Y goes below world, stop animating
			if(newWorld[Yx*40+X].strength > 0){
				if(newWorld[Yx*40+X].strength == 1){
					if(newWorld[Yx*40 + X].type == 77){
						// delete the monkey...
						deleteTile(Yx, X);
						newWorld[Yx*40 + X].strength = 0;
						newWorld[Yx*40 + X].type = 0;
					}else{
						// or propagate damage if a tile is destroyed.
						propagateDamage(Yx, X, newWorld);
					}
				}else{
					// otherwise, keep track of the tile's strength
					newWorld[Yx*40 + X].strength = newWorld[Yx*40 + X].strength - 1;
					colorTile(Yx, X, newWorld[Yx*40 + X].strength);
				}
				break;
			}
			usleep(30000);
			// gotta animate!
			updateShot(Yx, X, 1);
			
		}
	}
	// reposition ball for next shot
	updateShot(0,0,1);

}

void findMonkey(int *branchLoc, Tile *newWorld){
	int i, j;
	int down, left, right;
	for(j = 0; j < 40; j++){
		for(i = 0; i < 40; i++){
			// Going down columns to find the left-most monkey
			int curType = newWorld[i*40 + j].type;
			if(curType == 77){
				if(i == 0){
					branchLoc[0] = i;
					branchLoc[1] = j;
				}
				findHint(i, j, branchLoc, newWorld, 1, 1);
				
				// branchLoc may contain the tree tile connected to the branch w/monkey. Finding correct direction:
				int goTop = newWorld[(branchLoc[0]+1)*40 + branchLoc[1]].type;
				int goL = newWorld[(branchLoc[0])*40 + branchLoc[1]-1].type;
				int goR = newWorld[(branchLoc[0])*40 + branchLoc[1]+1].type;
				if(newWorld[branchLoc[0]*40 + branchLoc[1]].type == 84){
					if(goTop == 77 || goTop == 66) branchLoc[0] = branchLoc[0]+1;
					else if(goL == 66) branchLoc[1] = branchLoc[1]-1;
					else if(goR == 66) branchLoc[1] = branchLoc[1]+1;
				}
				return;
			}
		}
	}
}

void findHint(int row, int col, int *branchLoc, Tile *newWorld, int l, int r){
	// recursively checks for the critical branch tile with the monkey on it
	
	int down, left, right;
	if(newWorld[row*40 + col].type == 84){
		if(branchLoc[2] != 4){
			branchLoc[0] = row;
			branchLoc[1] = col;
			branchLoc[2] = 4;
		}
		return;
	}
	
	down = row-1 >= 0 ? newWorld[(row-1)*40 + col].type : 0;
	if(down > 0){
		printf("goin down %d, (%d, %d)\n", down, row-1, col);
		findHint(row-1, col, branchLoc, newWorld, 1, 1);
	}
	
	left = col-1 >= 0 ? newWorld[row*40 + (col-1)].type : 0;
	if(left > 0 && l > 0){
		printf("goin left %d, (%d, %d)\n", left, row, col-1);
		findHint(row, col-1, branchLoc, newWorld, 1, 0);
	}
	
	right = col+1 < 40 ? newWorld[row*40 + (col+1)].type : 0;
	if(right > 0 && r > 0) {
		printf("goin right %d, (%d, %d)\n", right, row, col+1);
		findHint(row, col+1, branchLoc, newWorld, 0, 1);
	}
	
} 

int pathToBranch(int row, int col, Tile *newWorld, int l, int r, int u, int d){
	// Recursively checks for a path to a tree trunk when propagating damage through branch tiles
	
	int down, left, right, up;
	int db, lb, rb, ub;
	
	if(newWorld[row*40 + col].type == 84) return 1;
	
	//Checking Bounds of world
	down = row-1 >= 0 ? newWorld[(row-1)*40 + col].type : 0;
	left = col-1 >= 0 ? newWorld[row*40 + (col-1)].type : 0;
	right = col+1 < 40 ? newWorld[row*40 + (col+1)].type : 0;
	up = row+1 < 40 ? newWorld[(row+1)*40 + (col)].type : 0;
	
	if(up > 0 && u > 0){
		printf("goin up %d, (%d, %d)\n", up, row+1, col);
		return pathToBranch(row+1, col, newWorld, 1, 1, 1, 0);
	}
	
	if(down > 0 && d > 0){
		printf("goin down %d, (%d, %d)\n", down, row-1, col);
		return pathToBranch(row-1, col, newWorld, 1, 1, 0, 1);
	}
	
	if(left > 0 && l > 0){
		printf("goin left %d, (%d, %d)\n", left, row, col-1);
		return pathToBranch(row, col-1, newWorld, 1, 0, 1, 1);
	}
	
	if(right > 0 && r > 0) {
		printf("goin right %d, (%d, %d)\n", right, row, col+1);
		return pathToBranch(row, col+1, newWorld, 0, 1, 1, 1);
	}
	
	return 0;

}

void propagateDamage(int row, int col, Tile *newWorld){
	// Recursively propagates damage checking for properly supported tiles
	
	int left, right, down, up;
	usleep(20000);
	deleteTile(row, col);
	newWorld[row*40 + col].strength = 0;
	newWorld[row*40 + col].type = 0;
	
	left = col-1 >= 0 ? newWorld[row*40 + (col-1)].type : 0;
	right = col+1 < 40 ? newWorld[row*40 + (col+1)].type : 0;
	down = row-1 >= 0 ? newWorld[(row-1)*40 + col].type : 0;
	up = row+1 < 40 ? newWorld[(row+1)*40 + col].type : 0;
	
	if(up == 77 || up == 84 || up == 66){
		propagateDamage(row+1, col, newWorld);
	}
	if(down == 66){
		if(pathToBranch(row-1, col, newWorld, 1,1,0,1) != 1){
			propagateDamage(row-1, col, newWorld);
		}
	}
	if(left == 66){
		if(pathToBranch(row, col-1, newWorld, 1,0,1,1) != 1){
		propagateDamage(row, col-1, newWorld);
		}
	}
	if(right == 66){
		if(pathToBranch(row, col+1, newWorld, 0,1,1,1) != 1){
		propagateDamage(row, col+1, newWorld);
		}
	}
}

//fcn to send update
void updateShot(int row, int column, int del){
    //temp variables
    char buffer[BUFFSIZE];
    
    //construct message
    sprintf(buffer, "%s-%d-%d-%d;", "update", row, column, del);

    //send message
    send(connection_fd, buffer, strlen(buffer),0);
    waitForAck();
}

//fcn to send color
void colorTile(int row, int column, int strength){
    //temp variables
    char buffer[BUFFSIZE];
    
    //construct message
    sprintf(buffer, "%s-%d-%d-%d;", "color", row, column, strength);

    //send message
    send(connection_fd, buffer, strlen(buffer),0);
    waitForAck();
}    
    
//fcn to send delete
void deleteTile(int row, int column){
    //temp variables
    char buffer[BUFFSIZE];
    
    //construct message
    sprintf(buffer, "%s-%d-%d;", "delete", row, column);

    //send message
    send(connection_fd, buffer, strlen(buffer),0);
    waitForAck();
} 

//fcn to send power and angle
void paaUpdate(int power, int angle){
    //temp variables
    char buffer[BUFFSIZE];
    
    //construct message
    sprintf(buffer, "%s-%d-%d;", "paa", power, angle);

    //send message
    send(connection_fd, buffer, strlen(buffer),0);
    waitForAck();
} 

//fcn to send hint
void hint(int row, int column, int power, int angle){
    //temp variables
    char buffer[BUFFSIZE];
    
    //construct message
    sprintf(buffer, "%s-%d-%d-%d-%d;", "hint", row, column, power, angle);

    //send message
    send(connection_fd, buffer, strlen(buffer),0);
    waitForAck();
}

//fcn to get acknowledgement from serial peripheral
int waitForAck(void) {
    //get acknowlegement
    char buffer[BUFFSIZE];
    double elapsed;
    time_t start;
    time_t now;
    time(&start);
    while(1) {
        memset(&buffer[0],0,strlen(buffer));  
	    recv(connection_fd,buffer,BUFFSIZE-1,0);
        if(strncmp(ACK, buffer, strlen(ACK)) == 0) {
            break;
        }
        memset(&buffer[0],0,strlen(buffer));     
        time(&now);
        elapsed = difftime(now, start);
        //printf("%.f, ", elapsed);
        fflush(stdout);
        if(elapsed >= ACK_TIMEOUT)
            return 1;
    }
    return 0;
}

//fcn to initialize the frontend display
void startGame(void) {
    //temp variables
    char buffer[BUFFSIZE];

    //construct message
    sprintf(buffer, "start");

    //send message
    send(connection_fd, buffer, strlen(buffer),0);

    //wait for acknowledgement
    waitForAck();
}

//function to perform bitwise inversion
int invert(int value) {
    if (value == 0) {
        return 1;
    } else {
        return 0;
    }
}

char get_pb_zxcvqr(void) {
    char buf = 0;
    struct termios old = {0};
    if (tcgetattr(0, &old) < 0)
            perror("tcsetattr()");
    old.c_lflag &= ~ICANON;
    old.c_lflag &= ~ECHO;
    old.c_cc[VMIN] = 1;
    old.c_cc[VTIME] = 0;
    if (tcsetattr(0, TCSANOW, &old) < 0)
            perror("tcsetattr ICANON");
    if (read(0, &buf, 1) < 0)
            perror ("read()");
    old.c_lflag |= ICANON;
    old.c_lflag |= ECHO;
    if (tcsetattr(0, TCSADRAIN, &old) < 0)
            perror ("tcsetattr ~ICANON");
    return (buf);
}


// Callback routine is interrupt activated by a debounced pb hit
void pb1_hit_callback (void) {
    if(power==PHIGH)
        power=PLOW;
    else 
        power=PHIGH;
}
void pb2_hit_callback (void) {
    if(angle<90)
        angle++;
    else if(angle>=90) 
        angle=0;
}
void pb3_hit_callback (void) {
    if(angle>0)
        angle--;
    else if(angle<=0)
        angle=90;
}
void pb4_hit_callback (void) {
    fire++;
}

//func. to get world
void getworld (int**world, unsigned char *World){
    int i;
    char temp[3];
    
    //allocate world
    *world = (int*)malloc(sizeof(int)*(((World[2]<<8)+World[3])*4+2));
    
    //get it
    (*world)[0]=(World[0]<<8)+World[1];
    (*world)[1]=(World[2]<<8)+World[3];
    for(i=0;i<((*world)[1]*4);i++){
        temp[0] = World[(2*i)+4];
        temp[1] = World[(2*i)+5];
        temp[2] = '\0';   
        sscanf(temp, "%d", &((*world)[i+2]));            
    }
}
