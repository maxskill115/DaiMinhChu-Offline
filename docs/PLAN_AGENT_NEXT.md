# PLAN CHO AI AGENT TIẾP TỤC — DaiMinhChu-Offline

> Mục tiêu của plan này là để một AI agent mới có thể tiếp tục công việc ngay, không phải hỏi lại người dùng và không lặp lại kiểu sửa từng lỗi bằng phỏng đoán.

## 0. Đọc trước khi làm

BẮT BUỘC đọc theo thứ tự:

1. `HANDOFF.md`
2. `docs/protocol/runtime-dto-audit.md`
3. `server/app.py`
4. `server/state.py`
5. `server/static_endpoints.py`
6. `server/test_server.py`
7. `server/test_endpoint_audit.py`
8. `server/test_runtime_transport.py`

Không được coi stub hiện tại là gameplay hoàn chỉnh.

Phải giữ phân loại:

- **CONFIRMED STATIC** = xác nhận từ APK / Assembly-CSharp.dll.
- **SERVER TESTED** = unit/integration local đã pass.
- **CONFIRMED RUNTIME** = đã thấy client thật chạy trên LDPlayer.
- **HYPOTHESIS** = suy luận, chưa xác nhận.

Sau mỗi milestone phải cập nhật `HANDOFF.md`.

---

# 1. MỤC TIÊU TỔNG THỂ

Phục dựng client Đại Minh Chủ Việt Nam 8.0.2 chạy local/offline với backend tương thích càng đầy đủ càng tốt.

Không chỉ mục tiêu “không crash”; mỗi tính năng phải đạt đủ:

1. endpoint đúng;
2. transport đúng GET/POST + AES;
3. request DTO đúng;
4. response DTO đúng;
5. dữ liệu non-null/non-empty đúng chỗ client dereference;
6. state/persistence đúng;
7. UI client hiển thị đúng;
8. hành động gameplay tạo thay đổi state thật;
9. test tự động bảo vệ regression.

Hiện static endpoint coverage đã là **277/277**, nên KHÔNG tiếp tục làm kiểu “click rồi mới tìm endpoint”. Từ giờ tập trung vào DTO + semantics + config key + persistence.

---

# 2. MỐC HIỆN TẠI

## Client

- APK 8.0.2.
- Unity 4.x / Mono / ARMv7.
- Direct login patch hoạt động.
- `SohaSDKManager.SetUserInfo` đã no-op đúng.
- LDPlayer 32-bit vào được Home.

## Backend

- server branch hiện tại: `main`.
- server target version: `DMCOffline/0.11`.
- static client endpoint inventory: 277 endpoint.
- GM web đã chạy runtime.
- login / checkuser / getuserinfo hoạt động runtime.

## Error-code convention quan trọng

Uppercase family:

```text
ErrorCode = 1 => success
ErrorCode = 0 => failure
```

Lowercase family:

```text
errorCode = 0 => success
errorCode != 0 => failure
```

Không được trộn 2 convention.

---

# 3. ƯU TIÊN P0 — ỔN ĐỊNH SERVER / TRANSPORT TRƯỚC

## Task P0.1 — Xác minh user thực sự chạy server 0.11

Runtime log mới vẫn có:

```text
java.io.FileNotFoundException:
.../User.asmx/ChatGet
```

trong khi unit regression của 0.11 đã test GET `/ChatGet` trả 200 encrypted.

Vì vậy phải loại trừ server cũ / process cũ / code chưa pull.

### Agent phải làm

1. Kiểm tra `server/app.py` đang báo version 0.11.
2. Kiểm tra `do_GET()` có route game endpoint.
3. Viết thêm endpoint debug nếu cần:

```text
/health
/debug/routes
```

`/debug/routes` chỉ localhost, trả:

- server_version
- process pid
- startup timestamp
- exact route count
- static endpoint count
- hash của `app.py` hoặc git commit env nếu có

4. Log request phải ghi cả method + path:

```text
GET /Server/Webservice/User.asmx/ChatGet
POST /Server/Webservice/.../X
```

5. Nếu `ChatGet` GET vẫn 404 với server 0.11 thật, tái hiện bằng local HTTP test và sửa handler.

### Acceptance

- `python -m unittest -v` sạch.
- local GET `/ChatGet` trả AES response HTTP 200.
- runtime LDPlayer mở Luyện Công không còn `ChatGet FileNotFoundException`.

---

# 4. ƯU TIÊN P1 — REVERSE DTO/DATA CHO CÁC BLOCKER HIỆN TẠI

## Task P1.1 — Mở tướng / LayNhanVat

Hiện trạng:

- 0.10: không crash nhưng bấm Thu nhận không hiện tướng.
- 0.11 đã sửa `errorCode=0` success.

### Việc cần làm

1. Reverse `HTTP.WaitForLayNhanVat` IL đầy đủ.
2. Xác định chính xác:
   - field nào chứa code nhân vật;
   - `GetIdx` dùng thế nào;
   - `ListEventHon` format gì;
   - `UpdateUserInfo` cần chứa group nào.
3. Reverse `NhanVatPopup.CreateOnGetNewNhanVat` và `BigNhanVatAvatar.SetByName`.
4. Không chỉ dùng 3 starter code. Phải lấy danh sách code hợp lệ từ embedded `NhanVat` config.
5. Viết recruitment pool local.
6. Khi recruit:
   - trừ currency đúng loại;
   - thêm hero vào save;
   - nếu trùng hero thì xử lý hồn/event đúng client mong đợi;
   - trả đúng popup/result.

### Acceptance

- bấm Thu nhận thấy popup/tướng thật;
- hero mới xuất hiện trong danh sách;
- currency thay đổi đúng;
- restart server vẫn còn hero.

---

## Task P1.2 — Niên Thú

Runtime mới CONFIRMED:

```text
KeyNotFoundException
Dictionary<string,int>.get_Item
NienThuItem.SetGUI(HTTPNienThuResponse)
```

và khi auto:

```text
AutoTuLinhPopup.StartGame
StartAutoNienThu
WaitForGetNienThuInfoAuto
```

### Không được làm

Không đoán `BossName`/dictionary key rồi thử từng giá trị.

### Việc cần làm

1. Disassemble IL của:
   - `NienThuItem.SetGUI`
   - `NienThuItem.Update`
   - `NienThuForm.SetGUI`
   - `AutoTuLinhPopup.StartGame`
   - iterator `WaitForGetNienThuInfoAuto`
2. Xác định dictionary nào bị lookup.
3. Trace nguồn dictionary được populate từ Resource config nào.
4. Dump đúng key set từ embedded config.
5. Map `HTTPNienThuResponse` fields vào key client dùng.
6. Dựng response minimal nhưng **semantically valid**, không chỉ non-null.
7. Sau đó mới implement battle/auto state.

### Acceptance

- mở Niên Thú không còn KeyNotFoundException;
- 4 boss/items render được;
- Auto Tu Luyện không crash;
- nếu gameplay chưa hoàn chỉnh thì UI phải ở trạng thái hợp lệ, không fake success.

---

## Task P1.3 — Kỳ Ngộ

Runtime cũ:

```text
NullReferenceException
KyNgoForm.CreateDocCoPage
KyNgoForm.CreateNormalPage
KyNgoForm.CreateUI
KyNgoForm.SyncWithNetworkData
```

### Việc cần làm

1. Reverse toàn bộ `KyNgoForm.SyncWithNetworkData` và các `Create*Page`.
2. Liệt kê data source của từng page.
3. Xác định data đến từ:
   - embedded config;
   - GetUserInfo property;
   - endpoint riêng.
4. Với mỗi page, tạo fixture chính xác tối thiểu.
5. Viết test cho nested data non-null + required key.

### Acceptance

- mở Kỳ Ngộ không NullReference;
- các page render hợp lệ;
- action nào chưa làm thì controlled disabled/error, không crash.

---

# 5. ƯU TIÊN P2 — LÀM LẠI CÁC FEATURE ĐANG CHỈ LÀ STUB

## P2.1 — Giang Hồ

Hiện Giang Hồ chỉ là compatibility fixture.

Phải reverse từ embedded `GiangHo` config để map đúng:

- chapter;
- mission;
- NPC roster;
- số lượng NPC;
- HP/stat;
- reward;
- drop item;
- star condition;
- số lượt;
- unlock;
- quick battle.

### Việc cần làm

1. Viết tool dump structured `ConfigFile/GiangHo`.
2. Map mission index server <-> config.
3. Reverse BattleReplay generation đủ cho nhiều fighter, không chỉ 1v1.
4. Reward phải persist:
   - bạc;
   - EXP môn phái;
   - EXP nhân vật;
   - item/drop;
   - lượt/thể lực.
5. `DanhNhanhGiangHo` phải dùng cùng reward engine, không duplicate logic.
6. `ResetTurnNhiemVuGH` phải thật sự reset đúng lượt nếu client dùng.

### Acceptance

- 2 ải khác nhau có đội NPC khác nhau đúng config;
- thưởng hiển thị và cộng thật;
- đánh nhanh 10 lần hoạt động;
- restart giữ progress.

---

## P2.2 — Cửa hàng / Lễ bao

Hiện `BuyLeBao` có thể hiện popup thành công nhưng reward trống.

### Việc cần làm

1. Reverse request/response DTO của:
   - `BuyLeBao`
   - `BuyVatPhamTieuThu`
   - các endpoint shop liên quan trong 277 inventory.
2. Reverse UI callback popup reward.
3. Xác định item representation client mong đợi.
4. Xây inventory helper chung trong `state.py`.
5. Transaction phải atomic:
   - check currency;
   - trừ currency;
   - add item;
   - persist;
   - trả UpdateUserInfo / reward DTO đúng.

### Acceptance

- popup hiện đúng reward;
- inventory tăng;
- KNB/vàng/bạc giảm đúng;
- không thể mua khi thiếu tiền.

---

## P2.3 — Luyện Công / Niên Thú / Đồng Nhân / Huyết Chiến

Không chỉ trả skeleton.

Reverse form callback + DTO semantics cho từng feature:

- `GetMiniBossInfo`
- `GetDongNhanInfo`
- `GetHuyetChienInfo`
- `GetNienThuInfo`
- các endpoint đánh/buy/respawn/claim liên quan.

Tạo state riêng cho từng mode.

---

## P2.4 — Luận Kiếm

`GetAnhHungBang` hiện skeleton.

Reverse:

- leaderboard DTO;
- opponent data;
- refresh;
- challenge;
- rank points;
- rewards;
- NPC exchange.

Dùng local deterministic NPC list để offline nhưng phải đúng DTO/config key.

---

## P2.5 — Liên Minh / Bang Chiến

Hiện chưa có alliance state thật.

Phải xây local single-player alliance model tối thiểu:

- create alliance;
- membership;
- member list;
- contribution;
- alliance info;
- Bang Chiến fixture;
- persistence.

Không fake `success + null`.

---

# 6. ƯU TIÊN P3 — HỆ THỐNG HÓA REVERSE ENGINEERING

Đây là phần quan trọng để giảm số lần user phải test tay.

## P3.1 — Tool dump DTO tự động

Viết `tools/dump_dto_metadata.py` đọc `Assembly-CSharp.dll` và xuất:

```text
DTO type
field/property
CLR type
endpoint references
iterator/callback references nếu tìm được
```

Output JSON + Markdown.

Mục tiêu: endpoint nào cũng có schema index, không tra thủ công lại.

---

## P3.2 — Tool map endpoint -> request -> response -> callback

Viết static analysis report:

```text
endpoint
HTTP method
request DTO
response DTO
WaitFor... iterator
success callback
error callback
forms/classes consuming response
```

Nếu static analysis không xác định chắc chắn thì label HYPOTHESIS.

---

## P3.3 — Config inventory

Dump toàn bộ embedded config names và dictionary keys quan trọng:

- NhanVat
- TrangBi
- VoCong
- GiangHo
- HuyetChien
- KimCham
- LongChau
- AmKhi
- NienThu / DongNhan / event config nếu có
- localization

Không commit full proprietary asset dump; chỉ commit code/tool và schema/key summaries cần thiết.

---

## P3.4 — Runtime trace logging

Server log mỗi request thành structured JSONL:

```json
{
  "time":"...",
  "method":"GET",
  "route":"ChatGet",
  "request":{},
  "response":{},
  "handler":"exact|static_stub",
  "server_version":"0.11"
}
```

Tạo `local_data/runtime_trace.jsonl` và ignore git.

Viết `tools/summarize_runtime_trace.py` để báo:

- endpoint nào gọi nhiều;
- endpoint nào unsupported;
- endpoint nào ErrorCode failure;
- endpoint nào chưa exact handler.

Như vậy user chỉ cần test 1 vòng lớn, agent có thể đọc trace rồi xử lý hàng loạt.

---

# 7. TEST STRATEGY BẮT BUỘC

Mỗi feature mới phải có 3 tầng test nếu áp dụng được:

## Static contract test

- exact field names;
- exact casing;
- exact route name;
- exact error-code convention.

## State test

- action làm thay đổi save đúng;
- persistence qua reload;
- invalid action không mutate state.

## Transport test

- GET/POST đúng;
- AES encrypt/decrypt;
- HTTP status đúng;
- content đúng client expectation.

Không merge/commit feature mới nếu test cũ bị fail mà chưa giải thích.

---

# 8. QUY TẮC KHÔNG ĐƯỢC LẶP LẠI

1. Không thêm field “cho chắc” vào DTO nếu metadata không có.
2. Không dùng `ErrorCode=1` cho lower-case family.
3. Không trả success với nested object null nếu callback dereference.
4. Không gọi route generic success để che lỗi.
5. Không hard-code random code name nếu client lookup dictionary config.
6. Không sửa APK lại nếu lỗi chỉ nằm server DTO/state.
7. Không yêu cầu user test từng nút nếu có thể static reverse trước.
8. Không coi “UI mở được” là feature hoàn chỉnh.

---

# 9. THỨ TỰ THỰC THI ĐỀ XUẤT CHO AGENT

Agent nên làm liên tục theo thứ tự sau, không cần hỏi lại user giữa từng bước trừ khi thiếu artifact thật sự:

### Phase A — Stabilize

- xác minh 0.11 GET transport;
- fix `ChatGet` runtime 404;
- thêm process/version diagnostics;
- toàn bộ unit tests xanh.

### Phase B — Reverse current blockers

- LayNhanVat callback + recruit result;
- NienThu dictionary key;
- KyNgo data source;
- unsupported endpoint list từ trace/server logs.

### Phase C — Feature correctness

- GiangHo config-driven battle/reward;
- quick battle;
- shops/reward/inventory;
- LuyenCong modes;
- LuanKiem;
- alliance/bang chien.

### Phase D — Tooling

- DTO dumper;
- endpoint/callback mapper;
- config key dumper;
- runtime trace summarizer.

### Phase E — Broad runtime validation

Chỉ sau khi static + server tests tốt mới nhờ user test một vòng toàn bộ menu.

---

# 10. DEFINITION OF DONE CHO MỘT FEATURE

Chỉ đánh dấu feature `CONFIRMED RUNTIME` khi:

- mở UI không exception;
- request/response qua đúng endpoint;
- action chính hoạt động;
- reward/currency/inventory/state thay đổi đúng;
- restart không mất state;
- không hiện `Offline backend ... not reconstructed yet` trong luồng chính;
- unit tests cho feature pass;
- HANDOFF cập nhật.

---

# 11. MỆNH LỆNH CHO AI AGENT MỚI

> Đọc `HANDOFF.md` và file plan này trước. Tiếp tục trực tiếp trên repo `maxskill115/DaiMinhChu-Offline`. Không hỏi lại người dùng những gì đã có trong repo/log. Trước tiên xác minh server 0.11 và sửa triệt để `ChatGet` GET runtime mismatch. Sau đó reverse `NienThuItem.SetGUI`/`AutoTuLinhPopup.StartGame` từ Assembly để tìm exact dictionary key thay vì đoán. Tiếp theo reverse `LayNhanVat` callback và `KyNgoForm` data dependencies. Luôn ưu tiên static reverse + automated tests trước runtime manual test. Khi code xong thì chạy test, commit, cập nhật `HANDOFF.md`, rồi mới yêu cầu user test một vòng lớn.