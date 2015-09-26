import urllib, urllib2, subprocess, sys, json, datetime
from bs4 import BeautifulSoup

''' find the url for the episode we want '''

url = 'http://www.francetvinfo.fr/replay-jt/france-2/20-heures/'
response = urllib2.urlopen(url)
html = response.read()
soup = BeautifulSoup(html)
videolink = soup.find('section', {'class': 'first-element-jt'})
current_episode_link = videolink.a['href']

url = 'http://www.francetvinfo.fr' + current_episode_link
response = urllib2.urlopen(url)
html = response.read()
soup = BeautifulSoup(html)
link_to_json = soup.find('a', {'class': 'video'})
json_url = link_to_json['href']
# example of this url is
# http://info.francetelevisions.fr/?id-video=103668243@Info-web
# so find index of equal sign '=' and at sign '@'

equal_index = json_url.find('=')
at_index = json_url.find('@')
video_id = json_url[equal_index+1: at_index]

# get json object at this type of url
# http://webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=103668243&catalogue=Info-web

url = "http://webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=" + video_id + "&catalogue=Info-web"
response = urllib2.urlopen(url)
js = response.read()
jsonified = json.loads(js.decode('utf-8'))
m3u8_url = jsonified['videos'][1]['url']

response = urllib2.urlopen(m3u8_url)
config = response.read()

# write response to temp file so we can read last line of file
f = open('temp', 'w')
f.write(config)
f.close()

# read file into array, get last line which has highest res video
with open('temp') as f:
    content = f.readlines()
playlist = content[-1].strip()

# visit the 480p url and write the 250+ video pieces URL to a file
response = urllib2.urlopen(playlist).read()
f = open('temp', 'w')
f.write(response)
f.close()

# open file again and read into list
with open('temp') as f:
    content = f.readlines()

# now we have all the video pieces in one file
# and each line starts with http so we hit that url with wget
f = open('temp', 'w').close()
for line in content:
    if line.find('http') > -1:
        segment_index = line.find('segment')
        underscore_index = line.find('_')
        segment_number = line[segment_index+7: underscore_index]
        #command = "wget -O ./tempvideos/" + segment_number + " " + line.strip()
        #wget doesn't work any more, need to use urllib2
        response = urllib2.urlopen(line.strip())
        read_response = response.read()
        #write to a file in tempvideos
        f = open('tempvideos/' + segment_number, 'w')
        f.write(read_response)
        f.close()

        # write to a file that lists how many video chunks we have
        f = open('temp', 'a')
        f.write("file './tempvideos/" + segment_number + "'\n")
        f.close()
        #if int(segment_number) == 252:
        #print(command)
        #subprocess.call(command, shell=True)
        #print(line.strip())
        #print(segment_number)

# turn all the video parts into one complete mp4 file
file_name = "france2-" + str(datetime.datetime.now().month) + "-" + str(datetime.datetime.now().day)
command = "ffmpeg -f concat -i temp -bsf:a aac_adtstoasc -c copy " + file_name + ".mp4"
subprocess.call(command, shell=True)

# clear the tempvideos folder
command = "rm -R ./tempvideos/*"
subprocess.call(command, shell=True)

