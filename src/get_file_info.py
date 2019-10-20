#!/opt/local/bin/python3
def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)


import csv
import ffmpeg
import sys
import os

inputfile = sys.argv[1]
outputfile = sys.argv[2]
skipped = 0

video_info_list = ['width','height','duration','codec_name','display_aspect_ratio','bit_rate']
audio_info_list = ['codec_name','codec_long_name','bit_rate']


video_list = open(inputfile,'r')
video_data = open(outputfile, 'w')

nfs_prefix = '/edge/Finished'

print('Checking filenames from {0}'.format(nfs_prefix))

header_names = ['source', 'video_file_name', 'video_directory', 'edge_id', 'video_width', 'video_height', 'video_duration', 'video_codec_name', 'video_display_aspect_ratio', 'video_bit_rate', 'audio_codec_name', 'audio_codec_long_name', 'audio_bit_rate']
writer = csv.DictWriter(video_data, fieldnames=header_names) 
writer.writeheader()

video = video_list.readline()
while video:
    csv_output = {}
    print("{}".format(video.strip()))
    filename=video.strip()
    csv_output['source'] = filename
    csv_output['video_file_name'] = os.path.basename(filename)
    csv_output['video_directory'] = os.path.dirname(filename)
    csv_output['edge_id'] = os.path.basename(filename).split('_')[0]
  
    
  
    try:
        probe = ffmpeg.probe(nfs_prefix + filename)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream =  next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if video_stream is not None:
            for video_info in video_info_list:
                if video_info in video_stream.keys():
                    csv_output['video_' + video_info] = video_stream[video_info]
                    
            
        if audio_stream is not None:
            for audio_info in audio_info_list:
                if audio_info in audio_stream.keys():
                    csv_output['audio_' + audio_info] = audio_stream[audio_info]
    
        
        writer.writerow(csv_output)
        
        video = video_list.readline()
    except ffmpeg.Error as e:
        print('Error {0} Skipping {1}'.format(skipped,nfs_prefix + filename))
        skipped = skipped + 1
        #print(e.stderr, file=sys.stderr)
        
    
        
   
    video = video_list.readline()
    
    
    
   

#