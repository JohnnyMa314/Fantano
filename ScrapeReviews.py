import os
import re
import subprocess
import time
import youtube_dl
import requests
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
	# sometimes page doesn't load properly
	while not loaded:
		page = requests.get(webpage)
		soup = BeautifulSoup(page.content, 'html.parser')
		try:
			element = soup.find("div", class_="video-block")  # get block with embedded yt video
			text_block = element['data-block-json']  # get tag with link

			ytlink = re.search(r'url":"(.*?)","', text_block).group(1)  # regex to capture link pattern
			loaded = True
		except Exception:
			continue

	return ytlink

# download youtube link using youtube_dl
def download_ytlinks(ytlink):
	ydl_opts = {'format': 'bestvideo/best',
	            'automatic_captions': 'writeautomaticsub'}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download([ytlink])


def main():
	base_url = 'https://www.theneedledrop.com'
	page = '/articles/category/Reviews'

	reviews = []
	i = 0

	# get URLS for all reviews on website
	while i < 1:
		print('going ')
		print(i)
		page_reviews = get_review_links(base_url + page)  # get reviews for a page
		for link in page_reviews:
			reviews.append(link)  # add links to list
		time.sleep(2)
		page = next_page(base_url + page)  # get next page
		time.sleep(2)
		i += 1

	ytlinks = []
	i = 0
	for review_page in reviews:
		link = get_yt_link(base_url + review_page)
		ytlinks.append(link)
		time.sleep(2)
		i += 1
		print(i)

	download_ytlinks(ytlink=ytlinks[0])

if __name__ == '__main__':
	main()
