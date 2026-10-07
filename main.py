# -*- coding:utf-8 -*-
import copy
import hashlib
import logging
import os
import random
import smtplib
import time
from email.mime.text import MIMEText

import requests


ENV = os.environ


class RedactingFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        secrets = []

        bduss = ENV.get("BDUSS", "")
        if bduss:
            secrets.extend(value for value in bduss.split("#") if value)

        for key in ("AUTH", "FROM", "TO"):
            value = ENV.get(key)
            if value:
                secrets.append(value)

        for secret in secrets:
            message = message.replace(secret, "***")

        return message


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
formatter = RedactingFormatter(LOG_FORMAT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.propagate = False

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

failure_handler = logging.FileHandler("run.log", mode="a", encoding="utf-8")
failure_handler.setLevel(logging.ERROR)
failure_handler.setFormatter(formatter)
logger.addHandler(failure_handler)


LIKIE_URL = "http://c.tieba.baidu.com/c/f/forum/like"
TBS_URL = "http://tieba.baidu.com/dc/common/tbs"
SIGN_URL = "http://c.tieba.baidu.com/c/c/forum/sign"

HEADERS = {
    "Host": "tieba.baidu.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 6.1; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.71 Safari/537.36"
    ),
}
SIGN_DATA = {
    "_client_type": "2",
    "_client_version": "9.7.8.0",
    "_phone_imei": "000000000000000",
    "model": "MI+5",
    "net_type": "1",
}

COOKIE = "Cookie"
BDUSS = "BDUSS"
EQUAL = r"="
EMPTY_STR = r""
TBS = "tbs"
TIMESTAMP = "timestamp"
FID = "fid"
SIGN_KEY = "tiebaclient!!!"
UTF8 = "utf-8"
SIGN = "sign"
KW = "kw"

session = requests.Session()


def get_tbs(bduss):
    logger.info("获取 tbs 开始")
    headers = copy.copy(HEADERS)
    headers.update({COOKIE: EMPTY_STR.join([BDUSS, EQUAL, bduss])})

    try:
        tbs = session.get(url=TBS_URL, headers=headers, timeout=5).json()[TBS]
    except Exception as exc:
        logger.warning("首次获取 tbs 失败，准备重试：%s", type(exc).__name__)
        try:
            tbs = session.get(url=TBS_URL, headers=headers, timeout=5).json()[TBS]
        except Exception as retry_exc:
            raise RuntimeError("获取 tbs 失败") from retry_exc

    logger.info("获取 tbs 结束")
    return tbs


def get_favorite(bduss):
    logger.info("获取关注的贴吧开始")
    return_data = {}
    page = 1
    data = {
        "BDUSS": bduss,
        "_client_type": "2",
        "_client_id": "wappc_1534235498291_488",
        "_client_version": "9.7.8.0",
        "_phone_imei": "000000000000000",
        "from": "1008621y",
        "page_no": "1",
        "page_size": "200",
        "model": "MI+5",
        "net_type": "1",
        "timestamp": str(int(time.time())),
        "vcode_tag": "11",
    }
    data = encode_data(data)

    try:
        res = session.post(url=LIKIE_URL, data=data, timeout=5).json()
    except Exception as exc:
        raise RuntimeError("获取关注贴吧失败") from exc

    return_data = res
    if "forum_list" not in return_data:
        return_data["forum_list"] = []
    if res["forum_list"] == []:
        return {"gconforum": [], "non-gconforum": []}
    if "non-gconforum" not in return_data["forum_list"]:
        return_data["forum_list"]["non-gconforum"] = []
    if "gconforum" not in return_data["forum_list"]:
        return_data["forum_list"]["gconforum"] = []

    while "has_more" in res and res["has_more"] == "1":
        page += 1
        data = {
            "BDUSS": bduss,
            "_client_type": "2",
            "_client_id": "wappc_1534235498291_488",
            "_client_version": "9.7.8.0",
            "_phone_imei": "000000000000000",
            "from": "1008621y",
            "page_no": str(page),
            "page_size": "200",
            "model": "MI+5",
            "net_type": "1",
            "timestamp": str(int(time.time())),
            "vcode_tag": "11",
        }
        data = encode_data(data)

        try:
            res = session.post(url=LIKIE_URL, data=data, timeout=5).json()
        except Exception as exc:
            raise RuntimeError(f"获取关注贴吧第 {page} 页失败") from exc

        if "forum_list" not in res:
            continue
        if "non-gconforum" in res["forum_list"]:
            return_data["forum_list"]["non-gconforum"].append(
                res["forum_list"]["non-gconforum"]
            )
        if "gconforum" in res["forum_list"]:
            return_data["forum_list"]["gconforum"].append(
                res["forum_list"]["gconforum"]
            )

    favorites = []
    for group_name in ("non-gconforum", "gconforum"):
        for item in return_data["forum_list"][group_name]:
            if isinstance(item, list):
                for nested in item:
                    if isinstance(nested, list):
                        favorites.extend(nested)
                    else:
                        favorites.append(nested)
            else:
                favorites.append(item)

    logger.info("获取关注的贴吧结束")
    return favorites


def encode_data(data):
    raw = EMPTY_STR
    for key in sorted(data.keys()):
        raw += key + EQUAL + str(data[key])
    sign = hashlib.md5((raw + SIGN_KEY).encode(UTF8)).hexdigest().upper()
    data.update({SIGN: str(sign)})
    return data


def client_sign(bduss, tbs, fid, kw):
    logger.info("开始签到贴吧：%s", kw)
    data = copy.copy(SIGN_DATA)
    data.update(
        {
            BDUSS: bduss,
            FID: fid,
            KW: kw,
            TBS: tbs,
            TIMESTAMP: str(int(time.time())),
        }
    )
    data = encode_data(data)
    return session.post(url=SIGN_URL, data=data, timeout=5).json()


def send_email(sign_list):
    if not all(key in ENV for key in ("HOST", "FROM", "TO", "AUTH")):
        logger.error("未配置邮箱")
        return

    host = ENV["HOST"]
    from_addr = ENV["FROM"]
    to_addrs = ENV["TO"].split("#")
    auth = ENV["AUTH"]

    subject = f"{time.strftime('%Y-%m-%d', time.localtime())} 签到{len(sign_list)}个贴吧"
    body = """
    <style>
    .child {
      background-color: rgba(173, 216, 230, 0.19);
      padding: 10px;
    }
    .child * { margin: 5px; }
    </style>
    """

    for item in sign_list:
        body += f"""
        <div class="child">
            <div class="name">贴吧名称: {item['name']}</div>
            <div class="slogan">贴吧简介: {item['slogan']}</div>
        </div>
        <hr>
        """

    msg = MIMEText(body, "html", "utf-8")
    msg["subject"] = subject

    smtp = smtplib.SMTP()
    smtp.connect(host)
    smtp.login(from_addr, auth)
    smtp.sendmail(from_addr, to_addrs, msg.as_string())
    smtp.quit()


def main():
    bduss_raw = ENV.get("BDUSS", "").strip()
    if not bduss_raw:
        raise RuntimeError("未配置 BDUSS")

    accounts = [value for value in bduss_raw.split("#") if value]
    if not accounts:
        raise RuntimeError("BDUSS 配置为空")

    for index, bduss in enumerate(accounts, start=1):
        logger.info("开始签到第 %d 个用户", index)
        tbs = get_tbs(bduss)
        favorites = get_favorite(bduss)

        for forum in favorites:
            time.sleep(random.randint(1, 5))
            client_sign(bduss, tbs, forum["id"], forum["name"])

        logger.info("完成第 %d 个用户签到，共处理 %d 个贴吧", index, len(favorites))

    logger.info("所有用户签到结束")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("签到任务异常退出")
        raise
