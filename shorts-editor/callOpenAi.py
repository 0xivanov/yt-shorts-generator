from time import sleep 
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

URL = 'http://localhost:5800/'

options = Options()
options.add_argument('--headless=new')
driver = webdriver.Chrome()
actions = ActionChains(driver)

def click_button(Xpath):
    close_ui_button = driver.find_element(By.XPATH,Xpath)
    close_ui_button.click()   

def control_combination(key):
    sleep(2)
    actions.key_down(Keys.CONTROL)
    actions.key_down(key)
    actions.key_up(key)
    actions.key_up(Keys.CONTROL)
    actions.perform()
    
def press_enter():
    actions.send_keys(Keys.ENTER)
    actions.perform()

def call_chat_GPT(prompt):
    # Open a website
    sleep(2)
    driver.get(URL)
    sleep(2)
    driver.save_screenshot('diagnostic.png')
    sleep(2)
    click_button('/html/body/div[2]/div[1]/div[2]')
    text_area_input = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[1]/ul/li[2]/div/textarea')
    text_area_input.send_keys(prompt)
    sleep(3)
    
    #scale button
    click_button('/html/body/div[2]/div[1]/div[1]/ul/li[1]/div/a[2]')
    
    #close ui button
    click_button('/html/body/div[2]/div[1]/div[2]')
    sleep(3)
    
    control_combination('v')
    press_enter()
    
    sleep(10)
    actions.send_keys(Keys.TAB)
    actions.perform()
    #select copy reset
    control_combination('a')
    control_combination('c')
    control_combination('r')
    click_button('/html/body/div[2]/div[1]/div[2]')
    control_combination('t')
    result = text_area_input.get_attribute('value')
    text_area_input.send_keys(URL)
    press_enter()
    control_combination(Keys.TAB)
    control_combination('w')
    
    driver.close()
    
    return result
    
    

if __name__=="__main__":
    promt="Give me 5 interesting facts ?Respond in json code"
    print(call_chat_GPT(promt))