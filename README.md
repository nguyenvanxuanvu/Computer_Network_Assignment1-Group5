# Computer Network - Assignment 1 - Group 5 - L07 - HK211
### Danh sách thành viên:
1. Ngô Thị Hà Bắc - 1912700
2. Võ Thị Na - 1914210
3. Nguyễn Văn Nam - 1813168
4. Nguyễn Văn Xuân Vũ - 1915982

### Hướng dẫn chạy chương trình:

Trong terminal thứ nhất, ta chạy server với câu lệnh:
```python
python Server.py <server_port>
```
- Trong đó server_port là cổng mà máy chủ của bạn lắng nghe các kết nối RTSP đến.
- Chú ý cần chọn cổng lớn hơn 1025. Ví dụ với server_port là 3000:
```python
python Server.py 3000
```

Trong terminal thứ hai hoặc các terminal khác, chạy client với câu lệnh:
```python
python ClientLauncher.py <server_host> <server_port> <RTP_port> <video_file>
```
Trong đó: 
- server_host là tên của máy chủ đang chạy
- server_port là cổng nơi máy chủ đang lắng nghe
- RTP_port là cổng nơi các gói RTP được nhận
- video_file là tên của tệp video bạn muốn yêu cầu 

Ví dụ với server_host là localhost, server_port là 3000, RTP_port là 101 và video_file là movie.Mjpeg:
```python
python ClientLauncher.py localhost 3000 101 movie.Mjpeg
```


          
          
          
          



