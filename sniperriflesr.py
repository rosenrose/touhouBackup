import os
import re
import urllib.request
import requests
import time
import bs4
import sys
sys.path.append("C:/users/crazy/pictures/python")
from bs4 import BeautifulSoup
from replaceSpecialCh import replaceSpecialCh

url = "http://blog.daum.net/_blog/BlogTypeView.do?blogid=0qN5Q&articleno"
articleUrl = "http://blog.daum.net/_blog/hdn/ArticleContentsView.do?blogid=0qN5Q&articleno"
path = "D:/Touhou/doujin/sniperriflesr"
logfile = "log.log"
html_footer = "\n</body>\n</html>"
catIDList = [3,5,6,7,8,32,38,46,50,51,52,104,105,114,115,117,118,119,122,134,141,156,161,185,204,210,211,212,216,384,385,386,387,388,389,390,391,432,433]
codeRegex = re.compile('[0-9]*')

def writeLog(msg):
	with open("%s/%s"%(path,logfile),'a',encoding="utf-8-sig") as a:
		a.write(msg)
		
def sniperriflesr(codeList):
	for code in codeList:
		print("%d start" %(code))
		response = requests.get("%s=%d" %(url,code))
		soup = BeautifulSoup(response.content,'html.parser')

		notes = soup.find_all(text=lambda text:isinstance(text,bs4.element.Comment))
		for note in notes: note.extract()

		main = soup.find('div',class_='articlePrint')
		if main is None:
			writeLog("%d does not exist\n" %(code))
			continue

		catID = main.find('span',class_='cB_Folder')
		if catID is None:
			writeLog("%d out of category\n" %(code))
			continue

		catID = catID.find('a')['href']
		catID = codeRegex.findall(catID.split('&')[1])[-2]
		if not int(catID) in catIDList:
			writeLog("%d out of category\n" %(code))
			continue
		category = main.find('span',class_='cB_Folder').find('a').text

		articleResponse = requests.get("%s=%d" %(articleUrl,code))
		articleSoup = BeautifulSoup(articleResponse.content,'html5lib')
		if not articleSoup.find('img',class_='txc-image'):
			writeLog("%d has no image\n" %(code))
			continue
		
		title = soup.find('title').text
		pos1 = title.find('東方 Project')
		if pos1 != -1:
			pos2 = title.find('-',pos1)
			if pos2 != -1:
				title = title[pos2+1:].strip()
			else:
				pos2 = title.rfind('-',0,pos1)
				title = title[:pos2].strip()
		date = main.find('span',class_='cB_Tdate').text

		titleWin = replaceSpecialCh(title)
		doc = "%s/%d" %(path,code)
		if not os.path.isdir("%s_%s" %(doc,titleWin)):
			try:
				os.mkdir("%s_%s" %(doc,titleWin))
			except:
				writeLog("Making \'%s_%s\' folder fail\n" %(doc,titleWin))
				continue

		try:
			f = open(doc+".html","w",encoding="utf-8-sig")
		except:
			writeLog("Making \'%s\' file fail\n" %(title))
			f.close()
			continue

		html_header = "<html>\n<head>\n\t<title>%s</title>\n</head>\n<body>\n\t<h2>%s</h2><br/>\n" %(title,title)
		f.write(html_header)
		f.write("<div class=\"category\">%s</div><br/>\n" %(category))
		f.write("<div class=\"date\">%s</div><br/>\n" %(date))

		article = articleSoup.find('div',id='contentDiv')
		for link in article.find_all("link"): link.extract()
		for style in article.find_all("style"): style.extract()
		p = article.find_all("img")
		f.write("<div class=\"article\">\n")
		
		i=0
		while(i < len(p)):
			if p[i].has_attr('data-filename'):
				fileExt = p[i]["data-filename"].split('.')[-1]
			else:
				fileExt = "jpg"
			imgSrc = p[i]["src"].replace("image","original")
			fileName = "%03d.%s" %(i+1,fileExt)
				
			try:
				imgBuf = urllib.request.urlopen(imgSrc)
			except:
				writeLog("%d_%s/%s open fail\n" %(code,titleWin,fileName))
				continue

			try:
				imgBuf = imgBuf.read()
			except:
				writeLog("%d_%s/%s reading fail\n" %(code,titleWin,fileName))
				continue

			try:
				imgFile = open("%s_%s/%s" %(doc,titleWin,fileName),"wb")
			except:
				writeLog("Making %d_%s/%s fail\n" %(code,titleWin,fileName))
				continue
			else:
				imgFile.write(imgBuf)
			finally:
				imgFile.close()
				
			p[i].attrs["src"] = "%d_%s/%s" %(code,titleWin,fileName)
			for attr in list(p[i].attrs):
				if attr != "src":
					del p[i][attr]
			i+=1
		for t in article.find_all("p"):
			for attr in list(t.attrs):
				del t[attr]
		f.write(str(article))
		f.write("</div><br/>\n")
		
		f.write("<div class=\"another\">\n")
		f.write("\t<p>'%s' 카테고리의 다른 글</p>\n\t\t<ul>\n" %(category))
		another = soup.find('div',class_='cContentCateMore').find_all('li')
		for i in another:
			anotherTitle = i.find('a')['title']
			pos1 = anotherTitle.find('東方 Project')
			if pos1 != -1:
				pos2 = anotherTitle.find('-',pos1)
				if pos2 != -1:
					anotherTitle = anotherTitle[pos2+1:].strip()
				else:
					pos2 = anotherTitle.rfind('-',0,pos1)
					anotherTitle = anotherTitle[:pos2].strip()

			if str(i.find('a')).find("href") != -1:
				anotherCode = i.find('a')['href']
				anotherCode = codeRegex.findall(anotherCode.split('&')[1])[-2]
				f.write("\t\t\t<li><a href=\"%s.html\">%s</a></li>\n" %(anotherCode,anotherTitle))
			else:
				f.write("\t\t\t<li>%s</li>\n" %(anotherTitle))
		f.write("\t\t</ul>\n</div><br/>\n")

		comment = soup.find('div',class_="opinionListBox")
		fulTag = soup.new_tag("ul")
		fliTag = soup.new_tag("li",**{'class':'firstCmt'})
		fswitch = False
		sulTag = soup.new_tag("ul")
		sliTag = soup.new_tag("li",**{'class':'secondCmt'})
		sswitch = False
		while True:
			if isinstance(comment.contents[0],bs4.element.Tag):
				if comment.contents[0].has_attr('class'):
					if comment.contents[0]['class'][0] == "opinionListMenu":
						if fswitch:
							if sswitch:
								sulTag.append(sliTag)
								fliTag.append(sulTag)
								sulTag = soup.new_tag("ul")
								sswitch = False
							fulTag.append(fliTag)
						else:
							fswitch = True
						fliTag = soup.new_tag("li",**{'class':'firstCmt'})

					elif comment.contents[0]['class'][0] == "opinionListMenuRe":
						if sswitch:
							sulTag.append(sliTag)
						else:
							sswitch = True
						sliTag = soup.new_tag("li",**{'class':'secondCmt'})

				if comment.contents[0].has_attr('type') and (comment.contents[0]['type'] == "hidden"):
					if sswitch:
						sulTag.append(sliTag)
						fliTag.append(sulTag)
					if fswitch:
						fulTag.append(fliTag)
						comment.insert(0,fulTag)
					break;
			if not sswitch:
				fliTag.append(comment.contents[0])
			else:
				sliTag.append(comment.contents[0])
		
		firstCmt = comment.find_all('li',class_="firstCmt")
		for i in firstCmt:
			i.find('ul',class_="opinionListMenu").name = 'div'
			if i.find('li',class_="icon") is not None:
				i.find('li',class_="icon").name = 'div'
			i.find('li',class_="fl").name = 'div'
			if i.find('li',class_="sDateTime") is not None:
				i.find('li',class_="sDateTime").name = 'div'
			if i.find('li',class_="opinionBtn") is not None:
				i.find('li',class_="opinionBtn").decompose()

			if i.find('li',class_="secondCmt") is not None:
				secondCmt = i.find_all('li',class_="secondCmt")
				for j in secondCmt:
					j.find('ul',class_="opinionListMenuRe").name = 'div'
					j.find('li',class_="reIcon").name = 'div'
					if j.find('li',class_="icon") is not None:
						j.find('li',class_="icon").name = 'div'
					if j.find('li',class_="fl") is not None:
						j.find('li',class_="fl").name = 'div'
					if j.find('li',class_="sDateTime") is not None:
						j.find('li',class_="sDateTime").name = 'div'
					if j.find('li',class_="opinionBtn") is not None:
						j.find('li',class_="opinionBtn").decompose()

		for i in comment.find_all("input",type="hidden"):
			i.decompose()
		comment["class"] = "comment"
		f.write(str(comment))
		
		f.write(html_footer)
		f.close()
		print("%d end" %(code))
		time.sleep(5)


for i in range(1,len(sys.argv)):
	if sys.argv[i].find('-') == -1:
		sniperriflesr([int(sys.argv[i])])
	else:
		c1 = sys.argv[i].split('-')[0]
		c2 = sys.argv[i].split('-')[1]
		sniperriflesr(range(int(c1),int(c2)+1))