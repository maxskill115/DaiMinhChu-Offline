# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu

Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** chạy local/offline, giữ client/UI/assets gốc càng nhiều càng tốt. Hướng chính: clean-room local compatibility backend + client patch tối thiểu.

## 2. APK / client

```text
package: vn.sohagame.dminhchu
version: 8.0.2
size: 52,568,975
SHA256: 2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194
Unity 4.x / Mono / ARMv7
Assembly-CSharp.dll: assets/bin/Data/Managed/Assembly-CSharp.dll
```

Client patch hiện tại:

1. login URL -> local server;
2. `LoginForm.OnLoginBtnClick` bỏ Soha login, gọi HTTP Login trực tiếp;
3. `SohaSDKManager.SetUserInfo` -> `RET + NOP` để bỏ NPE từ legacy Soha SDK.

Signed v2 đã verify:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
v1/v2/v3 signature = true
```

LDPlayer 64-bit không ổn; **test chính dùng LDPlayer 32-bit**.

## 3. Runtime đã xác nhận

**CONFIRMED RUNTIME** trên LDPlayer 32-bit:

```text
StartForm
-> LoginForm
-> SelectServerForm
-> /Login
-> /CheckUser
-> /GetUserInfo
-> BeginCutsceneForm
-> /SelectStartNhanVat
-> HomeForm
-> GiangHoForm
-> BattleForm
-> BattleReplay chạy
-> quay lại GiangHo/Home
```

Giang Hồ là gameplay đầu tiên chạy được thật.

Runtime log còn có:

```text
Can not get nhiem vu Info from giang ho 0, nhiem vu 0
```

nhưng battle replay vẫn chạy.

## 4. Transport / protocol

```text
LitJson JSON -> AES-128-CBC PKCS7 -> Base64 -> form data=<cipher>
response -> AES decrypt -> LitJson
Key = IV = 03051f0205060315061705202a1f5620
```

User URL hiện dùng:

```text
http://192.168.1.14:8000/Server/Webservice/User.asmx
```

Battle URL derive `User.asmx` -> `Battle.asmx`.

## 5. Server hiện tại

`server/app.py` version hiện: **DMCOffline/0.6**.

Core endpoint:

```text
/Login
/CheckUser
/GetUserInfo
/SelectStartNhanVat
/Battle.asmx/GiangHo
```

Compatibility endpoint runtime-discovered đã có stub:

```text
/GetSystemHighLight
/GetMiniBossInfo
/LayNhanVat
```

Ba endpoint trên mới là stub/snapshot an toàn, **chưa gọi là feature hoàn chỉnh**.

Server save:

```text
server/local_data/save.json
```

GiangHo progress:

```text
Nhiemvu = JSON string [{S,T},...]
S = best stars
T = lượt đánh
92 chapter / 1405 mission structural counts
```

## 6. GM TOOL — CONFIRMED RUNTIME

GM web:

```text
http://127.0.0.1:8000/gm
```

User đã runtime-test và xác nhận GM sửa được account thật trong client:

```text
VIP -> 8
Vàng/KNB -> 10000
```

=> **CONFIRMED RUNTIME:** GM -> save -> `/GetUserInfo` -> client refresh hoạt động cho ít nhất VIP và Vàng/KNB.

GM hỗ trợ account/level/exp/VIP/Bạc/Vàng, lượt/thể lực, starter, hero raw, group editor, add item, raw save và reset active account.

## 7. APK WORKSPACE TOOL — IMPLEMENTED

```text
tools/apk_workspace.py
```

Commands:

```bat
python tools\apk_workspace.py unpack daiminhchu.apk apk_workspace --clean
python tools\apk_workspace.py scan apk_workspace
python tools\apk_workspace.py repack apk_workspace DMC_mod_unsigned.apk
```

Unity serialized assets/bundles vẫn là binary; muốn export/import texture/audio/animation/prefab/effect cần AssetRipper/UABE/UnityPy ngoài tool rồi thay lại file binary đúng vị trí.

## 8. Runtime test mới 12:45 — từng chức năng

User đã vào game ổn và bắt đầu test từng chức năng một.

### Mở tướng / LayNhanVat

Ảnh runtime: mở tướng hiện loading `Đang kết nối` vô hạn và không nhận tướng.

Server đã có `/LayNhanVat` stub nhưng runtime cho thấy **response shape/flow hiện chưa đủ đúng để client hoàn tất recruit**.

Trạng thái:

```text
ENDPOINT EXISTS
RUNTIME REQUEST/RESPONSE SHAPE NEEDS REVERSE
NOT FUNCTIONAL YET
```

Ưu tiên hiện tại: sửa **Mở tướng** trước, không sửa hàng loạt feature cùng lúc.

Cần capture đúng một lần bấm Mở tướng với:

```text
server console: LayNhanVat request + response
adb logcat: các dòng Unity quanh LayNhanVat / exception / callback
```

Không đoán DTO tiếp nếu chưa có exact runtime evidence.

### Endpoint mới nhìn thấy trực tiếp từ popup runtime

Ảnh Hoạt động/Liên minh cho thấy 404:

```text
User.asmx/GetInfoLienMinh
```

Ảnh một màn tỷ thí/hoạt động khác cho thấy 404 endpoint đọc được gần như:

```text
User.asmx/CoHatGet
```

Tên `CoHatGet` cần xác nhận lại bằng server log/logcat trước khi implement vì chữ popup bị UI che/mờ.

=> `GetInfoLienMinh` là **CONFIRMED RUNTIME endpoint name** từ popup rõ; chưa implement.

## 9. Việc cần làm NGAY

Chỉ xử lý **Mở tướng** trước.

1. Clear logcat.
2. Mở server console.
3. Vào game -> Chợ/Mở tướng -> bấm đúng 1 lần.
4. Chờ 3-5 giây.
5. Gửi:
   - các dòng server có `LayNhanVat request:` và `LayNhanVat response:`;
   - logcat từ lúc bấm tới lúc spinner treo.

Sau khi xác định DTO/callback chính xác mới sửa `/LayNhanVat`, thêm unit test rồi runtime retest. Khi Mở tướng pass mới chuyển sang `GetInfoLienMinh`, rồi endpoint tiếp theo.

## 10. Quy tắc dự án

- Phân biệt rõ: `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema item rồi coi như confirmed.
- Test từng feature một để attribution rõ.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
