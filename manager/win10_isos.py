# -*- coding: utf-8 -*-
# flake8: noqa
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.chrome.options import Options
import unittest
import time
import os


def win10license(destination):
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": destination,
        "download.prompt_for_download": False
    })
    driver = webdriver.Chrome(options=chrome_options)

    # How long to wait for every single page to load
    driver.implicitly_wait(30)
    wait = WebDriverWait(driver, 30)

    # Start URL
    driver.get("https://www.microsoft.com/Licensing/servicecenter/default.aspx")
    product = "Windows 10 Enterprise"

    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_signInButton"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_LoginOptionsPopup_WorkAccountButton"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_LoginPopup_Login_LoginIdTextBox"))).click()
    driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_LoginPopup_Login_LoginIdTextBox").clear()
    driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_LoginPopup_Login_LoginIdTextBox").send_keys("USER")
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_LoginPopup_Login_LoginSubmitButton"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "i0118"))).click()
    driver.find_element_by_id("i0118").clear()
    driver.find_element_by_id("i0118").send_keys("PASSWORD")
    wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "idBtn_Back"))).click()
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Downloads and Keys"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_AutoSuggest1_productAutoSuggest"))).click()

    autosuggestsearch = driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_AutoSuggest1_productAutoSuggest")

    #while driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_ti0").get_attribute("title") != product:
    #    print("Suche nach: " + product)
    autosuggestsearch.clear()
    autosuggestsearch.send_keys(product)
    autosuggestsearch.submit()
    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_AutoSuggest1_productListImageButton"))).click()
    time.sleep(2)
    if driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_ti0").get_attribute("title") != product:
        print("Error")
        return

    wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_ti2"))).click()
    time.sleep(2)

    methodselect = Select(driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_tab3_downloadPanel_Method"))
    methodselect.select_by_value("Browser")
    time.sleep(2)

    langselect = Select(driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_tab3_downloadPanel_Language"))
    langselect.select_by_value("German")
    time.sleep(2)

    typeselect = Select(driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_tab3_downloadPanel_OSTypeList"))
    typeselect.select_by_value("2")
    time.sleep(2)


    wait.until(EC.element_to_be_clickable((By.ID, "ContinueButton"))).click()

    #  driver.find_element_by_id("ctl00_ctl00_MainContent_BodyContent_TRGrid_ctl01_tc_tab3_downloadPanel_FilesPanel_fileGrid_ctl03_download").click()
    #  time.sleep(1.0)  
    
    #find table element where all updates are listed
    fileTable = driver.find_element_by_xpath('//*[@id="filePanel"]/table/tbody') #/tr[2]/td[1]/span

    #count the number of entries in the list and list them in the dictonary
    Versions = {}
    i = 0
    for row in fileTable.find_elements_by_xpath(".//tr"):
        print(i, "    ", row.find_element_by_xpath('.//td[1]/span').text)
        Versions[i] = {}
        Versions[i]['Name'] = row.find_element_by_xpath('.//td[1]/span').text
        if not "Files" in Versions[i]['Name']:
            Versions[i]['LinkID'] = row.find_element_by_xpath('.//td[5]/input').get_attribute('id')
            i+=1
        CountItems = i

    timeout = 60*60*2 #2 hours in seconds

    for i in range(CountItems):
        print(Versions[i]['Name'], " : will be downloaded")
        fileTable.find_element_by_id(Versions[i]['LinkID']).click()

    #give download some time to start
    time.sleep(5)
    seconds = 0
    dl_wait = True
    
    while dl_wait and seconds < timeout:
        time.sleep(5)
        dl_wait = False
        files = os.listdir(destination)
        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1
    print("This took {} seconds".format(seconds))
    return "Done"


def win10_main():
    destinationpath = '/mirror/win10'
    if not os.path.exists(destinationpath):
        os.makedirs(destinationpath)

    result = None
    while not result:
        try:
            result = win10license(destinationpath)
        except Exception as e:
            print(e)
            time.sleep(600)

    print(result)


if __name__ == "__main__":
    win10_main()
