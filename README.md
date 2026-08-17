# DaiMinhChu-Offline

Dự án nghiên cứu/phục dựng **Đại Minh Chủ Việt Nam** để chạy ở chế độ local/offline bằng cách tái tạo backend tương thích với client gốc.

## Trạng thái

Đang ở giai đoạn reverse APK 8.0.2:

- Unity 4.x + Mono.
- Có `Assembly-CSharp.dll` với nhiều tên class/method còn nguyên.
- Đã xác định endpoint Soha cũ và các class HTTP chính.
- Hướng hiện tại: local HTTP compatibility server, không phụ thuộc GS gốc nếu reverse được schema.

## Tài liệu quan trọng

- [`HANDOFF.md`](HANDOFF.md): trạng thái dự án mới nhất, bắt buộc đọc trước khi tiếp tục ở phiên làm việc mới.
- `docs/`: ghi chép reverse/protocol.
- `server/`: local compatibility server sẽ được xây dựng tại đây.

## Phạm vi

Ưu tiên offline cơ bản:

`Login -> GetUserInfo -> đội hình/tướng/trang bị/võ công -> Giang Hồ -> BattleReplay -> save local`

Không ưu tiên các hệ thống online như nạp tiền, chat, bang hội, leaderboard và PvP thật.

## Lưu ý

Repo không lưu APK gốc hoặc toàn bộ asset game. Chỉ lưu code tự viết, tài liệu reverse và fixture/test data tối thiểu cần thiết cho nghiên cứu tương thích.
