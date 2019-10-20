#!/usr/bin/env python3
# encoding: utf-8
'''
create_page -- shortdesc

create_page is a description

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
import re

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2019-07-16'
__updated__ = '2019-07-16'

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
        parser.add_argument("-i", "--input", dest="input", action="store", help="set input partnumbers")
        parser.add_argument("-t", "--title", dest="title", action="store", help="set page title")
        parser.add_argument("-o", "--output", dest="output", action="store", help="set output filename")
        parser.add_argument("-d", "--debug", dest="debug", action="store", default="INFO", help="set the debug level [INFO|ERROR|WARN|DEBUG]")
        parser.add_argument("-n", "--noexec", dest="noexec", action="store_true", help="Do not make any changes to data or os layer, just show what you would do" )
        # Process arguments
        args = parser.parse_args()
        print(args)

        config = args.config
        logfile = args.log
        debug = args.debug
        inputparts = args.input
        outputdir = args.output
        noexec = args.noexec
        html_title=args.title


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
        CONSOLE.setLevel(logging.INFO)

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
        logger.info('Creating page {0} with part numbers {1}'.format(html_title,inputparts))
        
        #Test for valid input
        
        if os.path.isdir(outputdir) and len(inputparts) > 0:
            logger.info("All is good for processing")
        else:
            logger.error("FAILED: Either your output dir does not exist {0} or you don't have enough input elements to process {1}".format(outputdir,inputparts))
            return 1
        
        
        HTML_HEADER_TEMPLATE="""
<!doctype html>
<head>
<meta charset="UTF-8">
<title>$TITLE</title>
<link href="category.css" rel="stylesheet" type="text/css">
</head>

<body>
  <div class="category">  
  <div class="container">
  <div class="title"><center>$TITLE</center></div>
  <div class="message">Watch FREE HD XXX PORN Videos</div>
  <div class="menu"><a href="index.html" target="_self">Back to Categories</a></div>
     
        """
        
        
        # Create Video Lines 
        HTML_HEADER = Template(HTML_HEADER_TEMPLATE).safe_substitute(TITLE=html_title)
        counter=3
        video_dir=""
        video_name=""
        preview_dir=""
        preview_name=""
        studio=""
        
        #poster="$POSTER"  width="200"
        
        VIDEO_TEMPLATE="""
        
         <div class="video videos">
         <a href="/video_play.php?VIDEO=$VIDEO"  width="1280" target="_parent">
         <video poster="$POSTER" width="320"  loop>
             <source src="$PREVIEW_DIR/$PREVIEW_NAME" type="video/mp4">
         </video>
         <p>$VIDEO</p>
        
         </a>      
         </div>
        
        """
        
        logger.debug(HTML_HEADER)        
        PAGE=HTML_HEADER 
        videos = inputparts.split(' ')
        for video in videos:
            studio = re.search("^([A-Z]*)", video)[1]
            
            logger.info("Studio {}".format(studio))
            video_dir = "https://services.porncentral.us/" + studio + "_Scenes_SS/" + video + "_S/" + video +"_I"
            preview_dir ="https://services.porncentral.us/" + studio + "_Scenes_SS/" + video + "_S/" + video +"_T"
            video_name=video + "_1280x720x1500.MP4"
            preview_name=video + "_PREVIEW_1280x720x1500K.MP4"
            poster = "https://services.porncentral.us/" + studio + "_Scenes_SS/" + video + "_S/" + video +"_T/" + video + "_POSTER.JPG"
            logger.info("Creating entry for part number {0}".format(video))
            HTML_VIDEO = Template(VIDEO_TEMPLATE).safe_substitute(ELEMENT=counter,VIDEO_DIR=video_dir,VIDEO_NAME=video_name,PREVIEW_DIR=preview_dir, PREVIEW_NAME=preview_name,POSTER=poster, VIDEO=video)
            PAGE=PAGE+HTML_VIDEO
            logger.debug("Video-{0} HTML: {1} {2}".format(counter,HTML_VIDEO,poster))
            counter = counter + 1
        
        # <iframe  width="1280" height="720" name="video"></iframe>
        
        HTML_FOOTER="""
        <div class="video spacer">
       
        <p>spacer<p>
        
        </div> 
        
        <div class="video footer"><P>footer</P></div>     
        <div class="video bottom"><P>bottom</P></div>     
        </div>
    
        <script src="/videohover.js"></script>
        </div>
        </body>
        
        </html>

        
        """
        PAGE = PAGE + HTML_FOOTER
        
        html_title = html_title.lower()
        pagefile_template = outputdir + "/" + html_title + ".html"
        pagefile = pagefile_template
        logger.info("Writing page {}".format(pagefile))
        
        pagefile = open(pagefile, "w")
        pagefile.write(PAGE)
        pagefile.close()
        
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