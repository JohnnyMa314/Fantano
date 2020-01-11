from __future__ import unicode_literals

import os
import pandas as pd
import re
import subprocess
import time
import csv
import requests
import youtube_dl
from bs4 import BeautifulSoup

# returns a list of links to reviews
def get_review_links(webpage):
	# open page and select links
	page = requests.get(webpage)
	soup = BeautifulSoup(page.content, 'html.parser')

	# select review headers, add to list
	reviews = []
	elms = soup.select("h1.entry-title a")
	for i in elms:
		reviews.append(i.attrs["href"])

	return reviews


# return url for the next page of reviews
def next_page(webpage):
	# sometimes page doesn't load properly
	loaded = False
	while not loaded:
		page = requests.get(webpage)
		soup = BeautifulSoup(page.content, 'html.parser')
		try:
			next_page = soup.select('div.older a')[0].attrs['href']
			loaded = True
		except Exception:
			continue

	return next_page

# get youtube link off of review page
def get_yt_link(webpage):
	loaded = False
	tries = 0
	ytlink = ''
	# sometimes page doesn't load properly
	while not ytlink:
		page = requests.get(webpage)
		soup = BeautifulSoup(page.content, 'html.parser')

		if tries > 10:
			return ytlink

		# try getting ytlink
		try:
			element = soup.find("div", class_="video-block")  # get block with embedded yt video
			text_block = element['data-block-json']  # get tag with link
			ytlink = re.search(r'url":"(.*?)","', text_block).group(1)  # regex to capture link pattern
		except Exception:
			pass

		# second method of getting ytlink, for older pages
		try:
			element = soup.find('div', class_='sqs-block-content') # get block with embedded yt video
			ytlink = re.search(r'src="(.*?)"', str(element)).group(1) # regex to capture link pattern
		except Exception:
			tries += 1
			continue

	return ytlink

# get tags off of review page
def get_tags(webpage):
	tags = []
	tries = 0
	while not tags and tries < 100:
		page = requests.get(webpage)
		soup = BeautifulSoup(page.content, 'html.parser')

		# select tags
		elms = soup.select('span.entry-tags a')

		# get all tags
		for tag in elms:
			tags.append(tag.text)

		# quit out if too many tries, no tags
		tries += 1

	return tags

def vtt_to_csv(vtt):
	for file in os.listdir(os.getcwd()):
		if file.endswith('.vtt'):
			for caption in webvtt.read(os.path.join(os.getcwd(), file)):
				print(caption.start)
				print(caption.end)
				print(caption.text)

# download youtube video and autogen captions using youtube_dl
def download_ytlinks(ytlink):

	ydl_opts = {'writeautomaticsub': 'writeautomaticsub',
	            'subtitlesformat': 'srt',
	            'writeinfojson': 'writeinfojson'}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download([ytlink])

def extract_audio(file, review_folder):
	if file.endswith('.webm'):
		command = "ffmpeg -i " + os.path.join(review_folder, file) + " -y -vn -acodec pcm_s16le -ar 44100 -ac 2 " + os.path.join(review_folder, file.replace(file[-5:], ".wav"))
	else:
		command = "ffmpeg -i " + os.path.join(review_folder, file) + " -y -vn -acodec pcm_s16le -ar 44100 -ac 2 " + os.path.join(review_folder, file.replace(file[-4:], ".wav"))
	subprocess.call(command, shell=True)

def main():
	base_url = 'https://www.theneedledrop.com'
	base_dir = '/Users/johnnyma/Desktop/Projects/Fantano'
	out_dir = '/Volumes/exHD/fantano/'
	page = '/articles/category/Reviews'

	i = 0
	invalids = []
	review_pages = []

	while i < 300:  # 284 pages as of 1-1-20
		print("retrieving review page: " + str(i))
		reviews = get_review_links(base_url + page)
		for link in reviews:
			review_pages.append(base_url + link)  # get reviews for a page

		# get next page of reviews
		page = next_page(base_url + page)
		i += 1

		time.sleep(1)

	# save tags to csv.
	os.chdir(base_dir)
	with open('review_tags.csv', 'w', newline='') as csvFile:
		writer = csv.writer(csvFile)
		# write header, generic tagN columns.
		writer.writerow(['review_name', 'review_url', 'has_video', 'has_subs', 'has_json'] + ['tag' + str(i) for i in range(0,40)])

		for link in review_pages:
			# print index and wait
			time.sleep(1)
			print(review_pages.index(link))
			# get name of review from url
			review_name = re.findall(r'([^/]+$)', link)[0]
			print(review_name)

			# get tags from review page
			tag = get_tags(link)
			print(tag)

			# create a folder for each review
			review_folder = os.path.join(out_dir, 'reviews', review_name)
			if not os.path.exists(review_folder):
				os.mkdir(review_folder)

			# get embedded ytlink from review page
			os.chdir(review_folder)
			ytlink = get_yt_link(link).strip('/')

			# if a link is found, download out
			if ytlink != '':
				try:
					download_ytlinks(ytlink)
				except Exception:
					invalids.append(review_name)

			has_vtt, has_video, has_json = False, False, False
			for file in os.listdir(review_folder):
				# rename folder to get rid of white spaces.
				os.rename(os.path.join(review_folder, file), os.path.join(review_folder, file.replace('-', '.').replace(' ', '.').replace('(', '.').replace(')', '.').replace('\'', '')))

			for file in os.listdir(review_folder):
				if file.endswith(('.mp4', '.webm', '.mkv')):
					has_video = True
					extract_audio(file, review_folder)
				if file.endswith('.vtt'):
					has_vtt = True
				if file.endswith('.json'):
					has_json = True

			# write tag into csv
			writer.writerow([review_name, link, has_video, has_vtt, has_json] + tag)

if __name__ == '__main__':
	main()
