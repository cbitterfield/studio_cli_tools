#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
deploy_files -- shortdesc

deploy_files is a description

It defines classes_and_methods

@author:     colin


@copyright:  2019 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

__author__ = "Colin Bitterfield"
__copyright__ = "Copyright 2019, " + __author__
__credits__ = ["Colin Bitterfield"]
__license__ = "GPL3"
__version__ = "0.1.0"
__maintainer__ = "Colin Bitterfield"
__status__ = "Alpha"
__created___ = "10/19/2019"
__updated___ = ""


DEBUG=1
LOG_LEVEL="INFO"
# When Dryrun = True, no write or change action will occur
DRYRUN=0

# Import Libraries
# Required
import sys
import os
import time
import shutil
import argparse
#Optional
from filehash import FileHash
md5hasher = FileHash('md5')
import xlsxwriter
# Global Variables


# Define System Variables
console_size = shutil.get_terminal_size((80, 20))[0]
runtime = epoch_time = int(time.time())

if DEBUG: console_size = 132

### Additiona Functions 




### System Required Functions 
def setup(configuration):
    global MEDIA_EXTENSIONS, PIL_EXTENSIONS
    global console_size
    global runtime
    global DEBUG
    global LOG_LEVEL
    global DRYRUN
    
    
    if DEBUG: print('Console Size = {}'.format(console_size))
    



def getListOfFiles(dirName):
    '''
    This function returns a list of all files recursively in the passed argument
    '''
    if not dirName:
        return None
    else:
        # create a list of file and sub directories 
        # names in the given directory 
        listOfFile = os.listdir(dirName)
        allFiles = list()
        # Iterate over all the entries
        for entry in listOfFile:
            # Create full path
            fullPath = os.path.join(dirName, entry)
            # If entry is a directory then get the list of files in this directory 
            if os.path.isdir(fullPath):
                allFiles = allFiles + getListOfFiles(fullPath)
            else:
                allFiles.append(fullPath)
                
    return allFiles

def getArgs(argv=None):
    '''
    Function for parsing common argumengts
    returns parsed arguments
    '''
    
    parser = argparse.ArgumentParser()
    parser.prog =os.path.basename(__file__)
    parser.description = "This is where the command-line utility's description goes."
    parser.epilog = "This is where the command-line utility's epilog goes."
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    
#     parser.add_argument('[-SHORT_FLAG]','[--LONG_FLAG]',
#                         help = '[Help Message]',
#                         action='store', # or use store_true/false
#                         type = str, # or use int, filename
#                         required=False, # or set to true
#                         dest='xls_filename', # variable to be stored
#                         choices=['rock', 'paper', 'scissors'], # Set valid choices
#                         default='[DEFAULT]' # Set a default value 
#                         ) 
    
    parser.add_argument('-d','--debug',
                        help='Turn on debugging, and set log level',
                        action='store',
                        type = str,
                        required=False,
                        dest='LOG',
                        choices=['none', 'alert', 'crit','err','warning','info','debug'],
                        default = 'none'
                        )
    
    parser.add_argument('-of','--outputfile',
                        help='Filename for output', #Customize messages as needed
                        action='store',
                        type = str,
                        required=True,
                        dest='outputfile',
                        default = None
                        )
    
    parser.add_argument('-id2','--inputdir2',
                        help='Filename for input', #Customize messages as needed
                        action='store',
                        type = str,
                        required=True,
                        dest='inputdir2',
                        default = None
                        )
    
    parser.add_argument('-od','--outputdir',
                        help='Directory for output', #Customize messages as needed
                        action='store',
                        type = str,
                        required=False,
                        dest='outputdir',
                        default = None
                        )
    
    parser.add_argument('-id1','--inputdir1',
                        help='Directory for Input', #Customize messages as needed
                        action='store',
                        type = str,
                        required=True,
                        dest='inputdir1',
                        default = None
                        )    
    
    parser.add_argument('-f','--format',
                        help='Directory for Input', #Customize messages as needed
                        action='store',
                        type = str,
                        required=False,
                        choices=['text', 'csv', 'xls','json'],
                        dest='outputformat',
                        default = None
                        ) 
    
    parser.add_argument('-dr','--dryrun',
                        help='Display what would be done. Create no objects, Modify no objects, Delete no objects', #Customize messages as needed
                        action='store_true',
                        required=False,
                        dest='dryrun',
                        default = False
                        )       
    parse_out = parser.parse_args()
    return parse_out
    
def main():
    CONFIG = getArgs(None)   
    setup(CONFIG)
    
    if CONFIG.LOG != None: print('ARGS: {}'.format(CONFIG))
    
    if CONFIG.LOG == 'DEBUG':
        DEBUG=1
    
    # initializations
    hashed_dir1 = {}
    hashed_dir2 = {}
    merged_dir = {}
    
    # Create a DICT of Directory 1 with MD5 hashes as the key
    
    
    print('Start Hashing the files directory 1')
    for fileToHash in getListOfFiles(CONFIG.inputdir1):
        
        if os.path.isfile(fileToHash) and not os.path.basename(fileToHash).startswith('.'):
            file_hash = md5hasher.hash_file(fileToHash)
            print('{hash} => {filename}'.format(hash=file_hash,filename=fileToHash))
            hashed_dir1[file_hash] = fileToHash
        
    numFileDir1 = len(hashed_dir1.keys())    
    print('Number of files in directory 1 [{}]'.
          format(numFileDir1)
          )
    
    print('Start Hashing the files directory 2')
    for fileToHash in getListOfFiles(CONFIG.inputdir2):
        if os.path.isfile(fileToHash) and not os.path.basename(fileToHash).startswith('.'):
            file_hash = md5hasher.hash_file(fileToHash)
            print('{hash} => {filename}'.format(hash=file_hash,filename=fileToHash))
            hashed_dir2[file_hash] = fileToHash
        
    numFileDir2 = len(hashed_dir2.keys())    
    print('Number of files in directory 2 [{}]'.
          format(numFileDir2)
          )

    # Merge the directories
    merged_dir.update(hashed_dir1)
    merged_dir.update(hashed_dir2)
    
    num_unique_files = len(merged_dir.keys())
    print('The number of unique files is '.format(num_unique_files))
    
    # Create a spreadsheet for analysis

    workbook = xlsxwriter.Workbook(CONFIG.outputfile)
    # Define a row heading format
    row_heading_format = workbook.add_format({'bold': True, 'font_color': 'blue'})
    row_even_format =  workbook.add_format({'font_color': 'black'})
    row_odd_format =  workbook.add_format({'font_color': 'black'})
    worksheet = workbook.add_worksheet('dir comparison')
    worksheet_header = ['path','filename','md5','dir1','dir2','full_path_name','delete_me']
    worksheet.write_row(0, 0, worksheet_header, row_heading_format)
    row = 1
    col = 0
    worksheet_row = ['path','filename','md5','dir1','dir2','full_path_name','delete_me']
    for unique_file in merged_dir.keys():
        
        worksheet_row[5] = merged_dir[unique_file]
        worksheet_row[0] = os.path.dirname(worksheet_row[5])
        worksheet_row[1] = os.path.basename(unique_file)
        worksheet_row[2] = unique_file
        
        if unique_file in hashed_dir1.keys():
            worksheet_row[3] = "X"
        else:
            worksheet_row[3] = ""
        if unique_file in hashed_dir2.keys():
            worksheet_row[4] = "X"
        else:
            worksheet_row[4]= ""
        if row % 2 == 0:
            worksheet.write_row(row, col, worksheet_row, row_even_format)
        else:
            worksheet.write_row(row, col, worksheet_row, row_odd_format)
        print('Row {}'.format(worksheet_row))
        row = row + 1
        
        if 
    
    workbook.close()    
                
    print('End of Program')
    return


if __name__ == "__main__":
    main()