# -*- coding: utf-8 -*-
import os, sys, re
import urllib, urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import unicodedata
import io
import gzip
import time
import simplejson as json
import datetime
import string
import requests
from requests_toolbelt.adapters.source import SourceAddressAdapter
from urllib.parse import urlencode, quote_plus
import html
import csv
import unidecode
from socket import timeout

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.response.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302

def unicodefraction_to_decimal(v):
    fracPattern = re.compile("(\d*)\s*([^\s\.\,;a-zA-Z]+)")
    fps = re.search(fracPattern, v)
    if fps:
        fpsg = fps.groups()
        wholenumber = fpsg[0]
        fraction = fpsg[1]
        decimal = round(unicodedata.numeric(fraction), 3)
        if wholenumber:
            decimalstr = str(decimal).replace("0.", ".")
        else:
            decimalstr = str(decimal)
        value = wholenumber + decimalstr
        return value
    return v

class AsteBoettoBot(object):
    htmltagPattern = re.compile("\<\/?[^\<\>]*\/?\>", re.DOTALL)
    pathEndingWithSlashPattern = re.compile(r"\/$")
    endspacePattern = re.compile("\s+$", re.DOTALL)
    beginspacePattern = re.compile("^\s+")
    emptyspacePattern = re.compile("^\s*$")
    commapattern = re.compile(",\s*")
    brPattern = re.compile("<br\s*\/?>", re.IGNORECASE)
    yearPattern = re.compile("(\d{4})", re.DOTALL)

    htmlEntitiesDict = {'&nbsp;' : ' ', '&#160;' : ' ', '&amp;' : '&', '&#38;' : '&', '&lt;' : '<', '&#60;' : '<', '&gt;' : '>', '&#62;' : '>', '&apos;' : '\'', '&#39;' : '\'', '&quot;' : '"', '&#34;' : '"'}
    
    def __init__(self, auctionurl, auctionnumber):
        self.opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler())
        self.no_redirect_opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(), NoRedirectHandler())
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language' : 'en-GB,en-US;q=0.9,en;q=0.8', 'Accept-Encoding' : 'gzip, deflate', 'Connection' : 'keep-alive', 'Host' : 'www.phillips.com'}
        self.httpHeaders['Cache-Control'] = "max-age=0"
        self.httpHeaders['Upgrade-Insecure-Requests'] = "1"
        self.httpHeaders['Sec-Fetch-Dest'] = "document"
        self.httpHeaders['Sec-Fetch-Mode'] = "navigate"
        self.httpHeaders['Sec-Fetch-Site'] = "same-origin"
        self.httpHeaders['Sec-Fetch-User'] = "?1"
        self.httpHeaders['host'] = "www.asteboetto.it"
        self.httpHeaders['Cookie'] = ""
        self.homeDir = os.getcwd()
        #self.requestUrl = self.__class__.startUrl
        self.requestUrl = auctionurl
        parsedUrl = urlparse(self.requestUrl)
        self.baseUrl = parsedUrl.scheme + "://" + parsedUrl.netloc + "/"
        print(self.requestUrl)
        self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
        self.pageResponse = None
        self.requestMethod = "GET"
        self.postData = {}
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
            headers = self.pageResponse.getheaders()
            #print(headers)
            if "Location" in headers:
                self.requestUrl = headers["Location"]
                self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
                try:
                    self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                except:
                    print ("Couldn't fetch page due to limited connectivity. Please check your internet connection and try again1. %s"%sys.exc_info()[1].__str__())
                    sys.exit()
        except:
            print ("Couldn't fetch page due to limited connectivity. Please check your internet connection and try again2. %s"%sys.exc_info()[1].__str__())
            sys.exit()
        self.httpHeaders["Referer"] = self.requestUrl
        self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
        self.httpHeaders["Cookie"] = self.sessionCookies
        # Initialize the account related variables...
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        #print(self.currentPageContent)
        self.currentPageNumber = 1 # Page number of the page that is currently being read.
        self.data = {'auction_house_name': '', 'auction_location' : '', 'auction_num' : '', 'auction_start_date' : '', 'auction_end_date' : '', 'auction_name' : '', 'lot_num' : '', 'sublot_num' : '', 'price_kind' : '', 'price_estimate_min' : '', 'price_estimate_max' : '', 'price_sold' : '', 'artist_name' : '', 'artist_birth' : '', 'artist_death' : '', 'artist_nationality' : '', 'artwork_name' : '', 'artwork_year_identifier' : '', 'artwork_start_year' : '', 'artwork_end_year' : '', 'artwork_materials' : '', 'artwork_category' : '', 'artwork_markings' : '', 'artwork_edition' : '', 'artwork_description' : '', 'artwork_measurements_height' : '', 'artwork_measurements_width' : '', 'artwork_measurements_depth' : '', 'artwork_size_notes' : '', 'auction_measureunit' : '', 'artwork_condition_in' : '', 'artwork_provenance' : '', 'artwork_exhibited' : '', 'artwork_literature' : '', 'artwork_images1' : '', 'artwork_images2' : '', 'artwork_images3' : '', 'artwork_images4' : '', 'artwork_images5' : '', 'image1_name' : '', 'image2_name' : '', 'image3_name' : '', 'image4_name' : '', 'image5_name' : '', 'lot_origin_url' : ''}
        self.saleno = auctionnumber
        self.auctiondate = ""
        self.auctiontitle = ""
        self.auction_number = ""

    
    def _decodeGzippedContent(cls, encoded_content):
        response_stream = io.BytesIO(encoded_content)
        decoded_content = ""
        try:
            gzipper = gzip.GzipFile(fileobj=response_stream)
            decoded_content = gzipper.read()
        except: # Maybe this isn't gzipped content after all....
            decoded_content = encoded_content
        decoded_content = decoded_content.decode('utf-8', 'ignore')
        return(decoded_content)

    _decodeGzippedContent = classmethod(_decodeGzippedContent)


    def _getCookieFromResponse(cls, lastHttpResponse):
        cookies = ""
        responseCookies = lastHttpResponse.getheader("Set-Cookie")
        pathPattern = re.compile(r"Path=/;", re.IGNORECASE)
        domainPattern = re.compile(r"Domain=[^;,]+(;|,)", re.IGNORECASE)
        expiresPattern = re.compile(r"Expires=[^;]+;", re.IGNORECASE)
        maxagePattern = re.compile(r"Max-Age=[^;]+;", re.IGNORECASE)
        samesitePattern = re.compile(r"SameSite=[^;]+;", re.IGNORECASE)
        securePattern = re.compile(r"secure;?", re.IGNORECASE)
        httponlyPattern = re.compile(r"HttpOnly;?", re.IGNORECASE)
        if responseCookies and responseCookies.__len__() > 1:
            cookieParts = responseCookies.split("Path=/")
            for i in range(cookieParts.__len__()):
                cookieParts[i] = re.sub(domainPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(expiresPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(maxagePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(samesitePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(securePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(pathPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(httponlyPattern, "", cookieParts[i])
                cookieParts[i] = cookieParts[i].replace(",", "")
                cookieParts[i] = re.sub(re.compile("\s+", re.DOTALL), "", cookieParts[i])
                cookies += cookieParts[i]
        cookies = cookies.replace(";;", ";")
        return(cookies)

    _getCookieFromResponse = classmethod(_getCookieFromResponse)


    def getPageContent(self):
        try:
            return(self.pageResponse.read())
        except:
            return(b"")
            #return bytes("".encode())
    

    def formatDate(cls, datestr):
        mondict = {'January' : '01', 'February' : '02', 'March' : '03', 'April' : '04', 'May' : '05', 'June' : '06', 'July' : '07', 'August' : '08', 'September' : '09', 'October' : '10', 'November' : '11', 'December' : '12' }
        mondict2 = {'Jan' : '01', 'Feb' : '02', 'Mar' : '03', 'Apr' : '04', 'May' : '05', 'Jun' : '06', 'Jul' : '07', 'Aug' : '08', 'Sep' : '09', 'Oct' : '10', 'Nov' : '11', 'Dec' : '12' }
        mondict3 = {'jan.' : '01', 'fév.' : '02', 'mar.' : '03', 'avr.' : '04', 'mai.' : '05', 'jui.' : '06', 'jul.' : '07', 'aoû.' : '08', 'sep.' : '09', 'oct.' : '10', 'nov.' : '11', 'déc.' : '12' }
        mondict4 = {'Janvier' : '01', 'Février' : '02', 'Mars' : '03', 'Avril' : '04', 'Mai' : '05', 'Juin' : '06', 'Juillet' : '07', 'Août' : '08', 'Septembre' : '09', 'Octobre' : '10', 'Novembre' : '11', 'Décembre' : '12'}
        datestrcomponents = datestr.split(" ")
        if not datestr:
            return ""
        dd = datestrcomponents[0]
        mm = '01'
        datestrcomponents[1] = datestrcomponents[1].capitalize()
        if datestrcomponents[1] in mondict.keys():
            mm = mondict[datestrcomponents[1]]
        else:
            try:
                mm = mondict2[datestrcomponents[1]]
            except:
                pass
        yyyy = datestrcomponents[2]
        yearPattern = re.compile("\d{4}")
        if not re.search(yearPattern, yyyy):
            yyyy = "2021"
        retdate = mm + "/" + dd + "/" + yyyy
        return retdate
    formatDate = classmethod(formatDate)


    def fractionToDecimalSize(self, sizestring):
        sizestringparts = sizestring.split("x")
        if sizestringparts.__len__() < 1:
            sizestringparts = sizestring.split("by")
        unitPattern = re.compile("(\s*(in)|(cm)\s*$)", re.IGNORECASE)
        ups = re.search(unitPattern, sizestringparts[-1])
        unit = ""
        if ups:
            upsg = ups.groups()
            unit = upsg[0]
        sizestringparts[-1] = unitPattern.sub("", sizestringparts[-1])
        decimalsizeparts = []
        beginspacePattern = re.compile("^\s+")
        endspacePattern = re.compile("\s+$")
        for szpart in sizestringparts:
            szpart = beginspacePattern.sub("", szpart)
            szpart = endspacePattern.sub("", szpart)
            d_szpart = unicodefraction_to_decimal(szpart)
            decimalsizeparts.append(d_szpart)
        decimalsize = " x ".join(decimalsizeparts)
        decimalsize += " " + unit
        return decimalsize


    def getLotsFromPage(self):
        pageContent = self.currentPageContent
        soup = BeautifulSoup(pageContent, features="html.parser")
        alltitletag = soup.find("div", {'class' : 'cols-2'})
        if alltitletag is not None:
            titleh2tag = alltitletag.find("h2").renderContents().decode('utf-8')
            self.auctiontitle = titleh2tag
            dateh3tag = alltitletag.find("h3")
            if dateh3tag is not None:
                dateh3tag = dateh3tag.renderContents().decode('utf-8')
            self.auctiondate = dateh3tag
        
        print(self.auctiontitle)
        print(self.auctiondate)
        print(dateh3tag)
        
        lotdivtags = soup.find_all("div", {'style' : 'min-height:200px;width:40%;float:left;'})
        #print(lotdivtags.__len__())
        return lotdivtags


    def getDetailsPage(self, detailUrl):
        self.requestUrl = detailUrl
        self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
        self.pageResponse = None
        self.postData = {}
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
        except:
            print ("Error %s"%sys.exc_info()[1].__str__())
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return self.currentPageContent
    

    #unedited
    def getImagenameFromUrl(self, imageUrl):
        urlparts = imageUrl.split("/")
        imagefilepart = urlparts[-1]
        imagefilenameparts = imagefilepart.split("?")
        imagefilename = imagefilenameparts[0]
        return imagefilename
    

    def parseDetailPage(self, detailsPage, lotno, imagepath, artistname, artworkname, downloadimages):
        detailData = {}

        brPattern = re.compile("<br\s*\/?>", re.IGNORECASE)
        xPattern = re.compile("x")
        heightFounding = re.compile("\d+")
        romanpattern = re.compile("^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.IGNORECASE)
        htmltagPattern = re.compile("\<\/?[^\<\>]*\/?\>", re.DOTALL)

        soup = BeautifulSoup(detailsPage, features="html.parser")
        detailData['artwork_name'] = ""
        detailData['artwork_materials'] = ""
        detailData['artwork_exhibited'] = ""
        detailData['artwork_provenance'] = ""
        detailData['artwork_description'] = ""
        detailData['auction_measureunit'] = "cm"

        divTag = soup.find("div", {'id' : 'descrlotto'})
        if divTag is not None:
            divTag = divTag.renderContents().decode('utf-8')
            divTag = re.split(brPattern, divTag)
            if divTag.__len__() > 0:
                parsedivtag = re.split(",", divTag[0])
                detailData['artwork_name'] = parsedivtag[0].replace('"', "'")
                if parsedivtag.__len__() > 2:
                    detailData['artwork_materials'] = parsedivtag[1]
                if parsedivtag.__len__() > 1:
                    detailData['artwork_year'] = parsedivtag[-1]
                if divTag[-1].__len__() > 5:
                    artwork_measurements = re.split(xPattern, divTag[-1])
                    #if artwork_measurements.__len__() > 0:
                    detailData['artwork_size_notes'] = "x".join(artwork_measurements)

                    artwork_measurements_height = re.findall(heightFounding, artwork_measurements[0])
                    if artwork_measurements_height.__len__() > 0:
                        detailData['artwork_measurements_height'] = artwork_measurements_height[0]

                    if artwork_measurements.__len__() > 1:
                        artwork_measurements_width = re.findall(heightFounding, artwork_measurements[1])
                        if artwork_measurements_width.__len__() > 0:
                            detailData['artwork_measurements_width'] = artwork_measurements_width[0]
                        if artwork_measurements_width.__len__() > 1:
                            detailData['artwork_measurements_width'] = artwork_measurements_width[1]
                    else:
                        artwork_measurements_width = re.findall(heightFounding, artwork_measurements[0])
                        if artwork_measurements_width.__len__() > 0:
                            detailData['artwork_measurements_width'] = artwork_measurements_width[0]

        divTag2 = soup.find("div", {'id' : 'divdeslotto'})
        if divTag2 is not None:
            strongtag = divTag2.find_all("strong")
            if strongtag.__len__() > 1:
                strongtag = re.sub(htmltagPattern, "", strongtag[1].renderContents().decode('utf-8'))
                print(strongtag)
                detailData['price_sold'] = strongtag[:-2]
        
        allimagetags = soup.find_all("a", {'class' : 'zoom'})
        imgctr = 1
        for i in allimagetags:
            imagetagfinder = i.find("img")
            removingsrcatart = re.sub("/\.\./", "/", imagetagfinder['src'])
            imagesrc = "https://www.asteboetto.it" + removingsrcatart
            imagename = removingsrcatart

            if imgctr == 1:
                detailData['image1_name'] = imagename
                detailData['artwork_images1'] = imagesrc
            elif imgctr == 2:
                detailData['image1_name'] = imagename
                detailData['artwork_images1'] = imagesrc
            elif imgctr == 3:
                detailData['image1_name'] = imagename
                detailData['artwork_images1'] = imagesrc
                break
            imgctr += 1    

        return detailData


    #unedited
    def getImage(self, imageUrl, imagepath, downloadimages):
        imageUrlParts = imageUrl.split("/")
        imagefilename = imageUrlParts[-2] + "_" + imageUrlParts[-1]
        imagedir = imageUrlParts[-2]
        backslashPattern = re.compile(r"\\")
        if downloadimages == "1":
            pageRequest = urllib.request.Request(imageUrl, headers=self.httpHeaders)
            pageResponse = None
            try:
                pageResponse = self.opener.open(pageRequest)
            except:
                print ("Error: %s"%sys.exc_info()[1].__str__())
            try:
                imageContent = pageResponse.read()
                imagefilename = backslashPattern.sub("_", imagefilename)
                ifp = open(imagepath + os.path.sep + imagefilename, "wb")
                ifp.write(imageContent)
                ifp.close()
                return imagefilename
            except:
                print("Error: %s"%sys.exc_info()[1].__str__())
        return imagefilename
    

    def getInfoFromLotsData(self, lotslist, imagepath, downloadimages):
        baseUrl = "https://www.asteboetto.it/index.php/it/archivio-aste"
        info = []

        getLotNumber = re.compile("Lotto", re.IGNORECASE)

        matcatdict_en = {}
        matcatdict_fr = {}
        with open("/mnt/d/ArtBider_Internship/fineart_materials.csv", newline='') as mapfile:
            mapreader = csv.reader(mapfile, delimiter=",", quotechar='"')
            for maprow in mapreader:
                matcatdict_en[maprow[1]] = maprow[3]
                matcatdict_fr[maprow[2]] = maprow[3]
        mapfile.close()
        for lotdiv in lotslist:
            data = {}
            data['auction_num'] = self.saleno
            detailUrl = ""
            lotno = ""
            artistname, artworkname = "", ""
            data['lot_num'] = ""
            data['lot_origin_url'] = ""
            data['price_estimate_min'] = ""
            data['price_estimate_max'] = ""
            data['price_sold'] = ""
            data['artist_name'] = ""
            data['artwork_name'] = ""
            data['artwork_materials'] = ""
            data['artwork_size_notes'] = ""

            lotNumberSpanTag = lotdiv.find("span", {'style' : 'font-weight:bold;'}).renderContents().decode('utf-8')
            lotNumberSpanTag = re.split(getLotNumber, lotNumberSpanTag)
            data['lot_num'] = lotNumberSpanTag[1]
            lotno = lotNumberSpanTag[1].replace(" ", "")
            detailUrl = baseUrl + "?id=135&codAsta=2401C" + "&Lotto={}".format(lotno) +"&ProgrLotto=0"
            print(detailUrl)
            data['lot_origin_url'] = detailUrl

            if detailUrl == "":
                continue
            detailsPageContent = self.getDetailsPage(detailUrl)
            detailData = self.parseDetailPage(detailsPageContent, lotno, imagepath, data['artist_name'], data['artwork_name'], downloadimages)
            for k in detailData.keys():
                data[k] = detailData[k]
            
            if 'artwork_materials' in data.keys() and 'artwork_category' not in data.keys():
                materials = str(data['artwork_materials'])
                materialparts = materials.split(" ")
                catfound = 0
                for matpart in materialparts:
                    if matpart in ['in', 'on', 'of', 'the', 'from']:
                        continue
                    try:
                        matPattern = re.compile(matpart, re.IGNORECASE|re.DOTALL)
                        for enkey in matcatdict_en.keys():
                            if re.search(matPattern, enkey):
                                data['artwork_category'] = matcatdict_en[enkey]
                                catfound = 1
                                break
                        for frkey in matcatdict_fr.keys():
                            if re.search(matPattern, frkey):
                                data['artwork_category'] = matcatdict_fr[frkey]
                                catfound = 1
                                break
                        if catfound:
                            break
                    except:
                        pass
            withdrawnPattern = re.compile("withdrawn", re.IGNORECASE|re.DOTALL)
            data['price_kind'] = "euro"
            if ('price_sold' in data.keys() and re.search(withdrawnPattern, data['price_sold'])) or ('price_estimate_max' in data.keys() and re.search(withdrawnPattern, data['price_estimate_max'])):
                data['price_kind'] = "withdrawn"
            elif 'price_sold' in data.keys() and data['price_sold'] != "":
                data['price_kind'] = "price realized"
            elif 'price_estimate_max' in data.keys() and data['price_estimate_max'] != "":
                data['price_kind'] = "estimate"
            else:
                pass
            if 'price_sold' not in data.keys() or data['price_sold'] == "":
                data['price_sold'] = ""
            data['auction_name'] = self.auctiontitle
            data['auction_location'] = "Genova"
            data['auction_start_date'] = self.auctiondate
            data['auction_house_name'] = "Aste Boetto"
            info.append(data)
        return info


    

"""
[
'auction_house_name', 'auction_location', 'auction_num', 'auction_start_date', 'auction_end_date', 'auction_name', 'lot_num', 'sublot_num', 'price_kind', 'price_estimate_min', 'price_estimate_max', 'price_sold', 'artist_name', 'artist_birth', 'artist_death', 'artist_nationality', 'artwork_name', 'artwork_year_identifier', 'artwork_start_year', 'artwork_end_year', 'artwork_materials', 'artwork_category', 'artwork_markings', 'artwork_edition', 'artwork_description', 'artwork_measurements_height', 'artwork_measurements_width', 'artwork_measurements_depth', 'artwork_size_notes', 'auction_measureunit', 'artwork_condition_in', 'artwork_provenance', 'artwork_exhibited', 'artwork_literature', 'artwork_images1', 'artwork_images2', 'artwork_images3', 'artwork_images4', 'artwork_images5', 'image1_name', 'image2_name', 'image3_name', 'image4_name', 'image5_name', 'lot_origin_url'
]
 """

def updatestatus(auctionno, auctionurl):
    auctionurl = auctionurl.replace("%3A", ":")
    auctionurl = auctionurl.replace("%2F", "/")
    pageurl = "http://216.137.189.57:8080/scrapers/finish/?scrapername=AsteBoetto&auctionnumber=%s&auctionurl=%s&scrapertype=2"%(auctionno, urllib.parse.quote(auctionurl))
    pageResponse = None
    try:
        pageResponse = urllib.request.urlopen(pageurl)
    except:
        print ("Error: %s"%sys.exc_info()[1].__str__())



if __name__ == "__main__":
    if sys.argv.__len__() < 5:
        print("Insufficient parameters")
        sys.exit()
    auctionurl = sys.argv[1]
    auctionnumber = sys.argv[2]
    csvpath = sys.argv[3]
    imagepath = sys.argv[4]
    downloadimages = 0
    convertfractions = 0
    if sys.argv.__len__() > 5:
        downloadimages = sys.argv[5]
    if sys.argv.__len__() > 6:
        convertfractions = sys.argv[6]
    
    asteBoetto= AsteBoettoBot(auctionurl, auctionnumber)
    fp = open(csvpath, "w")
    fieldnames = ['auction_house_name', 'auction_location', 'auction_num', 'auction_start_date', 'auction_end_date', 'auction_name', 'lot_num', 'sublot_num', 'price_kind', 'price_estimate_min', 'price_estimate_max', 'price_sold', 'artist_name', 'artist_birth', 'artist_death', 'artist_nationality', 'artwork_name', 'artwork_year_identifier', 'artwork_start_year', 'artwork_end_year', 'artwork_materials', 'artwork_category', 'artwork_markings', 'artwork_edition', 'artwork_description', 'artwork_measurements_height', 'artwork_measurements_width', 'artwork_measurements_depth', 'artwork_size_notes', 'auction_measureunit', 'artwork_condition_in', 'artwork_provenance', 'artwork_exhibited', 'artwork_literature', 'artwork_images1', 'artwork_images2', 'artwork_images3', 'artwork_images4', 'artwork_images5', 'image1_name', 'image2_name', 'image3_name', 'image4_name', 'image5_name', 'lot_origin_url']
    fieldsstr = ",".join(fieldnames)
    fp.write(fieldsstr + "\n")

    while True:
        soup = BeautifulSoup(asteBoetto.currentPageContent, features="html.parser")
        lotsdata = asteBoetto.getLotsFromPage()
        if lotsdata.__len__() == 0:
            break
        info = asteBoetto.getInfoFromLotsData(lotsdata, imagepath, downloadimages)


        lotctr = 0 
        for d in info:
            lotctr += 1
            for f in fieldnames:
                if f in d and d[f] is not None:
                    fp.write('"' + str(d[f]) + '",')
                else:
                    fp.write('"",')
            fp.write("\n")
    fp.close()
    updatestatus(auctionnumber, auctionurl)




#srivasanth
#python aste_boetto.py "https://www.asteboetto.it/index.php/it/archivio-aste?id=141&codAsta=2401C" 2401C "/mnt/d/ArtBider_Internship/Folders/aste_boetto/aste_boetto_2401C.csv" "/mnt/d/ArtBider_Internship/Folders/aste_boetto/2401C" 0 0

