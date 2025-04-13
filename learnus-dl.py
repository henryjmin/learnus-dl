#! /usr/bin/env python3
import argparse
import ffmpeg
import m3u8
import requests
import sys
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from tqdm import tqdm


def login(id: str, pw: str) -> requests.Session:
    s = requests.Session()
    LEARNUS_URL = 'https://ys.learnus.org'
    YONSEI_URL = 'https://infra.yonsei.ac.kr'
    data1 = {
        'ssoGubun': 'Login',
        'logintype': 'sso',
        'type': 'popup_login',
        'username': id,
        'password': pw
    }
    res = s.post(LEARNUS_URL + '/passni/sso/coursemosLogin.php', data=data1)
    soup = BeautifulSoup(res.text, features='html.parser')
    s1 = soup.find('input', {'name': 'S1'})['value']

    data2 = {
        'app_id': 'ednetYonsei',
        'retUrl': LEARNUS_URL,
        'failUrl': LEARNUS_URL + '/login/index.php',
        'baseUrl': LEARNUS_URL,
        'S1':  s1,
        'loginUrl': LEARNUS_URL + '/passni/sso/coursemosLogin.php',
        'ssoGubun': 'Login',
        'refererUrl': LEARNUS_URL,
        'test': 'SSOAuthLogin',
        'loginType': 'invokeID',
        'E2': '',
        'username': id,
        'password': pw
    }
    res = s.post(YONSEI_URL + '/sso/PmSSOService', data=data2)
    soup = BeautifulSoup(res.text, features='html.parser')
    sc = soup.find('input', {'name': 'ssoChallenge'})['value']
    km = soup.find('input', {'name': 'keyModulus'})['value']

    data3 = {
        'app_id': 'ednetYonsei',
        'retUrl': LEARNUS_URL,
        'failUrl': LEARNUS_URL + '/login/index.php',
        'baseUrl': LEARNUS_URL,
        'loginUrl': LEARNUS_URL + '/passni/sso/coursemosLogin.php',
        'ssoChallenge': sc,
        'loginType': 'invokeID',
        'returnCode': '',
        'returnMessage': '',
        'keyModulus': km,
        'keyExponent': '10001',
        'ssoGubun': 'Login',
        'refererUrl': LEARNUS_URL,
        'test': 'SSOAuthLogin',
        'username': id,
        'password': pw
    }
    res = s.post(LEARNUS_URL + '/passni/sso/coursemosLogin.php', data=data3)
    soup = BeautifulSoup(res.text, features='html.parser')
    s1 = soup.find('input', {'name': 'S1'})['value']
    json_str = f'{{"userid":"{id}","userpw":"{pw}","ssoChallenge":"{sc}"}}'
    key_pair = RSA.construct((int(km, 16), 0x10001))
    cipher = PKCS1_v1_5.new(key_pair)
    e2 = cipher.encrypt(json_str.encode()).hex()

    data4 = {
        'app_id': 'ednetYonsei',
        'retUrl': LEARNUS_URL,
        'failUrl': LEARNUS_URL + '/login/index.php',
        'baseUrl': LEARNUS_URL,
        'S1':  s1,
        'loginUrl': LEARNUS_URL + '/passni/sso/coursemosLogin.php',
        'ssoGubun': 'Login',
        'refererUrl': LEARNUS_URL,
        'test': 'SSOAuthLogin',
        'loginType': 'invokeID',
        'E2': e2,
        'username': id,
        'password': pw
    }
    res = s.post(YONSEI_URL + '/sso/PmSSOAuthService', data=data4)
    soup = BeautifulSoup(res.text, features='html.parser')
    e3 = soup.find('input', {'name': 'E3'})['value']
    e4 = soup.find('input', {'name': 'E4'})['value']
    s2 = soup.find('input', {'name': 'S2'})['value']
    cltid = soup.find('input', {'name': 'CLTID'})['value']

    data5 = {
        'app_id': 'ednetYonsei',
        'retUrl': LEARNUS_URL,
        'failUrl': LEARNUS_URL + '/login/index.php',
        'baseUrl': LEARNUS_URL,
        'loginUrl': LEARNUS_URL + '/passni/sso/coursemosLogin.php',
        'E3': e3,
        'E4': e4,
        'S2': s2,
        'CLTID': cltid,
        'ssoGubun': 'Login',
        'refererUrl': LEARNUS_URL,
        'test': 'SSOAuthLogin',
        'username': id,
        'password': pw
    }
    s.post(LEARNUS_URL + '/passni/sso/spLoginData.php', data=data5)

    s.get(LEARNUS_URL + '/passni/spLoginProcess.php')
    return s


def m3u8_download_direct(m3u8_url: str, file_name: str):
    playlist = m3u8.load(uri=m3u8_url)
    seq_len = len(playlist.segments)
    with open(file_name, 'wb') as f:
        for i in tqdm(range(seq_len)):
            seg = playlist.segments[i]
            data = requests.get(seg.absolute_uri).content
            f.write(data)


def m3u8_download_ffmpeg(url: str, file_name: str):
    (
        ffmpeg
        .input(m3u8_url)
        .output(file_name, c='copy')
        .run()
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', dest='username', action='store')
    parser.add_argument('-p', '--password', dest='password', action='store')
    parser.add_argument('-o', '--output', dest='output', action='store')
    parser.add_argument(dest='url', action='store')
    args = parser.parse_args()

    id = args.username
    pw = args.password

    try:
        s = login(id, pw)
    except:
        print('Failed to login!')
        sys.exit(0)

    url: str = args.url
    if ('view' in url) and ('viewer' not in url):
        url = url.replace('view', 'viewer')
    res = s.get(url)
    soup = BeautifulSoup(res.text, features='html.parser')

    try:
        m3u8_url = soup.find(
            'source', {'type': 'application/x-mpegURL'})['src']
    except:
        print('Not a valid video url!')
        sys.exit(0)

    if args.output is None:
        video_title: str = soup.select_one('#vod_header > h1').find(
            string=True, recursive=False).text.strip()
        fix_table = str.maketrans('\\/:*?"<>|', '＼／：＊？＂＜＞｜')
        video_title = video_title.translate(fix_table)
        file_name = video_title + '.mp4'
    else:
        file_name = args.output

    try:
        m3u8_download_ffmpeg(m3u8_url, file_name)
    except:
        try:
            m3u8_download_direct(m3u8_url, file_name)
        except:
            print('Failed to download the video!')
            sys.exit(0)

    print('Download Complete!')
