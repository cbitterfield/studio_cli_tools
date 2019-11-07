#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
AWS Template to create command line programs for reporting
Created on Oct 12, 2019
@author: colin_bitterfield
'''
### Library Imports  

# Required

import os
import sys
import shutil
import argparse
import time
from datetime import datetime
import ffmpeg
import re

import xlsxwriter
import textdistance
import warnings

# Import file processing libraries
from queue import Empty
from multiprocessing import Pool, Queue, Process

import PIL
from PIL import Image as ImageP
from wand.image import Image as ImageW
import PyPDF2
from subprocess import Popen, PIPE
from requests_toolbelt.downloadutils import stream

# Program Description Variables
__author__ = "Colin Bitterfield"
__copyright__ = "Copyright 2019, " + __author__
__credits__ = ["Colin Bitterfield"]
__license__ = "GPL3"
__version__ = "0.1.0"
__maintainer__ = "colin_bitterfield"
__status__ = "Alpha"
__created___ = "10/19/2019"
__updated___ = ""
__prog_name__ = os.path.basename(__file__)
__console_size_ = shutil.get_terminal_size((80, 20))[0]
__timestamp__ = time.time() 
__run_datetime__ = datetime.fromtimestamp(__timestamp__) # Today's Date



#Test and Debugging Variables
DEBUG=False
LOGLEVEL='info'
# When Dryrun = True, no write or change action will occur
DRYRUN=False
VERBOSE=False
PROBLEM=False

UPDATE_SEC_INTERVAL = 5  # sec
UPDATE_GB_INTERVAL = 1  # minimum MBytes of data between output log/messages

# Media extensions to check
PIL_EXTENSIONS = ['jpg', 'jpeg', 'jpe', 'png', 'bmp', 'gif', 'pcd', 'tif', 'tiff', 'j2k', 'j2p', 'j2x', 'webp']
VIDEO_EXTENSIONS = ['avi', 'mp4', 'mov', 'mpeg', 'mpg', 'm2p', 'mkv', '3gp', 'ogg', 'flv', 'f4v', 'f4p', 'f4a', 'f4b']
MAGICK_EXTENSIONS = ['psd', 'xcf']
PDF_EXTENSIONS = ['pdf']
MEDIA_EXTENSIONS = []

VIDEO_FIELDS=['codec_name',
             'codec_long_name',
             'codec_type',
             'width',
             'height',
             'coded_width',
             'coded_height',
             'display_aspect_ratio',
             'avg_frame_rate',
             'bit_rate'
             ]

AUDIO_FIELDS=['codec_name',
             'codec_long_name',
             'codec_type',
             'sample_rate',
             'channels',
             'avg_frame_rate',
             'bit_rate',
             'max_bit_rate',
             ]

VIDEO_RUNTIME = None
VIDEO_CREATION = None
VIDEO_MD5 = None
OUTPUT_ROW = []
OUTPUT_ROW_HEADER = {}
OUTPUT_ROW_WIDTHS = {}
OUTPUT_ROW_HEADER['Videos'] = ['filename','duration','md5'] 
OUTPUT_ROW_HEADER['Videos'] += VIDEO_FIELDS
OUTPUT_ROW_HEADER['Videos'] += AUDIO_FIELDS
OUTPUT_ROW_HEADER['Videos'] += ['full_filename','comments']


OUTPUT_ROW_HEADER['PhotoSets'] =['header']
OUTPUT_ROW_HEADER['2257'] =['header']

OUTPUT_ROW_WIDTHS['Videos']= {}
for element in OUTPUT_ROW_HEADER['Videos']:
    element_length = len(element) + 4
    OUTPUT_ROW_WIDTHS['Videos'].update( { element : element_length })

OUTPUT_ROW_WIDTHS['PhotoSets']= {}
OUTPUT_ROW_WIDTHS['2257']= {}

PROBLEM=False

PREFIX = "HXHX"
EDGEID = ""
CONFIG = None



## System Functions
def bestMatch(**kwargs):
    #parameters
    # value, list
    bestmatch=""
    matchvalue = float(0)
    match_threshold = .5
    
    for testvalue in kwargs['list']:
        # Remove extensions in files and 2257 text when special
        # Remove any extensions on value
        source = os.path.splitext(kwargs['value'])[0].upper()
        destination = os.path.splitext(testvalue)[0].upper()
        
        # Now remove any reference to 2257s
        source = source.replace('_2257','')
        source = source.replace('2257','')
        
        destination = destination.replace('_2257','')
        destination = destination.replace('2257','')
        
        padvalue = max([len(source),len(destination)])
        source = source.rjust(padvalue)
        destination = destination.rjust(padvalue)
        
        # We need to remove extensions from both values just in case and make sure everything is one case.
            
        distance = textdistance.hamming.normalized_similarity(source, destination)
        if distance > matchvalue:
            matchvalue = distance
            bestmatch = testvalue
            
    if matchvalue <= match_threshold:
        bestmatch = ""
        matchvalue = 0
        
    matchvalue = float("{0:.4f}".format(matchvalue)) 
    # Return the best match from the list
  
    return bestmatch,matchvalue

import re
def assignID(**kwargs):
    '''
    Take string and assign a edge id to based on method
    Arguememts current_id='', method='', row=''. prefix=''
    
    methods available are:
    num_right_side = "Take all of the numbers starting with the first number in the id and add them to a prefix
        IDID0001 = EDGEID0001
        Takes a minimum of three digits. If no block of numbers is found return None and assignment will occur during final evaluation
        
    Always pad for a minimum of 8 characters
    
    '''
    # add in better fuction layout on next version
    current_id = kwargs['current_id']
    method = kwargs['method']
    row = kwargs['row']
    prefix = kwargs['prefix']
    padsize = 4
    SUCCESS = True
    EDGEID=""
    
    match = r1 = re.findall(r"\d{3,}",current_id)
    if len(match) > 1:
        SUCCESS = False
        EDGEID = None
        raise Exception('Error {0}'.format(str(match)))
    
    elif len(match) == 0:
        EDGEID = None
    
    else:
        EDGEID = kwargs['prefix'] + match[0].rjust(padsize, '0')
        
    return SUCCESS,EDGEID

## Imported Functions

def pil_check(filename):
    img = ImageP.open(filename)  # open the image file
    img.verify()  # verify that it is a good image, without decoding it.. quite fast
    img.close()

    # Image manipulation is mandatory to detect few defects
    img = ImageP.open(filename)  # open the image file
    # alternative (removed) version, decode/recode:
    # f = cStringIO.StringIO()
    # f = io.BytesIO()
    # img.save(f, "BMP")
    # f.close()
    img.transpose(PIL.Image.FLIP_LEFT_RIGHT)
    img.close()

def magick_check(filename, flip=True):
    # very useful for xcf, psd and aslo supports pdf
    img = ImageW(filename=filename)
    if flip:
        temp = img.flip
    else:
        temp = img.make_blob(format='bmp')
    img.close()
    return temp

def magick_identify_check(filename):
    proc = Popen(['identify', '-regard-warnings', filename], stdout=PIPE,
                 stderr=PIPE)  # '-verbose',
    out, err = proc.communicate()
    exitcode = proc.returncode
    if exitcode != 0:
        raise Exception('Identify error:' + str(exitcode))
    return out

def wandIdentifyCheck(filename):
    '''
    Using the wand library open the image from filename and read basic parameters and return as a dict
    '''
    import logging
    logger = logging.getLogger("wandIdentifyCheck:")
    image_info = {}
    try:
        with ImageW(filename=filename) as image:
            image_info = {
                'filename' : filename,
                'basename' : os.path.basename(filename),
                'width' : image.width,
                'height' : image.height,
                'resolution' : image.resolution,
                'format' : image.format
            }
            
            
            image_info.update(**image.metadata)
            logger.debug('File {0} metadata {1}'.format(filename,image_info))
            logger.debug('File {0} metadata keys {1}'.format(filename,image_info.keys()))
            
     
    except Exception as e:
            logger.error("{0} Error {1} ".format(__name__,e))
            return False, filename, e


def pypdf_check(filename):
    # PDF format
    # Check with specific library
    pdfobj = PyPDF2.PdfFileReader(open(filename, "rb"))
    pdfobj.getDocumentInfo()
    # Check with imagemagick
    magick_check(filename, False)
    
def check_zeros(filename, length_seq_threshold=None):
    f = open(filename, "rb")
    thefilearray = f.read()
    f.close()
    num = 1
    maxnum = num
    prev = None
    maxprev = None
    for i in thefilearray:
        if prev == i:
            num += 1
        else:
            if num > maxnum:
                maxnum = num
                maxprev = prev
            num = 1
            prev = i
    if num > maxnum:
        maxnum = num
    if length_seq_threshold is None:
        return maxnum
    else:
        if maxnum >= length_seq_threshold:
            raise Exception("Equal value sequence, value:", maxprev, "len:", maxnum)

def check_size(filename, zero_exception=True):
    statfile = os.stat(filename)
    filesize = statfile.st_size
    if filesize == 0 and zero_exception:
        raise SyntaxError("Zero size file")
    return filesize


def get_extension(filename):
    file_lowercase = filename.lower()
    return os.path.splitext(file_lowercase)[1][1:]


def is_target_file(filename):
    import logging
    logger = logging.getLogger("is_target_file")
    logger.debug('Testing filename {0} against media list'.format(filename))
    file_ext = get_extension(filename)
    if file_ext in MEDIA_EXTENSIONS:
        STATUS=True
        logger.debug('Testing filename {0} against media list {1}'.format(filename,'match'))
    else:
        STATUS=False
        logger.debug('Testing filename {0} against media list {1}'.format(filename,"Doesn't match"))
    return STATUS


def ffmpeg_check(filename, error_detect='default', threads=0):
    if error_detect == 'default':
        stream = ffmpeg.input(filename)
    else:
        if error_detect == 'strict':
            custom = '+crccheck+bitstream+buffer+explode'
        else:
            custom = error_detect
        stream = ffmpeg.input(filename, **{'err_detect': custom, 'threads': threads})

    stream = stream.output('pipe:', format="null")
    stream.run(capture_stdout=True, capture_stderr=True)
    
def ffmpeg_info(filename):
    '''
    Takes a filename in
    provides a dict response for info parameters specific
    
    '''
    info = {}
    import logging
    logger = logging.getLogger("ffmpeg_info")
    #print('Filename {}'.format(filename))
    arguments = {'sexagesimal' : None, 'show_entries' : "stream=codec_name,bit_rate,channels,sample_rate,height,width,codec_type,codec_long_name,display_aspect_ratio,coded_width,coded_height,avg_frame_rate,bit_rate,max_bit_rate : stream_disposition= : format=duration : format_tags=creation_time " }
    try:
        info = dict(ffmpeg.probe(filename,**arguments))
    
    except Exception as e:
        logger.error("{0} Error as {1}".format(__name__,e))
        return False, filename, e
    
    return True, (info)

class TimedLogger:
    def __init__(self):
        self.previous_time = 0
        self.previous_size = 0
        self.start_time = 0

    def start(self):
        self.start_time = self.previous_time = time.time()
        return self

    def print_log(self, num_files, num_bad_files, total_file_size, wait_min_processed=UPDATE_GB_INTERVAL, force=False):
        import logging
        logger = logging.getLogger("print_log")

        if not force and (total_file_size - self.previous_size) < wait_min_processed * (1024 * 1024):
            return
        cur_time = time.time()
        from_previous_delta = cur_time - self.previous_time
        if from_previous_delta > UPDATE_SEC_INTERVAL or force:
            self.previous_time = cur_time
            self.previous_size = total_file_size

            from_start_delta = cur_time - self.start_time
            speed_MB = total_file_size / (1024 * 1024 * from_start_delta)
            speed_IS = num_files / from_start_delta
            processed_size_GB = float(total_file_size) / (1024 * 1024 * 1024)

            logger.critical("Number of bad/processed files: {0} / {1} , size of processed files: {2:,.3f} GB".format(num_bad_files,num_files,round(processed_size_GB,3)) )
            logger.critical("Processing speed: {0:,.2f} MB/s, or {1:,.2f} files/s".format(round(speed_MB,2),round(speed_IS,2)))

def is_pil_simd():
    return 'post' in PIL.PILLOW_VERSION


def check_file(filename, error_detect='default', strict_level=0, zero_detect=0, ffmpeg_threads=0):
    if sys.version_info[0] < 3:
        filename = filename.decode('utf8')

    file_lowercase = filename.lower()
    file_ext = os.path.splitext(file_lowercase)[1][1:]

    file_size = 'NA'

    try:
        file_size = check_size(filename)
        if zero_detect > 0:
            check_zeros(filename, CONFIG.zero_detect)

        if file_ext in PIL_EXTENSIONS:
            if strict_level in [1, 2]:
                pil_check(filename)
            if strict_level in [0, 2]:
                magick_identify_check(filename)

        if file_ext in PDF_EXTENSIONS:
            if strict_level in [1, 2]:
                pypdf_check(filename)
            if strict_level in [0, 2]:
                magick_identify_check(filename)

        if file_ext in MAGICK_EXTENSIONS:
            if strict_level in [1, 2]:
                magick_check(filename)
            if strict_level in [0, 2]:
                magick_identify_check(filename)

        if file_ext in VIDEO_EXTENSIONS:
            ffmpeg_check(filename, error_detect=error_detect, threads=ffmpeg_threads)

    # except ffmpeg.Error as e:
    #     # print e.stderr
    #     return False, (filename, str(e), file_size)
    except Exception as e:
        # IMHO "Exception" is NOT too broad, io/decode/any problem should be (with details) an image problem
        return False, (filename, str(e), file_size)

    return True, (filename, None, file_size)

def check_file_b(filename, error_detect='default', strict_level=0, zero_detect=0, ffmpeg_threads=10):
    '''
    Returns:
    
    SUCCESS, filename, None, file_size, info(DICT) [This will be different for each media type]
    '''
    import logging
    logger = logging.getLogger('check_file_b:')
    info = {}
    if sys.version_info[0] < 3:
        filename = filename.decode('utf8')
        
    file_lowercase = filename.lower()
    file_ext = os.path.splitext(file_lowercase)[1][1:]

    file_size = 'NA'    
    try:
        file_size = check_size(filename)
        
    
        if file_ext in VIDEO_EXTENSIONS:
            logger.debug('Checking video information for file {}'.format(filename))    
            #ffmpeg_check(filename, error_detect=error_detect, threads=ffmpeg_threads)
            info = ffmpeg_info(filename)[1]
            
            info.update({'md5' : '5fcd5be293148e56c12afe3d73269e88'})
                
        if file_ext in PIL_EXTENSIONS:
            logger.critical('Checking image information for file {}'.format(filename))    
            info = wandIdentifyCheck(filename)
            info.update({'md5' : '5fcd5be293148e56c12afe3d73269e88'})
            
                
    except Exception as e:
        # IMHO "Exception" is NOT too broad, io/decode/any problem should be (with details) an image problem
        logger.error('{name} Filename {0}, Error{1}, FileSize {2}'.format(filename, str(e), file_size,name=__name__))
        return False, (filename, str(e), file_size)
    
    return True, (filename, None , file_size, info)


def log_check_outcome(check_outcome_detail):
    import logging
    logger = logging.getLogger('log_check_outcome:')
    
    logger.error("Bad file: {0} , error detail: {1} , size[bytes]: {2}".format(check_outcome_detail[0],check_outcome_detail[
        1],check_outcome_detail[2]))


def worker(in_queue, out_queue):

    try:    
        while True:
            full_filename = in_queue.get(block=True, timeout=2)
            is_success = check_file(full_filename, CONFIG.error_detect, strict_level=CONFIG.strict_level, zero_detect=CONFIG.zero_detect)
            out_queue.put(is_success)
    except Empty:
        print("Closing parallel worker, the worker has no more tasks to perform")
        return
    except Exception as e:
        print ("Parallel worker got unexpected error {}".format(str(e)))
        sys.exit(1)

def worker_b(in_queue, out_queue):
    import logging
    logger = logging.getLogger("worker_b:")
    try:
        while True:
            full_filename = in_queue.get(block=True, timeout=2)
            is_success = check_file_b(full_filename, 0, strict_level=0, zero_detect=0)
            out_queue.put(is_success)
    except Empty:
        logger.info("Closing parallel worker, the worker has no more tasks to perform")
        return
    except Exception as e:
        logger.error("Parallel worker got unexpected error {}".format(str(e)))
        sys.exit(1)
      



def setup(configuration):
    global logger
    global DEBUG
    global DRYRUN
    global MEDIA_EXTENSIONS, PIL_EXTENSIONS
    
    MEDIA_EXTENSIONS += VIDEO_EXTENSIONS  #+ PIL_EXTENSIONS #+ PDF_EXTENSIONS
    MEDIA_EXTENSIONS += MAGICK_EXTENSIONS
    

def getCLIparams(cli_args):
    if DEBUG: print('CLI Params {0}'.format(cli_args))
    parser = argparse.ArgumentParser(None)
    parser.prog = __prog_name__
    parser.description = "This program pulls all of the network information by AWS Account number"
    parser.epilog = "Eventually you can pass AWS variables right now only the profile variable."
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

    parser.add_argument('-d', '--debug', 
                    help = 'Turn on debugging',
                    action = 'store_true',
                    required = False,
                    dest='debug', 
                    default=False
                    )
    
    
    parser.add_argument('-dr', '--dryrun', 
                    help = 'Turn on verbose output',
                    action = 'store_true',
                    required = False,
                    dest='dryrun', 
                    default=False
                    )

    parser.add_argument('-l', '--log-level', 
                    help = 'Set the loglevel {alert | crit | err | warning | notice | info | debug} - lowercase',
                    type = str,
                    action = 'store',
                    choices = ['INFO','WARNING','DEBUG'],
                    required = False,
                    dest='loglevel', 
                    default='INFO'
                    )
       
    parser.add_argument('-of', '--output-file', type=str,
                    help = 'Filename for output defaults to xls format',
                    action = 'store',
                    required = False,
                    dest='output_filename', 
                    default='output'
                    )
    
    parser.add_argument('-f', '--output-format', type=str,
                    help = 'Format for output { txt, csv, xls}',
                    action = 'store',
                    required = False,
                    dest='format', 
                    default='csv'
                    )
    
    parser.add_argument('-id', '--input-dir', type=str,
                    help = 'Directory for studio inventory',
                    action = 'store',
                    required = True,
                    dest='studio',  
                    )

    parser.add_argument('-p', '--prefix', type=str,
                    help = 'Prefix for Studio',
                    action = 'store',
                    required = True,
                    dest='prefix', 
                    default='XXXX'
                    )

    parser.add_argument('-t', '--threads', type=int,
                    help = 'Prefix for Studio',
                    action = 'store',
                    required = False,
                    dest='threads', 
                    default=10
                    )
 
    parser.add_argument('-to', '--timeout', type=int,
                    help = 'Prefix for Studio',
                    action = 'store',
                    required = False,
                    dest='timeout', 
                    default=5
                    )
                    
    
    parse_out = parser.parse_args(cli_args)
    

    return parse_out



## Main Program starts here
def main():
    #Local Variables
    COLUMNS =[]
    sheet = {}
    inventory_list = {}
    dir_list = {}
    CONFIG = getCLIparams(None)
    setup(CONFIG)
    
    #===============================================================================
    # Setup  Logging
    #===============================================================================
    import logging
    import logging.config 
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=CONFIG.loglevel)

    logger.critical(CONFIG)
    
    
    ###############################################################
    # Set Common names for config variables in CAPS
    FILENAME = CONFIG.output_filename
    STUDIO_DIR = CONFIG.studio
    
    logger.critical('Creating a spreadsheet name {0} from studio dir {1}'.format(FILENAME,STUDIO_DIR))
     
    # Create XLS Sheet 
    workbook = xlsxwriter.Workbook(FILENAME,{'constant_memory': True, 'tmpdir': '/Users/colinbitterfield/tmp' })
    inventory = workbook.add_worksheet('inventory')
    inventory_list = workbook.add_worksheet('inventory_list')
     
    # Create worksheet formatting
    header = workbook.add_format({'font_name' : 'Helvetica','font_size':'14','font_color': 'black','bold': True,'align' : 'center'})
    bold   = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','font_color': 'black','bold': True,'align' : 'center'})
    percent = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','num_format': '0.00%'})
    normal = workbook.add_format({'font_name' : 'Helvetica','font_size':'12'})
    bg_green = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': "#B0BF1A"})
    bg_red = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': 'red' })
    bg_amber = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': "#FFBF00"})
    bg_missing = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': "#FFD4CC"})
    green = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': 'green'})
    red = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': 'red' })
    amber = workbook.add_format({'font_name' : 'Helvetica','font_size':'12','bg_color': "#FFBF00"})
 
    
    # Get list of subdirectorys to form columns in spreadsheet
    dir_listing = os.listdir(STUDIO_DIR)
    logger.info(dir_listing)
    for dir in dir_listing:
        if os.path.isdir(STUDIO_DIR + '/' + dir): 
            logger.info('Is dir {}'.format(dir))
            COLUMNS.append(dir)
        else:
            logger.info('Is not dir {}'.format(dir))
    COLUMNS = list(filter(lambda x: not x.startswith('.'),COLUMNS))        
    COLUMNS.sort(reverse = True)
    logger.info('Using these columns for spreadsheet {}'.format(COLUMNS))
    for column in COLUMNS:
        #Create a spreadsheet for each directory
        logger.critical('Creating sheet named {}'.format(column))
        sheet[column]=workbook.add_worksheet(column)
    videos =  workbook.add_worksheet('videos2')    
    for column in COLUMNS:
        dir_list[column] =  os.listdir(STUDIO_DIR + '/' + column)    
        dir_list[column] = list(filter(lambda x: not x.startswith('.'),dir_list[column]))
        dir_list[column].sort()
     
    max_list ={}
    for column in COLUMNS:
        max_list[len(dir_list[column])] = column
         
    max_column = max(max_list.keys())
    big_column = max_list[max_column]
    logger.info('The list with the most values is {}'.format(big_column))
     
    # First create a dict of all of the values for the biggest list
    long_list = {}
    row = 1
    for value in dir_list[big_column]:
        SUCCESS, EDGEID = assignID(row=row,current_id=os.path.basename(value),prefix=PREFIX,method='num_right_side')
        if SUCCESS:
            long_list[row] = { 'EDGEID' : EDGEID}
        else:
            long_list[row] = { 'EDGEID' : None}
        long_list[row].update( { big_column : value } )
        logger.debug('Writing row # {0} values {1}'.format(row,long_list[row]))
        for column in COLUMNS:
            if column != big_column:
                match,confidence = bestMatch(value=value,list=dir_list[column])
                long_list[row].update({column : match})
                long_list[row].update({column + '_confidence' : confidence})
                 
                     
        row = row + 1
     
    logger.info('Number of rows create {0}'.format(len(long_list)))
     
    # send output to inventory tab
    row = 0
    col = 0
     
        # Setup Conditional Formatting
    # Write a conditional format over a range.
    max_rows_for_format = len(long_list) + 1
    # Format cell red if cell is blank
    inventory.conditional_format('A2:A'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': 'ISBLANK($C2)',
                                  'format':   bg_missing})
     
    inventory.conditional_format('B2:B'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '=ISBLANK($B2)',
                                  'format':   bg_missing})
     
    inventory.conditional_format('C2:C'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '=ISBLANK($C2)',
                                  'format':   bg_missing})
 
    inventory.conditional_format('E2:E'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '=ISBLANK($E2)',
                                  'format':   bg_missing})
     
    inventory.conditional_format('C2:D'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '$D2 <= .50',
                                  'format':   bg_red})
     
    inventory.conditional_format('C2:D'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '=and ($D2 > .50 , $D2 < .66)',
                                  'format':   bg_amber})
         
    inventory.conditional_format('C2:D'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '$D2 >= .75',
                                  'format':   bg_green})
 
    inventory.conditional_format('E2:F'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '$f2 <= .50',
                                  'format':   bg_red})
     
    inventory.conditional_format('E2:F'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '=and ($f2 > .50 , $f2 < .66)',
                                  'format':   bg_amber})
         
    inventory.conditional_format('E2:F'+str(max_rows_for_format), 
                                 {'type':     'formula',
                                  'criteria': '$f2 >= .75',
                                  'format':   bg_green})
     
     
   
    # Write a header row
    header = list(long_list[1].keys())
    inventory.write_row(row,row,header)
    column_width = {}
    for column in header:
        column_width[column] = len(column)+6
        inventory.set_column(col,col,column_width[column])
        col = col + 1
    for row in long_list.keys():
        col = 0
        logger.debug('Row = {0} data = {1}'.format(row,long_list[row]))
        for column in long_list[row].keys():
            column_width[column] = len(str(long_list[row][column])) if len(str(long_list[row][column])) > column_width[column] else column_width[column]
            logger.debug('Current Width {0} Proposed Width {1} for column name {2}'.format(column_width[column],len(str(long_list[row][column])),column))
            if type(long_list[row][column]) == str:
                inventory.write(row,col,long_list[row][column],normal)
            else:
                inventory.write(row,col,long_list[row][column],percent)
             
            col = col + 1
         
     
    logger.info('Column Widths {}'.format(column_width))
    col = 0
    for column in column_width.keys():
        logger.info('setting col {0} to width {1} named {2}'.format(col,column_width[column],column))
        inventory.set_column(col,col, column_width[column] + 4, None)
        col = col + 1
         
         
         
    #Output to inventory_list
    inventory_list.write_row(0,0,COLUMNS,bold)
    col = 0
    for column in COLUMNS:
        row = 1
        for row_value in dir_list[column]:
            inventory_list.write(row,col,row_value,normal)
            row = row + 1
        inventory_list.set_column(col,col, column_width[column] + 4, None)
        col = col + 1 
         
         
    logger.critical('Completed Dirs')

    # Start Integrity Check
        # initializations
    logger.debug('Media Extensions to consider {}'.format(MEDIA_EXTENSIONS))
    count = 0
    count_bad = 0
    total_file_size = 0
    bad_files_info = [("file_name", "error_message", "file_size[bytes]")]
    timed_logger = TimedLogger().start()

    task_queue = Queue()
    out_queue = Queue()
    pre_count = 0
    q_files = 0
    for root, sub_dirs, files in os.walk(STUDIO_DIR):

        media_files = []
        for filename in files:
            if is_target_file(filename):
                media_files.append(filename)
            else:
                logger.debug('File is not in our criteria {}'.format(filename))
        
        pre_count += len(media_files)
        
        for filename in media_files:
            full_filename = os.path.join(root, filename)
            if task_queue.full():
                logger.critical('Task queue is full')
            task_queue.put(full_filename)
            q_files = q_files + 1
    
    logger.critical('Number of files to process {0:,}'.format(q_files))    
    
    for i in range(CONFIG.threads):
        p = Process(target=worker_b, args=(task_queue, out_queue,))
        p.start()

# consume the outcome
    logger.debug('Processing {0} files'.format(len(media_files)))
    

    file_info = {}
    worker_row = {}
    worker_col ={}
    col = 0


    #Setup the output for each column
    for COLUMN in COLUMNS:
        worker_row[COLUMN] = 0
        worker_col[COLUMN] = 0
        logger.critical('Write header for {}'.format(COLUMN))
        sheet[COLUMN].write_row(worker_row[COLUMN],worker_col[COLUMN],OUTPUT_ROW_HEADER[COLUMN])
        worker_row[COLUMN] = worker_row[COLUMN] + 1

    try:
        for j in range(pre_count):

            count += 1

            is_success = out_queue.get(block=True, timeout=CONFIG.timeout)
            STATUS = 'Verified Good'  if is_success[0] else 'Bad'
            FILENAME = is_success[1][0]
            DATA = is_success[1][3]
            file_size = is_success[1][2]
            if file_size != 'NA':
                total_file_size += file_size

            if not is_success[0]:
                check_outcome_detail = is_success[1]
                count_bad += 1
                bad_files_info.append(check_outcome_detail)
                log_check_outcome(check_outcome_detail)
            
            if STATUS:    
                logger.info('File {0} is {1} size {2} data {3}'.format(FILENAME,STATUS,file_size,DATA))
            
            else:
                logger.error('File {0} is {1} size {2} data {3}'.format(FILENAME,STATUS,file_size,DATA))
            
            RELATIVE_PATH = FILENAME.replace(STUDIO_DIR + '/','')    
            
            COLUMN = os.path.dirname(RELATIVE_PATH).split('/')[0]
            logger.debug('Short path {0} Column {1}'.format(RELATIVE_PATH,COLUMN))
            
            if 'VIDEO' in COLUMN.upper():
                # This is too big to store in memory, so we write it out a line at a time.
                # Built a spreadsheet row.
                # Clear the row
                OUTPUT_ROW = []
                OUTPUT_ROW += [os.path.basename(FILENAME)]
                OUTPUT_ROW_WIDTHS[COLUMN]['filename'] = len(str(os.path.basename(FILENAME))) if len(os.path.basename(FILENAME)) > OUTPUT_ROW_WIDTHS[COLUMN]['filename'] else OUTPUT_ROW_WIDTHS[COLUMN]['filename']                          
                OUTPUT_ROW += [DATA['format']['duration']]
                OUTPUT_ROW_WIDTHS[COLUMN]['duration'] = len(str(DATA['format']['duration'])) if len(DATA['format']['duration']) > OUTPUT_ROW_WIDTHS[COLUMN]['duration'] else OUTPUT_ROW_WIDTHS[COLUMN]['duration']                          
                OUTPUT_ROW += [DATA['md5']]
                OUTPUT_ROW_WIDTHS[COLUMN]['md5'] = len(str(DATA['md5'])) if len(DATA['md5']) > OUTPUT_ROW_WIDTHS[COLUMN]['md5'] else OUTPUT_ROW_WIDTHS[COLUMN]['md5']                          
 
                
                # Find the first stream that is a video
                video_stream = None
                audio_stream = None
                PROBLEM = False
                stream = 0
                for stream in DATA['streams']:
                    if stream['codec_type'] == 'video' and video_stream is None:
                        video_stream = stream
                     
                    if stream['codec_type'] == 'audio' and audio_stream is None:
                        audio_stream = stream
                     
                if video_stream:
                    for F in VIDEO_FIELDS:
                        if F in video_stream.keys():                  
                            OUTPUT_ROW_WIDTHS[COLUMN][F] = len(str(video_stream[F])) if len(str(video_stream[F])) > OUTPUT_ROW_WIDTHS[COLUMN][F] else OUTPUT_ROW_WIDTHS[COLUMN][F]
                            OUTPUT_ROW += [str(video_stream[F])]
                        else:
                            OUTPUT_ROW += ['']
                else:
                    OUTPUT_ROW += VIDEO_FIELDS
                    PROBLEM = True
                         
                if  audio_stream:  
                    for F in AUDIO_FIELDS:
                        if F in audio_stream.keys():
                            OUTPUT_ROW_WIDTHS[COLUMN][F] = len(str(audio_stream[F])) if len(str(audio_stream[F])) > OUTPUT_ROW_WIDTHS[COLUMN][F] else OUTPUT_ROW_WIDTHS[COLUMN][F]
                            OUTPUT_ROW += [str(audio_stream[F])]
                        else:
                            OUTPUT_ROW += ['']
                else:
                    OUTPUT_ROW += AUDIO_FIELDS
                    PROBLEM = True
                     
                OUTPUT_ROW += [FILENAME]
                OUTPUT_ROW_WIDTHS[COLUMN]['full_filename'] = len(str(FILENAME)) if len(FILENAME) > OUTPUT_ROW_WIDTHS[COLUMN]['full_filename'] else OUTPUT_ROW_WIDTHS[COLUMN]['full_filename']                          
 
                 
                 
                if len(DATA['streams']) > 2: OUTPUT_ROW.append("Additional Streams are present in source material")
                 
                 
                
                if PROBLEM:  
                    sheet[COLUMN].write_row(worker_row[COLUMN],0,OUTPUT_ROW,amber)
                else:
                    sheet[COLUMN].write_row(worker_row[COLUMN],0,OUTPUT_ROW,normal)
                     
                worker_row[COLUMN] = worker_row[COLUMN] + 1
                 
            elif 'PHOTO' in COLUMN.upper(): 
                OUTPUT_ROW=[]
   
   
             
            else:
                pass # 2257s
                
            timed_logger.print_log(count, count_bad, total_file_size)
        
    except Empty as e:
        logger.critical("Waiting other results for too much time, perhaps you have to raise the timeout".format( e.message))
    
    logger.info("**Task completed**")
    timed_logger.print_log(count, count_bad, total_file_size, force=True)
    
#     for COLUMN in COLUMNS:
#         logger.info('Setting Column Widths for {0}'.format(COLUMN))
#         col = 0
#         for value in range(0,len(OUTPUT_ROW_HEADER[COLUMN])):
#             logger.info(OUTPUT_ROW_WIDTHS[COLUMN][value])
#             logger.debug('Column {0} value{1} Width {1}'.format(COLUMN,value,OUTPUT_ROW_WIDTHS[COLUMN] ))
#             sheet[COLUMN].set_column(col,col, OUTPUT_ROW_WIDTHS[COLUMN][value] + 4)
#             col = col + 1
            
    workbook.close()
    logger.critical('end of program')
    
if __name__ == "__main__":
    

   
    main()
