#!/usr/bin/python2

# Imports and constants
import sys
import os
import optparse
import cPickle
import zlib
import time

# The dictionary to check words against
DICT = cPickle.loads(zlib.decompress(open('dict', 'rb').read()))

# Valid prefixes to trim paths
PREFIXES = cPickle.loads(zlib.decompress(open('prefixes', 'rb').read()))

MIN_LEN = 3 # Minimum length of word to look for 
MAX_LEN = 12 # Maximum length of word to look for
DESC = True # Display results in descending order of length

# The graph used to create paths through the grid for
# creating words to score in the Scramble game
LETTERS_GRAPH = { 0  : [1, 4, 5]
                , 1  : [0, 2, 4, 5, 6]
                , 2  : [1, 3, 5, 6, 7]
                , 3  : [2, 6, 7]
                , 4  : [0, 1, 5, 8, 9]
                , 5  : [0, 1, 2, 4, 6, 8, 9, 10]
                , 6  : [1, 2, 3, 5, 7, 9, 10, 11]
                , 7  : [2, 3, 6, 10, 11]
                , 8  : [4, 5, 9, 12, 13]
                , 9  : [4, 5, 6, 8, 10, 12, 13, 14]
                , 10 : [5, 6, 7, 9, 11, 13, 14, 15]
                , 11 : [6, 7, 10, 14, 15]
                , 12 : [8, 9, 13]
                , 13 : [8, 9, 10, 12, 14]
                , 14 : [9, 10, 11, 13, 15]
                , 15 : [10, 11, 14]
                }

# Save each letter in the grid in a list
LETTERS = []

# Save a word->path mapping for possible pretty printing
WORD_TO_PATH = {}

#=================================================#
#                                                 #
#             FUNCTION DEFINITIONS                #
#                                                 #
#=================================================#
def find_all_paths(start, end, path=[]):
    """ Modified version of Guido's DFS.
    """
    path = path + [start]
    if start == end:
        return [path]
    if len(path) > MAX_LEN:
        return []
    paths = []
    for node in LETTERS_GRAPH[start]:
        # Check if the current path is worth exploring
        prefix = ''
        for i in path:
            prefix += LETTERS[i]
        prefix_len = len(prefix)
        if prefix_len > 1 and prefix not in PREFIXES:
            continue 

        # If so, find all paths from that tile
        if node not in path:
            newpaths = find_all_paths(node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def check_paths(paths):
    """ Check if a path is an actual word.
    """
    if paths == []: return paths

    words = []
    for path in paths:
        word = ''
        if len(path) < MIN_LEN: continue
        for i in path:
            word += LETTERS[i]
        if word in DICT:
            words.append(word)
            WORD_TO_PATH[word] = path
    return words

def solve_scramble():
    """ Solve the scramble puzzle based on the letters passed in and the round.
    """
    # Start to measure the time taken to find the words
    start = time.time()

    # Calculate the paths of words
    found_words = set() 
    for i in range(16):
        for j in range(16):
            if i == j: continue
            found_words.update(check_paths(find_all_paths(i, j))) 

    # Give a little indication of how long it took
    print('Took %.2f secs' % (time.time() - start))

    # Finally, print out the words 
    # in ascending order of length
    count = 1 # Used to only print three grids at a time
    clear()   # Clear the screen
    for word in sorted(list(found_words), key=len, reverse=DESC):
        print_grid(word)
        if count % 3 == 0:
            try:
                raw_input('\n'*6 + ':')
                clear()
            except KeyboardInterrupt:
                clear()
                sys.exit()
        count += 1

def clear():
    """ Clear the screen. """
    if os.name == 'posix':
        os.system('clear')
    else:
        os.system('CLS')

def print_grid(word):
    """ Print a grid representation of the word and its path.
    """
    path = WORD_TO_PATH[word]
    sorted_path = sorted(path) 

    at_idx = 0 # Tracks which tile is being written to
    
    for i in range(9): # Odd = |; Even = -+
        if i % 2 == 0:
            for j in range(4):
                if j == 0: sys.stdout.write('+')
                sys.stdout.write('-'*6+'+')
        else:
            for j in range(4): 
                if j == 0: sys.stdout.write('|')
                if sorted_path != [] and sorted_path[0] == at_idx:
                    sys.stdout.write('{:^6}'.format(str(path.index(sorted_path[0])+1)))
                    sorted_path.pop(0)
                else:
                    sys.stdout.write(' '*6)

                sys.stdout.write('|')
                at_idx += 1
        sys.stdout.write('\n')
    # Show the word down below
    print('{:^28}'.format(word))

def parse_cmd_line():
    """ Parse the command line arguments and call the solver if all is well.
    """
    global MIN_LEN, MAX_LEN, DESC
    # Create an OptionParser object
    parser = optparse.OptionParser()

    # Add options for parsing (-l is optional)
    parser.add_option('-l', '--letters', dest='letters', action='store', 
        help='The letters in the grid, as one string, from left to right and top to bottom.')
    parser.add_option('-m', '--min', dest='min', action='store', type='int',
        help='The minimum length of word to find (defaults to ' + str(MIN_LEN) + ').')
    parser.add_option('-x', '--max', dest='max', action='store', type='int',
        help='The maximum length of word to find (defaults to ' + str(MAX_LEN) + ').')
    parser.add_option('-a', '--asc', dest='asc', action='store_true',
        help='Display the results in ascending order by length (defaults to false).')

    # Do the parsing and then perform the necessary checks
    (opts, args) = parser.parse_args()

    # Check for mandatory arguments
    if opts.letters is None:
        if len(args) == 1:
            opts.letters = args[0]
        else:
            parser.print_help()
            sys.exit('[Error]: The letters in the grid are required.')

    # Check for correct input
    opts.letters = opts.letters.lower()
    if not opts.letters.isalpha():
        sys.exit('[Error]: Invalid characters in the letter argument')
    elif len(opts.letters) != 16 and len(opts.letters) != 17:
        sys.exit('[Error]: There must be 16 or 17 letters: you entered ' + \
                    str(len(opts.letters)))

    # Add the letters to the LETTERS list
    double = False # Used for Qu tiles with two letters
    let_len = len(opts.letters)
    for i, let in enumerate(opts.letters):
        if let_len == 17 and let == 'q':
            LETTERS.append(let)
            double = True
        elif double:
            LETTERS[i-1] += let
            double = False
        else:
            LETTERS.append(let) 

    # See if max and min were passed in
    if opts.min is not None:
        assert(opts.min > 0)
        if opts.min > 1:
            MIN_LEN = opts.min
    if opts.max is not None:
        assert(opts.max > 0)
        if opts.max > 16:
            MAX_LEN = opts.max

    # Check on the order of the results
    if opts.asc is not None:
        DESC = False

    # Finally, solve the puzzle
    solve_scramble()
#=================================================#
#                                                 #
#                 MAIN                            #
#                                                 #
#=================================================#
if __name__ == '__main__':
    parse_cmd_line()
