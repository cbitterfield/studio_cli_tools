#!/usr/bin/env python3
# encoding: utf-8
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

import sys
import os
from string import Template
from shutil import copy

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2019-07-21'
__updated__ = '2019-07-21'

DEBUG = False
TESTRUN = False
NOEXEC = False

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2019 organization_name. All rights reserved.

  Licensed under the GNU Public License 3.0
  https://www.gnu.org/licenses/gpl-3.0.en.html

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-c","--configfile", dest="config", default="config.yaml", help="use config file, default is config.yaml in working dir")
        parser.add_argument("-l","--log", action="store",default="console", help="logfile for output, if none is selected then use console" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument("-i", "--input", dest="input", action="store", help="set input filename")
        parser.add_argument("-o", "--output", dest="output", action="store", help="set output filename")
        parser.add_argument("-d", "--debug", dest="debug", action="store", default="INFO", help="set the debug level [INFO|ERROR|WARN|DEBUG]")
        parser.add_argument("-n", "--noexec", dest="noexec", action="store_true", help="Do not make any changes to data or os layer, just show what you would do" )
        # Process arguments
        args = parser.parse_args()
        print(args)

        config = args.config
        logfile = args.log
        debug = args.debug
        inputfile = args.input
        outputfile = args.output
        noexec = args.noexec
    


        if debug:
            print("Debug Value: {}".format(debug))
            
        if noexec:
            print("NOEXEC=True; No data or files will be changed")

        #===============================================================================
        # Setup  Logging
        #===============================================================================
        import logging
        import logging.config 
        import logging.handlers


        # Set Formatting
        LOG_FORMAT = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        LOG_DATE = '%m/%d/%Y %I:%M:%S %p'
        LOG_STYLE = style='%'

        if not 'Linux' in os.uname()[0]:
            LOG_SOCKET = '/var/run/syslog'
        else:
            LOG_SOCKET = '/dev/log'

        # create logger
        # set name as desired if not in a module
        logger = logging.getLogger('__name__')
        logger.setLevel(logging.DEBUG)

        # create handlers for Console and set level
        CONSOLE = logging.StreamHandler()
        CONSOLE.setLevel(logging.DEBUG)

        #create handlers for Syslog and set level
        SYSLOG = logging.handlers.SysLogHandler(address=LOG_SOCKET, facility='local0')
        SYSLOG.setLevel(logging.INFO)

        #create handler for FILENAME and set level
        LOG_FILE = logging.FileHandler('/tmp/logger.log',mode='a', encoding=None, delay=False)
        LOG_FILE.setLevel(logging.INFO)
        # create formatter
        formatter = logging.Formatter(LOG_FORMAT)

        # add formatter(s) to handlers
        CONSOLE.setFormatter(formatter)
        SYSLOG.setFormatter(formatter)
        LOG_FILE.setFormatter(formatter)

        # add handlers to logger
        logger.addHandler(CONSOLE)
        logger.addHandler(SYSLOG)
        logger.addHandler(LOG_FILE)
         
        
        
        #===========================================================================
        # Main program starts here
        #===========================================================================
        logger.info('{0} starting with debug level of {1}'.format(os.path.basename(__file__),debug))        
        COPY_TEMPLATE="cp '$SOURCE' '$DESTINATION/$VIDEO'"
        
        JPG_TEMPLATE=""
        
        PREVIEW_TEMPLATE=""
        
        sourcefile = open ('./working_files','r')
        
        for row in csv.reader(sourcefile):
            edge_id, source, master = row
            source = source.replace('EDGE01/DATAVOL4','/edge')
            finaldestination = '/edge/Scratch/deployment-2019-07-18/' + master
            video_name = str(edge_id) + '_VIDEO_1280x720x1500k.MP4'
            v = video_name.upper()
            source_name = os.path.basename(source)
            try:
                if os.path.exists(source):
                    # Do Copy
        
                    if not os.path.exists(finaldestination):
                        print('Creating directory {}'.format(finaldestination))
                        os.makedirs(finaldestination, mode=0o755, exist_ok=False)
                    if copy(source, finaldestination + video_name ):
                        STATUS='good copy'
                    else:
                        STATUS='failed copy'
                    print ('Copying {0} to {1} with status: {2}'.format(source_name,video_name,STATUS))
                else:
                    # File doesn't exist error
                    print("File {0} source doesn't exist".format(source))
            except OSError as err:
                print("OS error: {0}".format(err))
            except Exception as err:
                print("An exception occurred {}".format(err))

        #=======================================================================
        # Main program ends here
        #=======================================================================

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
    
    
    
    
    

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d INFO")
        
    if TESTRUN:
        import doctest
        doctest.testmod()
    if NOEXEC:
        print("No exec")
        sys.argv.append("--noexec")
        
    
    



   
        
    sys.exit(main())