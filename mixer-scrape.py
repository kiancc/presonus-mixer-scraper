# import libraries
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import os
from mixerSkus import skus
import time 
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

def main():
    url_root = "https://www.presonus.com/produits/fr/Mixing-Systems"
    url_list = grab_url(url_root)
    # iterates over each product page's tech specs
    print("~~~~~~~~~~~~~~~~~~~~~~~~Scraping!~~~~~~~~~~~~~~~~~~~~~~~~")
    for url in url_list:
        print("---------------------------------------------------------")
        print("https://www.presonus.com{}/caract-tech".format(url))
        # page = requests.get("https://www.presonus.com/produits/fr/Eris-E35/caract-tech")
        page = requests.get("https://www.presonus.com{}/caract-tech".format(url), verify=False)
        soup = BeautifulSoup(page.content, "html.parser")
        spec_tables = spec_table(soup)
        spec_cats = spec_cat(spec_tables)
        dict_ = dict_generator(spec_tables, spec_cats, url)
        pim_export(dict_, url)
        time.sleep(100)
    print("---------------------------------------------------------")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~Done!~~~~~~~~~~~~~~~~~~~~~~~~~~")


def grab_url(url_root):
    # grabs product branch names and puts it into a list
    url_list = []
    page1 = requests.get(url_root, verify=False)
    soup1 = BeautifulSoup(page1.content, "html.parser")
    soup1 = soup1.find("div", {"class": "container twocol product-category"})
    for a in soup1.find_all("a", href=True):
        url = a["href"]
        if "/produits/fr/" in url:
            if url not in url_list:
                url_list.append(url)

    return url_list


def spec_table(soup):
    spec_list = []
    # finds tech spec tables
    spec_tables = soup.find_all("table")
    # iterates through each tech spec features and adds to list
    for table in spec_tables:
        spec_list.append(table)

    return spec_list


def spec_cat(spec_tables):
    cat_list = []
    # appends categories to a list
    for table in spec_tables:
        cat = table.find("tr").text.strip()
        cat = cat.replace("/", "_")
        if (
            #cat == "Microphone Inputs"
            cat == "Mi crophone Preamplifier"
            or cat == "Microphone Preamplifier"
            or "Preamplifier" in cat
            or "Microphone" in cat
        ):
            cat = "Microphone Preamp"
        cat_list.append(cat)

    return cat_list


def dict_generator(spec_tables, spec_cats, url):
    product_name = url.replace("/produits/fr/", "")
    dict_ = {}
    if product_name in skus:
        dict_['productNo'] = skus[product_name]
        dict_['Full Product Name'] = 'PreSonus® ' + product_name
    # grabs sub categories and info for each category then appends to a list
    for i in range(len(spec_tables)):
        cat = spec_cats[i]
        table = spec_tables[i].find_all("tr")
        for j in range(len(table)):
            if j > 0:
                subinfo = table[j].text.strip().split("\n")
                # removes empty strings from list
                while "" in subinfo:
                    subinfo.remove("")
                # if there are more then one spec per attribute/ sub category it will seperate those values by a delimiter "|"
                specs = ("|").join(subinfo[1:])
                # fixes info if info is in sub category
                if "(" in subinfo[0]:
                    temp_info = "(" + subinfo[0].split("(")[1]
                    subinfo[0] = subinfo[0].split("(")[0]
                    specs = specs + ' ' + temp_info
                # if the list is not empty, key and value pairs are assigned to dict_
                if subinfo:
                    key = subinfo[0]
                    dict_[key] = specs

    return dict_


def pim_export(dict_, url):
    # export product specs to xlsx if tech specs available, otherwise throws error
    product_name = url.replace("/produits/fr/", "")
    if dict_:
        df = pd.DataFrame.from_dict([dict_])
        writer = pd.ExcelWriter("{} Specs FR.xlsx".format(product_name))
        df.to_excel(writer, index=False, engine='xlsxwriter')
        writer.save()
        print("SCRAPE TO XLSX SUCCESSFUL!")
    else:
        print("ERROR: NO TECH SPECS AVAILABLE!")

    pass


main()
