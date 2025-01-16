import argparse
import requests
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import m3u8
from tqdm import tqdm

def decrypt_video(encrypted_data, key, iv):
    encrypted_data = pad(data_to_pad=encrypted_data, block_size=AES.block_size)
    aes = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    decrypted_data = aes.decrypt(encrypted_data)
    return decrypted_data

def binify(x):
    h = hex(x)[2:].rstrip('L')
    return binascii.unhexlify('0'*(32-len(h))+h)

def login(session, username, password):
    data1 = {
        'ssoGubun': 'Login',
        'logintype': 'sso',
        'type': 'popup_login',
        'username': username,
        'password': password
    }
    res = session.post('https://ys.learnus.org/passni/sso/coursemosLogin.php', data=data1)
    soup = BeautifulSoup(res.text, features='html.parser')
    s1 = soup.find('input', {'name': 'S1'})['value']

    data2 = {
        'app_id': 'ednetYonsei',
        'retUrl': 'https://ys.learnus.org',
        'failUrl': 'https://ys.learnus.org/login/index.php',
        'baseUrl': 'https://ys.learnus.org',
        'S1':  s1,
        'loginUrl': 'https://ys.learnus.org/passni/sso/coursemosLogin.php',
        'ssoGubun': 'Login',
        'refererUrl': 'https://ys.learnus.org',
        'test': 'SSOAuthLogin',
        'loginType': 'invokeID',
        'E2': '',
        'username': username,
        'password': password
    }

    res = session.post('https://infra.yonsei.ac.kr/sso/PmSSOService', data=data2)
    soup = BeautifulSoup(res.text, features='html.parser')
    sc = soup.find('input', {'name': 'ssoChallenge'})['value']
    km = soup.find('input', {'name': 'keyModulus'})['value']

    jsonStr = '{"userid":"'+username+'","userpw":"'+password+'","ssoChallenge":"'+sc+'"}'
    keyPair = RSA.construct((int(km, 16), 0x10001))
    cipher = PKCS1_v1_5.new(keyPair)
    e2 = cipher.encrypt(jsonStr.encode()).hex()

    data3 = {
        'app_id': 'ednetYonsei',
        'retUrl': 'https://ys.learnus.org',
        'failUrl': 'https://ys.learnus.org/login/index.php',
        'baseUrl': 'https://ys.learnus.org',
        'loginUrl': 'https://ys.learnus.org/passni/sso/coursemosLogin.php',
        'ssoChallenge': sc,
        'loginType': 'invokeID',
        'returnCode': '',
        'returnMessage': '',
        'keyModulus': km,
        'keyExponent': '10001',
        'ssoGubun': 'Login',
        'refererUrl': 'https://ys.learnus.org',
        'test': 'SSOAuthLogin',
        'username': username,
        'password': password,
        'E2': e2
    }

    res = session.post('https://infra.yonsei.ac.kr/sso/PmSSOAuthService', data=data3)
    soup = BeautifulSoup(res.text, features='html.parser')
    if soup.find('input', {'name': 'E3'}) is None:
        raise Exception("Login Failed!")
    else:
        e3 = soup.find('input', {'name': 'E3'})['value']
        e4 = soup.find('input', {'name': 'E4'})['value']
        s2 = soup.find('input', {'name': 'S2'})['value']
        cltid = soup.find('input', {'name': 'CLTID'})['value']

        data4 = {
            'app_id': 'ednetYonsei',
            'retUrl': 'https://ys.learnus.org',
            'failUrl': 'https://ys.learnus.org/login/index.php',
            'baseUrl': 'https://ys.learnus.org',
            'loginUrl': 'https://ys.learnus.org/passni/sso/coursemosLogin.php',
            'E3': e3,
            'E4': e4,
            'S2': s2,
            'CLTID': cltid,
            'ssoGubun': 'Login',
            'refererUrl': 'https://ys.learnus.org',
            'test': 'SSOAuthLogin',
            'username': username,
            'password': password
        }

        session.post('https://ys.learnus.org/passni/sso/spLoginData.php', data=data4)
        session.get('https://ys.learnus.org/passni/spLoginProcess.php')

def download_video(session, url, output=None):
    res = session.get(url)
    soup = BeautifulSoup(res.text, features='html.parser')
    if soup.find('source', {'type': 'application/x-mpegURL'}) is None:
        print(f"Not a valid video url for {url}!")
        return
    m3u8_url = soup.find('source', {'type': 'application/x-mpegURL'})['src']
    video_title = soup.find('div', id='vod_header').find('h1')
    spans = video_title.find_all('span')
    for span in spans:
        span.decompose()
    video_title = video_title.text.strip()

    fix_table = str.maketrans('\/:*?"<>|', '＼／：＊？＂＜＞｜')
    video_title = video_title.translate(fix_table)

    if output is None:
        file_name = video_title + ".mp4"
    else:
        file_name = output

    playlist = m3u8.load(uri=m3u8_url)
    key = requests.get(playlist.keys[-1].absolute_uri).content
    seq_len = len(playlist.segments)

    with open(file_name, "wb") as f:
        for i in tqdm(range(seq_len)):
            seg = playlist.segments[i]
            data = requests.get(seg.absolute_uri).content
            iv = binify(i + 1)
            data = decrypt_video(data, key, iv)
            f.write(data)

    print(f"Download Complete for {file_name}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", dest="username", action="store")
    parser.add_argument("-p", "--password", dest="password", action="store")
    parser.add_argument("-o", "--output", dest="output", action="store")
    parser.add_argument("urls", nargs='+', action="store")
    args = parser.parse_args()

    with requests.Session() as session:
        try:
            login(session, args.username, args.password)
            for url in args.urls:
                download_video(session, url, args.output)
        except Exception as e:
            print(f"Failed to download videos: {str(e)}")
