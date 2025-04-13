# learnus-dl

## Requirements
python >= 3.10 (Optional for Windows)

ffmpeg (Optional, recommended)
```
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg
```
## Usage

Python script
```
pip install -r requirements.txt
./learnus-dl.py -u username(학번) -p password video_url
```
Windows executable
```
learnus-dl.exe -u username(학번) -p password video_url
```
Download as `output.mp4`
```
learnus-dl.exe -u username(학번) -p password -o output.mp4 video_url
```

## Build Windows executable
```
.\build-exe.bat
```
