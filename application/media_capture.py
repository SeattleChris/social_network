from flask import flash, current_app as app
import chromedriver_binary  # Adds chromedriver binary to path
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
import re
from pprint import pprint
# import json

location = 'application/save/'
URL = app.config.get('URL')
# chrome_path = chromedriver_binary.chromedriver_filename
# myProxy = "10.0.x.x:yyyy"
myProxy = None


def chrome_grab(ig_url, filename):
    """ Using selenium webdriver with Chrome and grabing the file from the page content. """
    filepath = location + filename
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')  # required when running as root user to avoid sandbox errors.
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--test-type')
    # options.add_argument('--log-level=ALL')
    if myProxy:
        options.add_argument(f"--proxy-server={myProxy}")
    # options.binary_location = "/usr/bin/chromium"
    # chrome_path = '/home/dev/chromedriver'  # TODO: Set accurate values
    # service_args = ['--verbose', '--log-path=/tmp/chromedriver.log', '--log-level=ALL']  # TODO: Set accurate values
    service_args = ['--log-level=ALL']
    # # Instead of ChromeOptions approach, could use pyvirtualdisplay
    # from pyvirtualdisplay import Display
    # display = Display(visible=0, size=(1024, 768))
    # display.start()
    # driver = webdriver.Chrome(driver_path=chrome_path, service_args=service_args)
    driver = webdriver.Chrome(chrome_options=options, service_args=service_args)
    # Firefox:
    # firefox_proxy = Proxy({
    #     'proxyType': ProxyType.MANUAL,
    #     'httpProxy': myProxy,
    #     'ftpProxy': myProxy,
    #     'sslProxy': myProxy,
    #     'noProxy': ''
    # })
    # ff_driver = webdriver.Firefox(proxy=firefox_proxy)

    app.logger.info("==============================================")
    driver.get(ig_url)
    success = driver.save_screenshot(f"{filepath}_full.png")
    count = 0 if success else -1
    app.logger.debug(f"Start of count at {count + 1}. ")
    soup = bs(driver.page_source, 'html.parser')
    target = [img.get('src') for img in soup.findAll('img') if not re.search("^\/", img.get('src'))]
    pprint(target)
    for ea in target:
        count += 1
        time.sleep(1)
        try:
            driver.get(ea)
            temp = f"{filepath}_{count}.png"
            app.logger.debug(temp)
            driver.save_screenshot(temp)
        except Exception as e:
            message = f"Error on file # {count} . "
            app.logger.error(message)
            app.logger.exception(e)
            flash(message)
    success = count == len(target)
    message = 'Files Saved! ' if success else "Error in Screen Grab. "
    app.logger.debug(message)
    flash(message)
    answer = f"{URL}/{filepath}_full.png" if success else f"Failed. {success} "
    driver.close()
    return answer


def soup_no_chrome(ig_url, filename):
    """ If possible, approach that does not require a browser emulation. """
    import requests
    import urllib.request
    filepath = location + filename

    def _get_images(ig_url, filename):
        """ Helper function to traverse and capture image files.
            Recursive call if image source points to another web page.
        """
        response = requests.get(ig_url)
        app.logger.debug(response)
        soup = bs(response.text, "html.parser")
        app.logger.debug(soup)
        images = [img.get('src') for img in soup.findAll('img')]
        app.logger.debug(images)
        goal, bonus = len(images), 0
        file_count = 1
        for image in images:
            # TODO: The following steps are not fully implemented.
            # Check if the src pointed to actual images, or a web page
            # 1) regex to grab the file extension
            # 2) if file extension exists, confirm it matches known image extensions.
            extension = 'png'  # example, but actually set according to a.
            #   a) set the output filename to have the same file extension as original file.
            urllib.request.urlretrieve(image, f"{filepath}_{file_count}.{extension}")
            # 3) if no file extension or doesn't match known extensions, assume a web page view.
            recur_goal, recur_found = _get_images(image, f"filename_{file_count}")
            goal += recur_goal
            bonus += recur_found
            file_count += 1
        return (goal, file_count + bonus)

    goal, found = _get_images(ig_url, filename)
    success = goal == found
    message = 'Files Saved! ' if success else "Error in Capture(s). "
    app.logger.debug(message)
    flash(message)
    answer = f"{URL}/{filepath}" if success else f"Failed. {success} "
    return answer


def capture(post, filename):
    """ Visits the permalink for give Post, creates a screenshot named the given filename. """
    ig_url = post.permalink
    answer = chrome_grab(ig_url, filename)
    return answer

    # script = body.find('script', text=lambda t: t.startswith('window._sharedData'))
    # page_json = script.text.split(' = ', 1)[1].rstrip(';')
    # data = json.loads(page_json)