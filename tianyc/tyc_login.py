"""
突破天眼查极验验证码
"""
import random
import time, re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import requests
from io import BytesIO


class HuXiu(object):
    def __init__(self):
        chrome_option = webdriver.ChromeOptions()
        # chrome_option.set_headless()

        self.driver = webdriver.Chrome(executable_path=r"G:\drivers\chromedriver.exe", chrome_options=chrome_option)
        self.driver.maximize_window()

    def move_x(self, distance):
        element = self.driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')

        # 这里就是根据移动进行调试，计算出来的位置不是百分百正确的，加上一点偏移
        distance -= element.size.get('width') / 2
        distance += 15

        # 按下鼠标左键
        ActionChains(self.driver).click_and_hold(element).perform()
        time.sleep(0.05)

        one = distance + 5


        ActionChains(self.driver).move_by_offset(one, 0).perform()
        time.sleep(0.1)
        ActionChains(self.driver).move_by_offset(-2, 0).perform()
        time.sleep(0.2)
        ActionChains(self.driver).move_by_offset(-4, 0).perform()
        time.sleep(1)
        # ActionChains(self.driver).move_by_offset(4, 0).perform()

        # ActionChains(self.driver).move_by_offset(distance, 1).perform()
        ActionChains(self.driver).release(on_element=element).perform()

        time.sleep(5)
        cookies = self.driver.get_cookies()
        cookie_list = []
        for cookei in cookies:
            name = cookei.get("name")
            value = cookei.get("value")
            n_v = "{}={}".format(name, value)
            cookie_list.append(n_v)

        cook = ";".join(cookie_list)
        print(cook)

    # 判断颜色是否相近
    def is_similar_color(self, x_pixel, y_pixel):
        for i, pixel in enumerate(x_pixel):
            if abs(y_pixel[i] - pixel) > 50:
                return False
        return True

    def get_offset_distance(self, cut_image, full_image):
        for x in range(cut_image.width):
            for y in range(cut_image.height):
                cpx = cut_image.getpixel((x, y))
                fpx = full_image.getpixel((x, y))
                if not self.is_similar_color(cpx, fpx):
                    img = cut_image.crop((x, y, x + 50, y + 40))
                    # 保存一下计算出来位置图片，看看是不是缺口部分
                    img.save("tyc1.jpg")
                    return x

    # 拼接图片
    def mosaic_image(self, image_url, location):
        resq = requests.get(image_url)
        file = BytesIO(resq.content)
        img = Image.open(file)
        image_upper_lst = []
        image_down_lst = []
        for pos in location:
            if pos[1] == 0:
                # y值==0的图片属于上半部分，高度58
                image_upper_lst.append(img.crop((abs(pos[0]), 0, abs(pos[0]) + 10, 58)))
            else:
                # y值==58的图片属于下半部分
                image_down_lst.append(img.crop((abs(pos[0]), 58, abs(pos[0]) + 10, img.height)))

        x_offset = 0
        # 创建一张画布，x_offset主要为新画布使用
        new_img = Image.new("RGB", (260, img.height))
        for img in image_upper_lst:
            new_img.paste(img, (x_offset, 58))
            x_offset += img.width

        x_offset = 0
        for img in image_down_lst:
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width

        return new_img

    def get_image_url(self, xpath):
        link = re.compile('background-image: url\("(.*?)"\); background-position: (.*?)px (.*?)px;')
        elements = self.driver.find_elements_by_xpath(xpath)
        image_url = None
        location = list()
        for element in elements:
            style = element.get_attribute("style")
            groups = link.search(style)
            url = groups[1]
            x_pos = groups[2]
            y_pos = groups[3]
            location.append((int(x_pos), int(y_pos)))
            image_url = url
        return image_url, location

    def analog_drag(self):
        # 鼠标移动到拖动按钮，显示出拖动图片
        element = self.driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')
        ActionChains(self.driver).move_to_element(element).perform()
        time.sleep(3)

        # 刷新一下极验图片
        element = self.driver.find_element_by_xpath('//a[@class="gt_refresh_button"]')
        element.click()
        time.sleep(1)

        # 获取图片地址和位置坐标列表
        cut_image_url, cut_location = self.get_image_url('//div[@class="gt_cut_bg_slice"]')
        full_image_url, full_location = self.get_image_url('//div[@class="gt_cut_fullbg_slice"]')

        # 根据坐标拼接图片
        cut_image = self.mosaic_image(cut_image_url, cut_location)
        full_image = self.mosaic_image(full_image_url, full_location)

        cut_image.save("tyc_cut.jpg")
        full_image.save("tyc_full.jpg")

        # 根据两个图片计算距离
        distance = self.get_offset_distance(cut_image, full_image)
        self.move_x(distance)

    def visit_index(self):
        self.driver.get("https://www.tianyancha.com/")

        # WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="js-register"]')))
        # reg_element = self.driver.find_element_by_xpath('//*[@class="js-register"]')
        # reg_element.click()
        time.sleep(3)
        login = self.driver.find_element_by_xpath("//div[@class='nav-item -home']")
        login.click()
        time.sleep(2)
        pwd_login = self.driver.find_element_by_xpath("//div[@tyc-event-ch='LoginPage.PasswordLogin']")
        pwd_login.click()
        time.sleep(3)
        phone = self.driver.find_element_by_xpath("//div[@class='modulein modulein1 mobile_box  f-base collapse in']/div[@class='pb30 position-rel']/input")
        phone.send_keys("17328702802")
        time.sleep(1)
        pwd = self.driver.find_element_by_xpath("//div[@class='modulein modulein1 mobile_box  f-base collapse in']/div[@class='input-warp -block']/input")
        pwd.send_keys("QWER1234qwer")
        login_click = self.driver.find_element_by_xpath("//div[@onclick='loginObj.loginByPhone(event);']")
        login_click.click()

        WebDriverWait(self.driver, 10, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="gt_slider_knob gt_show"]')))

        # 进入模拟拖动流程
        self.analog_drag()


if __name__ == "__main__":
    h = HuXiu()
    h.visit_index()
