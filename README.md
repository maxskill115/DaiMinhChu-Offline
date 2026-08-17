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
 -> BeginCutsceneForm hoặc load nhân vật đã save
 -> /SelectStartNhanVat
 -> Home (Form 3)
 -> Giang Hồ (Form 4)
 -> Battle.asmx/GiangHo
 -> BattleForm (Form 7)
 -> BattleReplay 1v1 / 1 hiệp / 1 đòn thường
 -> result panel
 -> save sao / mở mission kế / bạc
```

Transport: **HTTP + JSON bọc AES-128-CBC/PKCS7**.

Core config nhân vật/trang bị/võ công/Giang Hồ... có sẵn trong Unity `Resources`; `/Login` local có thể để `LoginCfg=null` để bỏ remote config update.

Server hiện có **JSON save local** cho nhân vật, account cơ bản và tiến trình Giang Hồ. `giangho.Nhiemvu` đã xác nhận là JSON string; `S` là best-star, `T` là lượt đã đánh. Embedded config có **92 chapter / 1405 mission**, server chỉ giữ structural mission counts.

Server đã được **unit-test + encrypted HTTP smoke-test**, gồm save/reload và `Battle.asmx/GiangHo`.

> **Android/client runtime vẫn PENDING.** Chưa được coi là đã vào game/phát trận thành công cho tới khi chạy APK thật với server + `adb logcat`.

## Thành phần repo

- [`HANDOFF.md`](HANDOFF.md) — nguồn trạng thái chính; chat mới đọc file này trước.
- [`docs/protocol/login.md`](docs/protocol/login.md) — login / CheckUser / GetUserInfo / AES.
- [`docs/protocol/first-character.md`](docs/protocol/first-character.md) — BeginCutsceneForm / SelectStartNhanVat.
- [`docs/protocol/giangho-battle.md`](docs/protocol/giangho-battle.md) — Giang Hồ, Battle.asmx, DTO và replay tối thiểu.
- [`server/state.py`](server/state.py) — JSON save + progression.
- [`server/`](server/) — Python compatibility server + unit/smoke tests.
- [`tools/patch_client.py`](tools/patch_client.py) — patch APK 8.0.2 bỏ Soha SDK login và trỏ server về local.

## Milestone quan trọng tiếp theo

```text
APK patched + Android/emulator
 -> xác nhận Login/Home runtime
 -> mở Giang Hồ
 -> client gửi Battle.asmx/GiangHo
 -> client phát replay
 -> result panel
 -> quay lại Giang Hồ và thấy sao + mission kế mở
 -> restart server/game và xác nhận save được load lại
```

Sau runtime pass: mở rộng đội hình/trang bị/võ công, reward/progression chuẩn hơn và battle generator thật.

Không ưu tiên giai đoạn đầu: nạp tiền, Soha account thật, chat, bang hội/PvP online, leaderboard, liên server.

## Không lưu trong repo

Repo không chứa APK gốc, full asset dump, credential hay keystore. Chỉ lưu code tự viết, tài liệu reverse và fixture tối thiểu phục vụ nghiên cứu tương thích.
