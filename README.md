# Chuyển Đổi Văn Bản Thành Âm Thanh ElevenLabs

Ứng dụng desktop cho phép chuyển đổi tệp văn bản thành các tệp âm thanh với chất lượng giọng nói tự nhiên thông qua API của ElevenLabs.

## Tính năng

- Quản lý API Key ElevenLabs
- Chuyển đổi văn bản thành giọng nói
- Lựa chọn giọng nói và mô hình TTS
- Xử lý hàng loạt nhiều tệp
- Tùy chọn định dạng âm thanh và tham số giọng nói
- Theo dõi sử dụng credits
- Tính toán tổng credits từ nhiều API key (loại bỏ các key trùng lặp)
- Đếm số từ trong văn bản
- Nhập văn bản trực tiếp hoặc chọn file

## Cài đặt

1. Cài đặt Python 3.8 trở lên
2. Cài đặt các thư viện phụ thuộc:

```
pip install -r requirements.txt
```

3. Chạy ứng dụng:

```
python main.py
```

## Yêu cầu

- Windows 10 trở lên
- Tối thiểu 4GB RAM
- Kết nối internet ổn định
- 100MB dung lượng đĩa trống
- API key ElevenLabs hợp lệ

## Tính năng mới (Phiên bản 1.1)

### Tính toán tổng credits từ nhiều API key
- Hệ thống sẽ tự động phát hiện và gộp tổng credits từ các API key đã lưu
- Loại bỏ các API key trùng lặp khi tính toán tổng credits
- Hiển thị tổng số credits khả dụng và số lượng key độc nhất

### Đếm từ trong văn bản
- Tính toán số từ trong file văn bản đã chọn
- Tính toán số từ trong văn bản nhập trực tiếp

### Nhập văn bản trực tiếp
- Người dùng có thể lựa chọn giữa chế độ nhập văn bản trực tiếp hoặc chọn file
- Hỗ trợ chuyển đổi văn bản nhập trực tiếp sang âm thanh
- Tự động chia văn bản thành nhiều phần nếu vượt quá độ dài quy định 