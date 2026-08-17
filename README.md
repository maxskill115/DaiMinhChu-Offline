# DaiMinhChu-Offline

Dự án nghiên cứu/phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chạy local/offline bằng cách tái tạo backend tương thích với client gốc.

## Trạng thái hiện tại

APK đã được xác định là **Unity 4.x + Mono**, còn `Assembly-CSharp.dll` với nhiều symbol C# nguyên tên.

Đã reverse và dựng prototype cho flow:

```text
Patched LoginForm
    -> /Login
    -> chọn server Offline
    -> /CheckUser
    -> /GetUserInfo
    -> BeginCutsceneForm
    -> chọn Phong Thanh Dương / Lệnh Hồ Xung / Sở Lưu Hương
    -> /SelectStartNhanVat
    -> Home (Form 3)
```

Transport game đã xác định là **HTTP + JSON bọc AES-128-CBC/PKCS7**.

Core config nhân vật/trang bị/võ công/Giang Hồ... đã được xác nhận là có sẵn trong Unity `Resources` của APK; remote `LoginCfg` chỉ phục vụ cập nhật config và có thể để `null` trong prototype.

> Flow trên hiện đã được xác nhận bằng static reverse + fixture/test server. **Chưa được xác nhận end-to-end trên Android/emulator thật.** Runtime test là milestone tiếp theo.

## Thành phần repo

- [`HANDOFF.md`](HANDOFF.md) — nguồn trạng thái chính, **bắt buộc đọc trước khi tiếp tục ở chat mới**.
- [`docs/protocol/login.md`](docs/protocol/login.md) — login / CheckUser / GetUserInfo / AES transport.
- [`docs/protocol/first-character.md`](docs/protocol/first-character.md) — BeginCutsceneForm và `/SelectStartNhanVat`.
- [`server/`](server/) — Python local compatibility server.
- [`tools/patch_client.py`](tools/patch_client.py) — patch đúng APK 8.0.2 để bỏ Soha SDK login và trỏ login server về local.

## Mục tiêu offline ưu tiên

```text
Login
 -> profile/save local
 -> nhân vật/đội hình/trang bị/võ công
 -> Giang Hồ
 -> BattleReplay
 -> tiến trình offline ổn định
```

Không ưu tiên giai đoạn đầu: nạp tiền, Soha account thật, chat, bang hội online, PvP thật, leaderboard, liên server.

## Không lưu trong repo

Repo không chứa APK gốc, full asset dump, credential hay keystore. Chỉ lưu code tự viết, tài liệu reverse và fixture tối thiểu phục vụ nghiên cứu tương thích.
