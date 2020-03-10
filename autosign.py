import requests
import numpy as np
import uuid
import time
import cv2
import threading
from pyzbar import pyzbar

# 用户登录
# http://passport2.chaoxing.com/wlogin


class CheckSignThread(threading.Thread):

    def __init__(self):
        super(CheckSignThread, self).__init__()
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True
        self.autosign = AutoSign()

    # @property
    # def flag(self):
    #     return self.flag
    #
    # @flag.setter
    # def flag(self, flag):
    #     self._flag = flag

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
            self.autosign.run_one()

    def pause(self):
        """
        暂停
        :return:
        """
        self.__flag.clear()  # 设置为False, 让线程阻塞

    def resume(self):
        """
        恢复暂停
        :return:
        """
        self.__flag.set()  # 设置为True, 让线程停止阻塞

    def stop(self):
        """
        结束
        :return:
        """
        self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()  # 设置为False


class AutoSign:

    def __init__(self, sign_frequency_minutes: int =10):

        self.__uuid = uuid.uuid4()
        self.__sign_frequency_minutes = sign_frequency_minutes
        self.__login_request = self.__get_login_request()
        self.__uid, self.__cookies = self.__login()
        cookies_dict = requests.utils.dict_from_cookiejar(self.__cookies)
        cookies_str = ''
        for key, valus in cookies_dict.items():
            cookies_str += key + '=' + valus + ';'

        self.__header = {
            "Cookie": cookies_str,
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 13_3_1 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                          "ChaoXingStudy/ChaoXingStudy_3_4.3.2_ios_phone_201911291130_27 "
                          "(@Kalimdor)_11391565702936108810"
        }

    def __login(self):
        """
        封装好的的登录函数，并返回登录后的uid和cookies
        :return: uid cookies
        注：已不建议对外调用，现由构造函数完成
        """
        image = self.__return_login_image()
        cv2.imshow("超星app扫描，任意键结束图片", image)
        cv2.waitKey(1)
        enc = self.__get_enc_by_image(image)
        uid, cookies = self.__wait_or_get_uid_and_cookies(enc)
        return uid, cookies

    def __return_login_image(self):
        """
        返回登录的二维码
        :return: opencv中的mat
        """
        rq_image = np.asarray(bytearray(self.__login_request.content), dtype="uint8")
        image = cv2.imdecode(rq_image, cv2.IMREAD_COLOR)
        return image

    def run_one(self):
        data_list = self.__get_all_class_info()
        print('准备扫描：')
        star = time.time()
        for n in range(len(data_list)):
            print('正在扫描' + data_list[n].get('classname'))
            self.__check_sing(data_list[n].get('courseid'),
                              data_list[n].get('classid'))
        print("此次扫描结束，共消耗时间{}".format(str(time.time() - star)))

    def run(self):
        """
        封装好的run函数
        :return:
        """
        while True:
            data_list = self.__get_all_class_info()
            print('准备扫描：')
            star = time.time()
            for n in range(len(data_list)):
                print('正在扫描' + data_list[n].get('classname'))
                self. __check_sing(data_list[n].get('courseid'),
                                   data_list[n].get('classid'))
            print("此次扫描结束，共消耗时间{}，下次扫描将在{}分钟后继续".format(str(time.time() - star), self.__sign_frequency_minutes))
            time.sleep(self.__sign_frequency_minutes*60)

    def __get_active_json(self, courseid, classid):
        active_url = 'https://mobilelearn.chaoxing.com/ppt/activeAPI/' \
                     'taskactivelist?courseId=' + str(courseid) + \
                     '&classId=' + str(classid) + "&uid=" + str(self.__uid)

        rq = requests.get(active_url, headers=self.__header)
        return rq.json()

    def __check_sing(self, courseid, classid):
        json_data = self.__get_active_json(courseid, classid)
        active_list = json_data['activeList']

        for item in active_list:
            if item.get('activeType') == 2 and item.get('status') == 1:
                sign_url = item.get('url')
                aid = self.__get_aid(sign_url)
                print('扫描到待签到 :' + item.get('nameOne'))
                self.__sign(aid)

    def __sign(self, aid):
        sign_url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?" \
                   "activeId=" + str(aid) + "&uid=" + str(self.__uid) + "&clientip=" \
                   "&latitude=-1&longitude=-1&appType=15&fid=0"
        rq = requests.get(sign_url, headers=self.__header)
        if rq.text == 'success':
            print('已成功签到')
        else:
            print("签到失败,原因:" + str(rq.text))

    def __get_aid(self, url):
        var_list = url.split('=')[3]
        aid = var_list.split('&')[0]
        return aid

    def __get_all_class_info(self):
        class_json = self.__get_class_json()
        data_list = []
        try:
            assert class_json.get('result')
            channel_list = class_json.get('channelList')

            # 最后检查一遍的时候发现这个for循环写的不好，太困了，下次改

            for num in range(len(channel_list)):
                _temp = {}
                class_info = channel_list[num]
                content = class_info.get('content')
                # 班级id
                _temp['classid'] = content.get('id')
                course = content.get('course')
                data = course.get('data')[0]
                _temp['classname'] = data.get('name')
                # 课程id
                _temp['courseid'] = data.get('id')
                data_list.append(_temp)

        except AssertionError:
            raise Exception("课程获取失败")
        except AttributeError:
            raise Exception("存在没有找到的课程信息")
        except TypeError:
            raise Exception("暂未定义的bug，出处get_all_class_info")

        return data_list

    def __get_class_json(self):
        """
        得到课程信息的json
        :return: 课程信息
        """
        info_url = "http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json"#&rss=1"
        rq = requests.get(info_url, headers=self.__header)
        return rq.json()

    def __wait_or_get_uid_and_cookies(self, enc):
        """
        得到登录后，也是后面需要用到的uid和cookies
        :param enc: enc参数，通过读取登录二维码链接获得
        :return: uid 和 cookies
        注：cookies是request的一个类，将其转换dict并处理后才放入header
        """
        statu_url = "http://passport2.chaoxing.com/getauthstatus"
        post_data = {
            'uuid': str(self.__uuid),
            'enc': enc
        }

        timeout = 10
        for n in range(timeout):
            rq = requests.post(statu_url, data=post_data)
            if rq.json().get('status'):
                cv2.destroyAllWindows()
                print('登录成功')
                return rq.cookies.get('UID'), rq.cookies
            else:
                if n >= timeout-1:
                    raise Exception("太久未登录，自行结束")
                print("未检测到登录，次数" + str(n + 1))
                time.sleep(3)

    @staticmethod
    def __get_enc_by_image(image):
        """
        通过二维码得到enc
        :param image: 二维码
        :return: enc
        """
        url_list = pyzbar.decode(image)
        try:
            assert len(url_list) == 1
            url = str(url_list[0][0])
            enc = url.split('=')[2]
            enc = enc.split('&')[0]
        except AssertionError:
            raise Exception("这张不是我们要的图片")
        return enc

    def __get_login_request(self):
        """
        获取get访问登录页面的请求
        :return: requests的一个get请求返回
        """
        codeqrurl = "http://passport2.chaoxing.com/createqr?uuid=" + str(self.__uuid) + "&fid=-1"
        rq = requests.get(codeqrurl)
        return rq


if __name__ == '__main__':
    autosign = AutoSign(1)
    # run函数使用方便，但是死循环
    autosign.run()
    # print(autosign._AutoSign__get_class_json())
    # 使用CheckSignThread可以控制停止和恢复,基于线程
    test = CheckSignThread()
    test.start()
    for n in range(2):
        test.pause()
        time.sleep(10)
        test.resume()
    test.stop()
