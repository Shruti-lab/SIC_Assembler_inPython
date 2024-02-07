'''
    System Programming Assignment Group Number : 6
    Group Members:
        Shruti Patil(21CSE1034) 
        Pooja Sonawane(21CSE1025)

            
    Group Topic: SIC ASSEMBLER
'''                                                                            

import sys
from OpTable import OPTAB 
# OPTAB - Opcode Table

# --------------------------- HELPER FUNCTIONS ----------------------------#

def TR_size(curtxt):
    '''
    It is the function returning size of the passed Text Record.
    curtxt - Current text record of the form -> "T^00ABCD^^00xxxx^00yyyy^"
    Hence length of text record = (len(cur) - (len("T") + len("00ABCD") + count("^")))//2
    (Length is divided by 2 because a 6 bit object code is of the size 3 bytes)
    '''
    return (len(curtxt)-7-curtxt.count("^"))//2

def init_current(curloc):
    '''
    Function to initialize the current Text Record starting from the current location (curloc)
    curloc - Current Location
    
    Text record is initialised as -> "T^00curloc^"
    '''
    return "T^00"+curloc+"^" 
    
def final_current(curtxt):
    '''
    Function to finalise the current Text Record by inserting its length and returns the final Text Record
    
    curtxt - current Text Record
    
    length -> Hex(TR_size(curtxt)) in 2 bits
    After Insertion, TE -> "T^00ABCD^xx^00yyyy^...."
    '''
    length = str(hex(TR_size(curtxt)))[2:].zfill(2).upper()
    return curtxt[:9] + length + curtxt[9:] + "\n" # newline to write in file

def update_loc(curloc, n, bytes):
    '''
    Function to update the current location value based on passed parameters and return the location value
    curloc - Current location value
    n - No. of words
    bytes - Size of each word
    
    Current location is converted back to int from hexadecimal form, size is added, then converted back to hexadecimal and returned
    '''
    size = int(n)*bytes
    return str(hex(int(curloc, 16) + size)[2:]).upper()

def add_to_forRef(frd, key, curloc):
    '''
    Function to append a Forward Reference to the forRef dictionary and return the dictionary
    frd- Forward Reference Dictionary
    key - Name of the Forward Reference
    curloc - current location corresponding to the Forward Reference
    
    if key is in frd, then curloc is appended to the existing list of the key, else create a new list with the passed key
    
    current loc stored in list will be 1 more than the curr loc passed (to make for the OPCODE)
    '''
    if key in frd:
        frd[key].append(str(hex(int(curloc,16)+1))[2:].upper())
    else:
        frd[key] = [str(hex(int(curloc,16)+1))[2:].upper()]
    
    return frd
 
def write_to_file(curtxt, f):
    '''
    Function to write a Text Record to file
    
    curtxt - Text Record
    f - File Pointer in write/write+ mode
    '''
    if TR_size(curtxt) > 0: # make sure to not write an empty or faulty Text Record
        f.write(final_current(curtxt)) 

if __name__ == "__main__": # main method
    
    if(len(sys.argv) < 2): # input and output filenames need to be mentioned as command line arguments
        print("Error!!! Enter input and output filenames as command line arguments.")
        exit() 
    
    elif(len(sys.argv) < 3):
        print("Error !!! Output filename not entered.")
        exit()
        
    file = open(sys.argv[1], 'r')
    data = file.readlines() # reads the input.txt and stores each line as list elements
 ##############       ###############
    loc = data[0].split()[-1].upper() # starting location is stored
    start  = loc
        
    labels = {} # dictionary for storing Labels
    forRef = {} # dictionary for storing Forward References
    current = "" # for current Text Record

    file = open(sys.argv[2], 'w+') # open a file in write+ mode

    for line in data: #line here is each line in assembler code as string
        words = line.split() # split each line of input into list of words (type=list)
        if(words[0] == '.'): 
            continue # comment in the input file, ignore line
        
        if len(words) > 1 and words[-2] not in ['RESW', 'RESB'] and current == "": 
            # if Operand is not RESW or RESB, and text record is currently null, then initialize text record with the current location
            current = init_current(loc)
            
        if len(words) == 3: # line with a label
            
            if words[0] in forRef.keys(): # if a Forward Reference is caught
                write_to_file(current, file) # write the current text record, 
                for objc in forRef[words[0]]: # write all forwards references as Text Records to file
                    current = init_current(objc) + "02^" + loc
                    file.write(current + "\n")
                    
                del forRef[words[0]] # delete the Forward Reference from the dictionary
                current = init_current(loc) # initialize 

            labels[words[0]] = loc
        
        if len(words) == 1: # for RSUB command
            if TR_size(current) + 3 > 30: # size checking of text record
                write_to_file(current, file) 
                current = init_current(loc) 
                
            current += "^" + OPTAB[words[-1]] + '0000' # append to text record
            loc = update_loc(loc, 1, 3) # update location
            continue
        
        if words[-2] in ['START', 'END']: 
            # special text records for the two
            if words[-2] == 'START': #writing initial text record
                current = 'H^' + words[0][:6] # 6 bits for the name
                if(len(words[0])<6): 
                    current += (" ")*(6-len(words[0])) #if name is less than 6 characters, spaces are added
                current += ("^00" + loc)*2  # starting location 
                    
                file.write(current + "\n") # Header record written to file and current re-initialized
                current = "" 
            
            else:
                labels[words[-2]] = loc 
                write_to_file(current, file) # write current text record to file
                current = "E^00" + labels[words[-1]] + "\n" 
                file.write(current) # write the End record to file
        
        elif words[-2] in ["RESW", "RESB"]:
            # no object code for these words
            if current != "":
                write_to_file(current, file) # if a text record is there, write it and reset current
                current = ""
                
            if words[-2] == 'RESW': # update location accordingly
                loc = update_loc(loc, words[-1], 3) 
            else: 
                loc = update_loc(loc, words[-1], 1)
                    
        elif words[-2] == 'BYTE': 
            # constant Object codes
            if words[-1][0]=='C': # for a character byte
                if TR_size(current) + 3 > 30: # size checking
                    write_to_file(current, file)
                    current = init_current(loc)
                        
                current += "^" + (''.join([hex(ord(x))[2:] for x in words[-1][2:-1]]).upper() + "000000")[:6]    # generate Object code from the the ASCII equivalent of the character(s)       ord(x) gives the ASCII of a character
                loc = update_loc(loc, 1, 3)  
                
            else: # for a X byte
                if TR_size(current) + 1 > 30: # size checking
                    write_to_file(current, file)
                    current = init_current(loc)
                        
                current += "^" + words[-1][2:-1].upper() # byte data stored as Object Code to current Text Record
                loc = update_loc(loc, 1, 1) # loc updated accordingly
        
        else:
            # for all other Operands
            if TR_size(current) + 3 > 30: # size checking of text record
                write_to_file(current, file)            
                current = init_current(loc)
            
            if words[-2] == 'WORD': # for WORD memory storage
                current += "^" + str(hex(int(words[-1])))[2:].zfill(6)    
                # integer space converted to hexadecimal and stored in Object Code
            else:
                if ',' in words[-1]: # handling indexed Operators
                    if words[-1][:-2] in labels:
                        current += '^' + OPTAB[words[-2]] + hex(int(labels[words[-1][:-2]],16) | int("8000",16))[2:].zfill(4).upper() # flag the index bit
                    else: # Forward Reference 
                        forRef = add_to_forRef(forRef, words[-1][:-2], loc) # add to forRef table
                        current += "^" + OPTAB[words[-2]] + "8000" # mention the index in Object Code

                elif words[-1] in labels: # handling normal references
                    current += '^' + OPTAB[words[-2]] + hex(int(labels[words[-1]],16) & int("7FFF",16))[2:].zfill(4).upper() # use only 15 bits of the referenced curlocess as per SIC architecture
                    
                else:
                    forRef = add_to_forRef(forRef, words[-1], loc) # put Forward reference in forRef
                    current += "^" + OPTAB[words[-2]] + '0000' # add just the Opcode
                
            loc = update_loc(loc, 1, 3) # update loc 

    end = loc # ending location
    
    # write the length of the program in the Header Record
    file.seek(0)
    file.seek((file.readline()).rindex("^")+1) # putting pointer at location
    current = str(hex(int(end,16) - int(start,16)))[2:].upper().zfill(6) # format current with program length

    file.write(current)
    file.close() # write the length and close the file
