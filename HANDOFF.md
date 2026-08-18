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

Compatibility endpoint runtime-discovered:

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

## 6. GM TOOL — IMPLEMENTED, WINDOWS TEST PENDING

Mới thêm:

```text
server/gm.py
```

Chạy server rồi mở trên PC:

```text
http://127.0.0.1:8000/gm
```

GM được **giới hạn localhost**; game API vẫn listen `0.0.0.0` cho LDPlayer/LAN.

GM hiện hỗ trợ:

- tên account;
- Level / Exp / ExpMax;
- VIP;
- Bạc;
- Vàng/KNB qua `Account.Vang` hiện có;
- `LuotNV`, `LuotNVMax`, `LuotTD`, `LuotTDMax`, `LatTheBai`;
- đặt starter chính + level/exp;
- thêm hero record raw JSON;
- raw group editor + add-item cho:

```text
TrangBi
VoCong
Orb
VatPhamTieuThu
TanChuong
HonNhanVat
Mail
Banbe
DanhHieu
DanhSon
ServerInfo
LienMinh
KimCham
MoiRuou
LongChau
AmKhi
```

- raw save editor;
- tạo/reset active local test account với tên mới.

**Quan trọng:** đây là GM framework/harness rộng, không phải tất cả DTO item đã reverse hoàn chỉnh. Các record TrangBi/VoCong/KimCham/... vẫn cần reverse chính xác field/type từ `Assembly-CSharp.dll` và runtime. Raw JSON editor cho phép test ngay khi schema mới được phát hiện.

Để tránh regression, group mặc định rỗng không tự động được nhét vào `/GetUserInfo`; chỉ group đã bị GM chỉnh khác mặc định mới được trả về client.

Tài liệu:

```text
docs/gm-tool.md
```

## 7. APK WORKSPACE TOOL — IMPLEMENTED

Mới thêm:

```text
tools/apk_workspace.py
```

Commands:

```bat
python tools\apk_workspace.py unpack daiminhchu.apk apk_workspace --clean
python tools\apk_workspace.py scan apk_workspace
python tools\apk_workspace.py repack apk_workspace DMC_mod_unsigned.apk
```

Tool:

- unpack toàn bộ APK raw;
- tạo `.dmc_apk_manifest.json` lưu compression/timestamp metadata;
- phân loại image/audio/video/config/Unity data/DLL/native lib;
- safe path extraction;
- repack unsigned giữ compression metadata khi có thể;
- bỏ chữ ký cũ trong META-INF;
- optional wrapper cho `apktool-decode` / `apktool-build` nếu apktool có trong PATH.

Unity serialized assets/bundles vẫn là binary; muốn export/import texture/audio/animation/prefab/effect cần AssetRipper/UABE/UnityPy ngoài tool rồi thay lại file binary đúng vị trí.

Tài liệu:

```text
docs/apk-workspace.md
```

Workspace local được `.gitignore`:

```text
apk_workspace/
apktool_out/
```

## 8. Tests

Core server trước đây đã pass 11 tests + encrypted HTTP smoke.

Sau compatibility endpoints đã thêm tests.

GM phase vừa thêm tests cho:

- account/VIP/Vang/Bac/time edit;
- group TrangBi edit;
- add hero/item;
- reset account.

**User chưa pull/run suite mới trên Windows tại thời điểm handoff này.**

## 9. Commit/mốc mới nhất

Các commit mới trong phase GM/APK workspace:

```text
37d8293c  Mở rộng save state cho GM tool
0b437ee0  Thêm giao diện GM local
8e53bbdc  Tích hợp GM web tool vào server
b267e266  Thêm tool unpack/repack APK workspace
67756af0  Thêm test GM state và API
aadb234b  Bỏ qua workspace APK local
00b61547  Tài liệu tool unpack/repack APK
36e7e4a0  Giới hạn GM tool ở localhost
df507c3b  Chỉ trả GM group khi đã chỉnh để tránh đổi runtime mặc định
c1077bd1  Tài liệu GM tool local
```

## 10. Việc cần làm NGAY

User đã yêu cầu hoàn thành 2 task trước khi pull; code đã push. Bước tiếp theo:

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
```

Nếu test pass:

```bat
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

Mở GM:

```text
http://127.0.0.1:8000/gm
```

Test nhanh:

1. đổi Vang/Bac/Vip/LuotNV;
2. vào/reload client xem account refresh;
3. test TrangBi/VoCong bằng raw JSON chỉ sau khi biết schema DTO đúng;
4. thử compatibility endpoints mới: Hoạt động, Luyện Công, Chợ;
5. lấy logcat + server log cho endpoint/schema tiếp theo.

APK workspace test riêng:

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
python tools\apk_workspace.py unpack daiminhchu.apk apk_workspace --clean
python tools\apk_workspace.py scan apk_workspace
```

Sau sửa file:

```bat
python tools\apk_workspace.py repack apk_workspace DMC_mod_unsigned.apk
```

rồi zipalign + sign như pipeline hiện có.

## 11. Quy tắc dự án

- Phân biệt rõ: `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema item rồi coi như confirmed; dùng GM raw editor để test, sau đó reverse chính xác.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
