from selenium.webdriver.edge.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

if __name__ == '__main__':
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service('./msedgedriver.exe')
    browser = webdriver.Edge(service=service, options=options)
    browser.get("https://www.selenium.dev/selenium/web/web-form.html")
    print(browser.title)
    while(True):
       pass