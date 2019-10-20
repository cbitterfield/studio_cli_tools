#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2019

@author: colin

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



# Media Support

# The following extensions includes only the most common ones, you can add other extensions BUT..
# ..BUT, you have to double check Pillow, Imagemagick or FFmpeg to support that format/container
# please in the case I miss important extensions, send a pull request or create an Issue

PIL_EXTENSIONS = ['jpg', 'jpeg', 'jpe', 'png', 'bmp', 'gif', 'pcd', 'tif', 'tiff', 'j2k', 'j2p', 'j2x', 'webp']
PIL_EXTRA_EXTENSIONS = ['eps', 'ico', 'im', 'pcx', 'ppm', 'sgi', 'spider', 'xbm', 'tga']

MAGICK_EXTENSIONS = ['psd', 'xcf']

PDF_EXTENSIONS = ['pdf']

# this ones are managed by libav or ffmpeg
VIDEO_EXTENSIONS = ['avi', 'mp4', 'mov', 'mpeg', 'mpg', 'm2p', 'mkv', '3gp', 'ogg', 'flv', 'f4v', 'f4p', 'f4a', 'f4b']
AUDIO_EXTENSIONS = ['mp3', 'mp2']

MEDIA_EXTENSIONS = []

SUPPORT_TYPES = PIL_EXTENSIONS + PIL_EXTRA_EXTENSIONS + MAGICK_EXTENSIONS + PDF_EXTENSIONS + PDF_EXTENSIONS + AUDIO_EXTENSIONS + MEDIA_EXTENSIONS

# Global Variables
UPDATE_SEC_INTERVAL = 5  # sec
UPDATE_MB_INTERVAL = 500  # minimum MBytes of data between output log/messages

# SpreadSheet Tabs (or later SQL Tables
workbook = ''
worksheet = {}
xls_tabs = ['video_hd','video_sd','photosets','USC_2257','video_hd_errors','video_sd_errors','photosets_errors','USC_2257_errors']

video_header=('directory','filename','md5','width','height','runtime_seconds')
photoset_header=['directory','filename','md5','width','height','depth']
USC_2257_header=['directory','filename','md5']
error_header=['directory','filename','md5','error']

# Import Libraries

import sys
import os
import time
import PIL
import PyPDF2
import csv
import xlsxwriter
import ffmpeg
import argparse
#import PyPDF2d
import textwrap as _textwrap
import shutil
from subprocess import Popen, PIPE
import warnings
from queue import Empty
from multiprocessing import Pool, Queue, Process


# Define System Variables
console_size = shutil.get_terminal_size((80, 20))[0]
runtime = epoch_time = int(time.time())

if DEBUG: console_size = 132

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

class MultilineFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        text = self._whitespace_matcher.sub(' ', text).strip()
        paragraphs = text.split('|n ')
        multiline_text = ''
        for paragraph in paragraphs:
            formatted_paragraph = _textwrap.fill(paragraph, width, initial_indent=indent,
                                                 subsequent_indent=indent) + '\n\n'
            multiline_text = multiline_text + formatted_paragraph
        return multiline_text

def getArgs(argv=None):
    parser = argparse.ArgumentParser()
    parser.prog =os.path.basename(__file__)
    parser.description = "This is where the command-line utility's description goes."
    parser.epilog = "This is where the command-line utility's epilog goes."
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    
    parser.add_argument('-t', '--threads', type=int,
                    help='number of parallel threads used for speedup, default is one. Single file execution does'
                         'not take advantage of the thread option',
                    dest='threads', default=1)
    
    parser.add_argument('-s','--studio',
                        help='The name of the studio_ID for this studio',
                        dest='studio', default='UNKNOWN')
    
    parser.add_argument('-x','--xls',
                        help='THe name of the spreadsheet if no directory is specified it is written to the current directory',
                        dest='xls_filename',
                        default='media_validated.xlsx')
    
    parser.add_argument('-d','--debug',
                        help='Set the Debug LEVEL, default is NONE',
                        dest='loglevel')
    
    parser.add_argument('-v','--verbose',
                        help='Give as much information as possible',
                        dest='verbose', action='store_true', default=False)
    
    parser.add_argument('-n','--no-md5',
                        help='Save time and do not generate MD5 signatures',
                        dest='md5', action='store_true', default=False)
    
    parser.add_argument('-p','--path',
                        help='Path to media files. This will recursively check all files below this directory',
                        dest='source_path', action='store',default='./')
    
    parser.add_argument ('-o','--overwrite',
                        help='Overwrite the existing xlsx file if it exists',
                        dest='overwrite',action='store_true',default=False)
    
    parser.add_argument('--list',
                        help='display a list of all media extensions supported',
                        dest='list')
    
    parse_out = parser.parse_args()
    return parse_out
        
def setup(configuration):
    global MEDIA_EXTENSIONS, PIL_EXTENSIONS
    global console_size
    global runtime

    if DEBUG: print('Console Size = {}'.format(console_size))
    
    
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

def center_string(*args):
    '''
    takes four parameters edge_string, pad_string, string and line size
    returns a string padded on both sides by the pad string
    returns an error message if the number of arguments is wrong
    example center_string('=','mystring',60)
    '''
    
    
    
    
    
    if len(args) > 4:
        return ' Wrong number of arguments passed, got ' + str(len(args)) + 'expected 4'
    
    
    edge_char = args[0]
    pad_char = args[1]
    string = args[2]
    console_size = int(args[3])
    max_string = console_size - 6
    
    if len(string) > console_size - 4:
        string = ('..' + string[len(string)-max_string:] ) if len(string) > max_string else 'problem'
        
    
    if len(string) % 2 == 1:
        string = string + ' '
    
    string_length = len(string)
    
    side_size = int ((console_size - string_length ) / 2)
    
    left_side = edge_char.ljust(side_size,pad_char)
    right_side = edge_char.rjust(side_size,pad_char)
    return left_side + string + right_side
    
    
class TimedLogger:
    def __init__(self):
        self.previous_time = 0
        self.previous_size = 0
        self.start_time = 0

    def start(self):
        self.start_time = self.previous_time = time.time()
        return self

    def print_log(self, num_files, num_bad_files, total_file_size, wait_min_processed=UPDATE_MB_INTERVAL, force=False):
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
            processed_size_MB = float(total_file_size) / (1024 * 1024)

            print('Number of bad/processed files: {num_bad_files} / {num_files} size of processed files: {processed_size_MB}'.
                format(num_bad_files=num_bad_files,num_files=num_files,processed_size_MB=processed_size_MB))
            print('Processing speed: {speed_MB} MB/s, or {speed_IS}'.
                  format(speed_MB=speed_MB,speed_IS=speed_IS))
            

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



def get_extension(filename):
    file_lowercase = filename.lower()
    return os.path.splitext(file_lowercase)[1][1:]
   
def is_target_file(filename):
    file_ext = get_extension(filename)
    return file_ext in MEDIA_EXTENSIONS  


def worker(in_queue, out_queue):
    try:
        while True:
            full_filename = in_queue.get(block=True, timeout=2)
            is_success = check_file(full_filename, CONFIG.error_detect, strict_level=CONFIG.strict_level, zero_detect=CONFIG.zero_detect)
            out_queue.put(is_success)
    except Empty:
        print ("Closing parallel worker, the worker has no more tasks to perform")
        return
    except Exception as e:
        print ("Parallel worker got unexpected error".format(str(e)))
        sys.exit(1)

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
    
    
def main():
    CONFIG = getArgs(None)
    setup(CONFIG)
    
    # initializations
    count = 0
    count_bad = 0
    total_file_size = 0
    bad_files_info = [("file_name", "error_message", "file_size[bytes]")]
    timed_logger = TimedLogger().start()

    task_queue = Queue()
    out_queue = Queue()
    pre_count = 0

    # Validate parameters
    if not os.path.isdir(CONFIG.source_path):
        print('Source Path is not valid, verify and try again. Must be a directory')
        sys.exit(1)
    
    if os.path.isfile(CONFIG.xls_filename) and CONFIG.overwrite == False:
        if DEBUG: print('XLSX File exists filename will be modified')
        xls_name, xls_ext = os.path.splitext(CONFIG.xls_filename)
        CONFIG.xls_filename = xls_name + '_' + str(runtime) + xls_ext
    
    
    if DEBUG: print('Arguments -> {}'.format(CONFIG))
    print(''.ljust(console_size,'=')) 
    message = center_string('=',' ','Studio Media Analysis',console_size)
    print('{}'.format(message))
    print(''.ljust(console_size,'='))
    message = center_string('=',' ','Source Dir',console_size)
    print('{}'.format(message))
    print(''.ljust(console_size,'=')) 
    message = center_string('=',' ',CONFIG.source_path,console_size)
    print('{}'.format(message))
    print(''.ljust(console_size,'='))
    message = center_string('=',' ',CONFIG.xls_filename,console_size)
    print('{}'.format(message))
    print(''.ljust(console_size,'=')) 

    workbook = xlsxwriter.Workbook(CONFIG.xls_filename)
    
    for sheet in xls_tabs:
        worksheet[sheet] = workbook.add_worksheet(sheet)
        if 'video' in sheet and 'error' not in sheet:
            worksheet[sheet].write_row(0, 0, video_header)
        if 'photoset' and 'error' not in sheet:
            worksheet[sheet].write_row(0, 0, photoset_header)
        if '2257'  and 'error' not  in sheet:
            worksheet[sheet].write_row(0, 0, USC_2257_header)
        if 'error' in sheet:
            worksheet[sheet].write_row(0, 0, error_header)
            
            
    # Start Processing the Assets
    print('{source}'.
          format(source=center_string('=',' ','Processing '+CONFIG.source_path,console_size)))
    
    
    for root, sub_dirs, files in os.walk(CONFIG.source_path):
        process_count = 0
        skipped_count = 0
        media_files = []
        for filename in files:
            
            if is_target_file(filename):
                media_files.append(filename)
                print('{source}'.
                  format(source=center_string('=',' ','Processing '+filename + ' added',console_size)))
                process_count = process_count + 1
            else:
                print('{source}'.
                  format(source=center_string('=',' ','Processing '+filename + ' skipped',console_size)))
                skipped_count = skipped_count + 1
        pre_count += len(media_files)
        print('{message}'.
              format(message=center_string('=',' ','Processed '+ str(process_count) + ' Skipped ' + str(skipped_count),console_size)))
        for filename in media_files:
            full_filename = os.path.join(root, filename)
            print('File to check {filename}'.format(filename=full_filename))
            task_queue.put(full_filename)

        

#     for i in range(CONFIG.threads):
#         p = Process(target=worker, args=(task_queue, out_queue,))
#         p.start()


    workbook.close()

if __name__ == "__main__":
    main()