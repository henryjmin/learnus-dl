# learnus-dl

## 사용방법

python 3.10 이상
```
pip install -r requirements.txt
python learnus-dl.py -u username(학번) -p password video_url
```
Windows executable
```
learnus-dl.exe -u username(학번) -p password video_url
```
영상의 제목에 \ / : * ? " < > | 등의 문자가 포함되어 오류가 발생할 경우 `-o filename.mp4` 를 추가하여 저장되는 파일명을 지정할 수 있습니다.