#!/usr/bin/env python3

'''
Created on Aug 6, 2019

@author: colin
'''

import os 
import sys
import csv
import xlsxwriter
from collections import Counter
from collections import defaultdict
import ffmpeg
from sysconfig import get_platform




# Define Global Variables
video_ext = ('mp4','avi','mov','wmv','m4v','flv')
mac_list=['/Users/colin/Downloads']
linux_list=['/EdgeSource01/C1D767-C1D784/C1D768 GMHD Global Media Group 1 1770 GB/']
video_info_list = ['width','height','duration','codec_name','display_aspect_ratio','bit_rate']
audio_info_list = ['codec_name','codec_long_name','bit_rate']
check_dir = ['_video','_pix','_id','_2257','_movie']
studio = 'GMHD'
scenes_header=['edge_id','directory','title','talent','_video','_pix','_id','_2257','_movie']
split_chars = ['-','(','_']

    
if 'mac' in get_platform():
    prefix='/Volumes'
    FFPROBE='/opt/local/bin/ffprobe'
    dir_list = mac_list
else:
    prefix='/edge'
    FFPROBE='/usr/local/bin/ffprobe'
    dir_list = linux_list
        

outputfile = '/tmp/media_info.xlsx'



def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def getListOfDirectories(dirName):
    allDir =[]
    # create a list of file and sub directories 
    # names in the given directory 
    #print('Evaluating {}'.format(dirName))
    listOfDir = os.listdir(dirName)
    for entry in listOfDir:
        #print('Testing {0}'.format(entry))
        if os.path.isdir(os.path.join(dirName, entry)):
            #print('Directory {0} found'.format(entry))
            allDir.append(os.path.join(dirName, entry))
    
    #print(allDir)
    return allDir

def CountFiles(dirName):
    ''' Returns a count of files & their extensions
    '''
    counter = 0
    skipped = 0
    ext_count = {}
    ext_list = {}
    video_list = {}
    audio_list = {}
    
    FileList=os.listdir(dirName)
    
    
    
    for File in FileList:
        fullname = os.path.join(dirName,File).strip()
        if os.path.isfile(fullname):
            fName,current_extension = os.path.splitext(fullname)
            sName = os.path.basename(fullname)
            current_extension = current_extension.lower()[1:]
            if current_extension in ext_count:
                ext_count[current_extension] = ext_count[current_extension] + 1
            else:
                ext_count[current_extension] = 1
                if not current_extension in ext_header and len(current_extension) >= 1:
                    ext_header.append(current_extension)
                
            if current_extension in video_ext:
                print('Getting info for {0}'.format(fullname))
                try:
                    probe = ffmpeg.probe(fullname,cmd=FFPROBE)
                    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                    audio_stream =  next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                    
                    if video_stream is not None:
                        
                        for video_info in video_info_list: 
                            if video_info in video_stream.keys():
                                if video_info == 'duration':
                                    run_time[video_info] = humanize_time(int(round(float(video_stream['duration']))))
                                else:
                                    run_time[video_info] = video_stream[video_info]
                                
                               
                        
                    if audio_stream is not None:
                        for audio_info in audio_info_list:
                            if audio_info in audio_stream.keys():
                                run_time[audio_info] = audio_stream[audio_info]
                                
                    
                    
                except ffmpeg.Error as e:
                    print('Error {0} Skipping {1}'.format(skipped,fullname))
                    skipped = skipped + 1
                    run_time['status']='skipped'
   
                            
            counter += 1
    return Counter(ext_count).most_common(),counter,run_time


def CheckDir(dir,check_dir):
    check_results = {'_id': False, '_video': False, '_2257': False, '_pix': False, '_movie' : False}
    check_list = os.listdir(dir)
    for each_dir in check_list:
        
        if os.path.isdir(os.path.join(dir,each_dir)):
            #print(os.path.join(dir,each_dir))
            for check in check_dir:
                #print('Check {0} in {1}'.format(check,each_dir))
                if check in each_dir.lower():
                    check_results[check] = True
                 
                
            
    #print('Results {0}'.format(check_results))
    
    return check_results   

def main():
    # Define Variables here:
    count = 10
    processed = 0
    skipped = 0
    worksheet_scenes_header = []
    row = 0
    col = 0
    
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(outputfile)
    worksheet_scenes = workbook.add_worksheet('scenes')
    worksheet_runtime = workbook.add_worksheet('runtime')
    
    
    for element in scenes_header:
        worksheet_scenes.write(row,col,element)
        col += 1
    row += 1
    
    
    #Get list of directories
    for listofDir in dir_list:
        listofDir = prefix + listofDir
        directories = getListOfDirectories(listofDir)
        directories = sorted(directories)
        for directory in directories:
            
            print('Eval {0}'.format(directory))
            
            results = CheckDir(directory,check_dir)
            worksheet_scenes.write(row,scenes_header.index('edge_id'),studio + str(count).zfill(4))
            worksheet_scenes.write(row,scenes_header.index('directory'),directory)
            worksheet_scenes.write(row,scenes_header.index('title'),os.path.split(directory)[1])
            splits = False
            for mysplit in split_chars:              
                if mysplit in directory:
                    talent = os.path.split(directory)[1].split(mysplit)[0]
                    splits = True
                if not splits:
                    talent = os.path.split(directory)[1]
            worksheet_scenes.write(row,scenes_header.index('talent'),talent)
            for key in results:
                print(key,results)
                worksheet_scenes.write(row,scenes_header.index(key),results[key])
            row += 1
            count += 10    
            
        
        
        
#         subdirectories =  getListOfDirectories(directory)
#         for subdirectory in subdirectories:
#             for check in check_dir:
#                 if check in subdirectory:
#                     print('Check {0} Subdirectory {1}'.format(check,subdirectory))
#                     ext_results,ext_count, file_runtime = CountFiles(subdirectory)
#                     if ext_count > 0:
#                         print('Dir: {0} Results: {1}, Counter{2}, RunTime {3}'.format(subdirectory,ext_results,ext_count,file_runtime))
#                         if len(file_runtime) > 0:
#                             print(type(subdirectory),type(file_runtime))
#                             file_info[subdirectory]=file_runtime
        
            
    workbook.close()  
    

if __name__ == '__main__':
    main()