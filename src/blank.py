#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2019

@author: colin

'''
from fileinput import filename

__author__ = "Colin Bitterfield"
__copyright__ = "Copyright 2019, " + __author__
__credits__ = ["Colin Bitterfield"]
__license__ = "GPL3"
__version__ = "0.1.0"
__maintainer__ = "Colin Bitterfield"
__status__ = "Alpha"

def md5(*args):
    '''
    Generate an MD5 for an image
    takes 1 argument filename
    returns md5
    '''
    pass


def vid_info(*args):
    pass


def img_info(*args):
    pass





def main():
    pass



if __name__ == "__main__":
    main()
    
    
    
    
    
### Build an argparsing function ###
### Function requires variables and gets script name from the operating system

def getArgs(argv=None):
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.prog =os.path.basename(__file__)
    parser.description = "This is where the command-line utility's description goes."
    parser.epilog = "This is where the command-line utility's epilog goes."
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    
    parser.add_argument('[-SHORT_FLAG]','[--LONG_FLAG]',
                        help = '[Help Message]',
                        action='store', # or use store_true/false
                        type = str, # or use int, filename
                        required=False, # or set to true
                        dest='xls_filename', # variable to be stored
                        choices=['rock', 'paper', 'scissors'], # Set valid choices
                        default='[DEFAULT]' # Set a default value 
                        ) 
    
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
                        required=False,
                        dest='outputfile',
                        default = None
                        )
    
    parser.add_argument('-if','--inputfile',
                        help='Filename for input', #Customize messages as needed
                        action='store',
                        type = str,
                        required=False,
                        dest='inputfile',
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
    
    parser.add_argument('-if','--inputfile',
                        help='Directory for Input', #Customize messages as needed
                        action='store',
                        type = str,
                        required=False,
                        dest='inputdir',
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
                        type = bool,
                        required=False,
                        dest='dryrun',
                        default = False
                        )       
    parse_out = parser.parse_args()
    return parse_out