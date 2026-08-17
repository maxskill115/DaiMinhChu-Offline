# DaiMinhChu-Offline

Dự án nghiên cứu/phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chạy local/offline bằng backend tương thích với client gốc.

## Trạng thái hiện tại

APK: **Unity 4.x + Mono**, còn `Assembly-CSharp.dll` với nhiều symbol C# nguyên tên.

Đã reverse + implement server prototype cho:

```text
Patched LoginForm
 -> /Login
 -> /CheckUser
 -> /GetUserInfo
 -> BeginCutsceneForm
 -> chọn Phong Thanh Dương / Lệnh Hồ Xung / Sở Lưu Hương
 -> /SelectStartNhanVat
 -> Home (Form 3)
 -> Giang Hồ (Form 4)
 -> Battle.asmx/GiangHo
 -> BattleForm (Form 7)
 -> BattleReplay 1v1 / 1 hiệp / 1 đòn thường
 -> result panel
```

Transport đã xác định là **HTTP + JSON bọc AES-128-CBC/PKCS7**.

Core config nhân vật/trang bị/võ công/Giang Hồ... có sẵn trong Unity `Resources`; local `/Login` có thể để `LoginCfg=null` và bỏ remote config update.

Server đã được **unit-test + smoke-test bằng request AES thật qua HTTP**, gồm cả `Battle.asmx/GiangHo`.

> **Android/client runtime vẫn PENDING.** Chưa được coi là đã vào game/phát trận thành công cho tới khi chạy APK thật với server + `adb logcat`.

## Thành phần repo

- [`HANDOFF.md`](HANDOFF.md) — nguồn trạng thái chính; chat mới đọc file này trước.
- [`docs/protocol/login.md`](docs/protocol/login.md) — login / CheckUser / GetUserInfo / AES.
- [`docs/protocol/first-character.md`](docs/protocol/first-character.md) — BeginCutsceneForm / SelectStartNhanVat.
- [`docs/protocol/giangho-battle.md`](docs/protocol/giangho-battle.md) — Giang Hồ, Battle.asmx, DTO và replay tối thiểu.
- [`server/`](server/) — Python local compatibility server + unit/smoke tests.
- [`tools/patch_client.py`](tools/patch_client.py) — patch APK 8.0.2 bỏ Soha SDK login và trỏ server về local.

## Milestone tiếp theo

```text
APK patched + Android/emulator
 -> xác nhận Login/Home runtime
 -> mở Giang Hồ
 -> gửi Battle.asmx/GiangHo
 -> client phát replay
 -> result panel
```

Sau khi runtime pass mới chuyển sang:

```text
save/load local
 -> GiangHo progress
 -> đội hình/trang bị/võ công
 -> battle generator thật
 -> reward/progression
```

Không ưu tiên giai đoạn đầu: nạp tiền, Soha account thật, chat, bang hội/PvP online, leaderboard, liên server.

## Không lưu trong repo

Repo không chứa APK gốc, full asset dump, credential hay keystore. Chỉ lưu code tự viết, tài liệu reverse và fixture tối thiểu phục vụ nghiên cứu tương thích.
