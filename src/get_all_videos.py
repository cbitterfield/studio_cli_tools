#!/usr/bin/env python3

'''
Created on Aug 6, 2019

@author: colin
'''

import os 
import sys
import csv
from collections import Counter
import ffmpeg
from sysconfig import get_platform
from jupyter_core.tests.mocking import linux

ext = ('.mp4','avi','mov','wmv','m4v','flv')
in_use = {}
mac_list=['/DAVID_SLAUGHTER']
linux_list=['/EdgeSource01/C1D767-C1D784/C1D768 GMHD Global Media Group 1 1770 GB/']
video_info={}
video_info_list={}
audio_info_list={}
dir_parts =[]
video_info_list = ['width','height','duration','codec_name','display_aspect_ratio','bit_rate']
audio_info_list = ['codec_name','codec_long_name','bit_rate']



outputfile = '/tmp/dir_info.csv'
outputjob = '/tmp/dir_info.stats'

def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        if not entry.startswith('.'):
            fullPath = os.path.join(dirName, entry)
            # If entry is a directory then get the list of files in this directory 
            if os.path.isdir(fullPath):
                allFiles = allFiles + getListOfFiles(fullPath)
            else:
                if fullPath.lower().endswith(ext):
                    allFiles.append(fullPath)
                    
                
                #make a list of all extensions in use
                junk,current_extension = os.path.splitext(fullPath)
                if current_extension in in_use:
                    in_use[current_extension] = in_use[current_extension] + 1
                else:
                    in_use[current_extension] = 1
                
    return allFiles        


def main():
    if 'mac' in get_platform():
        prefix='/Volumes'
        FFPROBE='/opt/local/bin/ffprobe'
        dir_list = mac_list
    else:
        prefix='/edge'
        FFPROBE='/usr/local/bin/ffprobe'
        dir_list = linux_list
        
    print ('starting')
    video_data = open(outputfile, 'w')
    stats_file = open(outputjob,'w')
    
    skipped = 0
    counter = 0
    g_processed = 0
    max_lenth = 0
    
    
    header_names = ['source', 'media_file_name', 'media_directory', 'video_width', 'video_height', 'video_duration', 'video_codec_name', 'video_display_aspect_ratio', 'video_bit_rate', 'audio_codec_name', 'audio_codec_long_name', 'audio_bit_rate','dirpart0','dirpart1','dirpart2','dirpart3','dirpart4','dirpart5','dirpart6','dirpart7','dirpart8','dirpart9','dirpart10','dirpart10','dirpart11','dirpart12','dirpart13','dirpart14','dirpart15','filetype','status']
    writer = csv.DictWriter(video_data, fieldnames=header_names) 
    writer.writeheader()
    for dir_eval in dir_list:
        dir_eval = prefix + dir_eval
        
    
        # Get the list of all files in directory tree at given path
        listOfFiles = getListOfFiles(dir_eval)
        
        
        
        # Print the files
        for complete_name in listOfFiles:
            
            # Prepare CSV output
            
            csv_output = {}
            probe_name = complete_name.strip()
            filename=complete_name.strip().replace(prefix + '/','')
            dir_parts = filename.split('/',14)
            for part in dir_parts:
                csv_output['dirpart' + str(dir_parts.index(part))] = part
            csv_output['source'] = filename
            csv_output['media_file_name'] = os.path.basename(filename)
            csv_output['media_directory'] = os.path.dirname(filename)
            trash,file_extension = os.path.splitext(complete_name)
            file_extension = file_extension.replace('.','').lower()
            csv_output['filetype'] = file_extension
            
            
            try:
                #print('Getting info for {0}'.format(probe_name))
                probe = ffmpeg.probe(probe_name,cmd='/opt/local/bin/ffprobe')
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                audio_stream =  next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                
                if video_stream is not None:
                    
                    for video_info in video_info_list: 
                        if video_info in video_stream.keys():
                            if video_info == 'duration':
                                csv_output['video_' + video_info] = humanize_time(int(round(float(video_stream['duration']))))
                            else:
                                csv_output['video_' + video_info] = video_stream[video_info]
                            
                           
                    
                if audio_stream is not None:
                    for audio_info in audio_info_list:
                        if audio_info in audio_stream.keys():
                            csv_output['audio_' + audio_info] = audio_stream[audio_info]
                
                g_processed = g_processed + 1
                csv_output['status']='processed'
            
            except ffmpeg.Error as e:
                print('Error {0} Skipping {1}'.format(skipped,probe_name))
                skipped = skipped + 1
                csv_output['status']='skipped'
        
            #print(csv_output)
            counter = counter + 1
            if len(dir_parts) > max_lenth:
                max_lenth = len(dir_parts)
            #print(csv_output)    
            writer.writerow(csv_output)
            print('Files checked {0} Files Processed {1} Files Skipped {2} max parts {3}'.format(counter,g_processed,skipped,max_lenth))
            
            
        stats_file.write("****************\n")
        stats_file.write("***  stats   ***\n")
        stats_file.write("****************\n")
        
        sorted_extensions = Counter(in_use)
        stats_file.write ('Number of extensions in use are {}\n'.format(len(sorted_extensions.keys())))
        for ext_used,ext_times in sorted_extensions.most_common():
            stats_file.write('Extension {0} is used {1} times\n'.format(ext_used,ext_times))
        
        stats_file.write('Max number of filename parts is {0}\n'.format(max_lenth))
        stats_file.write('Files checked {0} Files Processed {1} Files Skipped {2}\n'.format(counter,g_processed,skipped))

        stats_file.write("********************\n")
        stats_file.write("***  end stats   ***\n")
        stats_file.write("********************\n")

        video_data.close()
        stats_file.close()

if __name__ == '__main__':
    main()