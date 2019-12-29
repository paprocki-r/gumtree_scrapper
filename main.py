from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import time
import os
import requests
import re
import json

artist=""
city="warszawa"
URL_START='https://www.gumtree.pl'
ARTIST_URL="mieszkania-i-domy-sprzedam-i-kupie/warszawa"#re.sub("\s",+,artist)
OFFER_CHOICE="v1c9073l3200008"

scrapings_dir = './tmp'
	
def scrape_gumtree_page_n(n):
    print("I'm scrapping page {0}\n".format(n))
    current_time=int(time.time())
    pageURL='{0}/s-{1}/{2}/page-{3}/{4}p{5}'.format(URL_START,ARTIST_URL,city,n,OFFER_CHOICE,n)
    print(pageURL)
    savePath=os.path.join(scrapings_dir,"{0}.html".format(current_time))
    print(savePath)
    results=requests.get(pageURL)
    results_file=open(savePath,'a')
    with results_file:
        results_file.write(results.text)
    return savePath

def getAddressAndSize(href):
    address = None
    size = 0
    #open the href
    pageURL = '{0}{1}'.format(URL_START, href)
    results=requests.get(pageURL)
    gtsoup = BeautifulSoup(results.text)

    #parse the site and find google map - below there is more precise location

    gt_li=gtsoup.findAll('div', attrs={'class': 'map'})
    if gt_li[0].find('span',attrs={"class":"address"}) is not None:
        # address = node.find('span',attrs={"class":"address"}).contents[0]
        address = (gt_li[0].find('span',attrs={"class":"address"}).contents[0])
    
    attrs=gtsoup.findAll('div', attrs={'class': 'attribute'})
    try:
        size = (attrs[6].find('span',attrs={"class":'value'}).text)
    except:
        pass

    return address, size

def getLatLon(address):
    llat=0
    llong = 0   
    if(address): 
        from geopy.geocoders import Nominatim
        nom = Nominatim()
        try:
            n = nom.geocode(address)
            if(n is not None):
                llat = n.latitude
                llong = n.longitude
        except:
            print("error while getting geocode data")

    return str(llat), str(llong)

def html_parser(filename):
    gumtree_file=open(filename)
    gumtree_contents=gumtree_file.read()
    gtsoup=BeautifulSoup(gumtree_contents)
    master_list=[]
    gt_li=gtsoup.findAll('div', attrs={'class': 'tileV1'})
    print("============")

    for (i, node) in enumerate(gt_li):
        print("Processing ad number {0}\n".format(i))
        if len(node.contents) > 0:
            post_dict={}
            if node.findAll('a') is not None:
                post_dict['title']=node.findAll('a')[0].string             
                post_dict['href'] = node.findAll('a', attrs={'class': "href-link"})[0].get('href')
                post_dict['address'], post_dict['size'] = getAddressAndSize(post_dict['href'])

            if post_dict['address'] is not None:
                post_dict['lat'], post_dict['lon'] = getLatLon(post_dict['address'])
            if node.find('span',attrs={"class":"ad-price"}) is not None:
                post_dict['price'] = node.find('span',attrs={"class":"ad-price"}).contents[0].replace("\n", "").strip()
             
            # if node.findAll('span') is not None:
            #     post_dict['description']=node.findAll('span')[0].contents[0]
            # if node.find('h3',attrs={"class":"rs-ad-location"}) is not None:
            #     post_dict['location1']=node.find('h3',attrs={"class":"rs-ad-location-area"}).contents[0]
            # if node.find('span',attrs={"class":"rs-ad-location-suburb"}) is not None:
            #     post_dict['location2']=node.find('span',attrs={"class":"rs-ad-location-suburb"}).contents[0]
            # if node.find('div',attrs={"class":"rs-ad-date"}) is not None:
            #     post_dict['date']=node.find('div',attrs={"class":"rs-ad-date"}).contents[0]
            # anchors=node.findAll('a')
            # for node in anchors:
            #     if node.get("data-adid") is not None:
            #         post_dict['ad_id']=node.get('data-adid')
            if('price' in post_dict and (post_dict['lat']) !="0"):
                master_list.append(post_dict)
    return master_list
def scrapGumtree(n):
    for x in range(n):

        path = scrape_gumtree_page_n(x)
        data = html_parser(path)
        with open('data.json', 'a') as outfile:  
            json.dump(data, outfile)

#mamy zapisane lokalizacje ogloszeb - teraz wystarczy wczytac jsona i wyswietlic je na mapie z planowanymi stacjami metra i zaznaczonymi 500 stacjami
import folium 

def popupText(d_point):

    return "<a href=\"" + URL_START + d_point['href']  + "\">"  +str(d_point['size']) + 'm2 #' +d_point['price'] + ' # ' + d_point['title'] + "</a>"   

def makePointOnTheMap(d_point):
        marker = folium.Marker(location=[d_point['lat'], d_point['lon']],
                                radius=20,
                                weight=5,
                                popup=popupText(d_point))
        return marker

def showPointsOnTheMap():


    folium_map = folium.Map(location=[52.2256, 21.0030],
                        zoom_start=13,
                       )
    ## dzielnice 
    folium.GeoJson(
        'warszawa_dzielnice.geojson',
        name='geojson'
    ).add_to(folium_map)



    d=[
        [52.141039, 21.0323214], #sub station 1
        [52.2328098, 21.019067] #sub station 2
    ]

    #@TODO: add heatmap for the subway stations
    # from folium.plugins import HeatMap
    # HeatMap(d).add_to(folium_map)

    #add advertisements points
    with open('data.json', 'r') as json_file:  
        data = json.load(json_file)
        for d in data:
            print(d['lon'])
            print(d['lat'])
            if(d['lon'] is not None and d['lat'] is not None):
                marker = makePointOnTheMap(d)
                marker.add_to(folium_map)       
    

    folium_map.save("my_map2.html")

   

#scrapGumtree(10)
showPointsOnTheMap()
