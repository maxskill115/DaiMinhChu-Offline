# Protocol — Login / CheckUser / GetUserInfo

> Trạng thái: **CONFIRMED bằng static IL/metadata** từ APK Việt Nam 8.0.2, SHA-256 `2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194`.

## 1. Base login URL gốc

`HTTP::.ctor` hard-code:

```text
http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx
```

Client nối path vào base URL, ví dụ:

```text
/Login
/CheckUser
/GetUserInfo
```

`CheckUser` nhận URL server được chọn rồi gán URL đó thành `HTTP.LobbyURL`. Vì vậy `HTTPLoginResponse.Servers[].Url` quyết định host cho `/CheckUser` và các request lobby tiếp theo.

## 2. Mã hóa transport

### Request

`HTTP.SendRequest(url, json, callback, showLoading)` làm đúng chuỗi sau:

1. `cipher = aes.Encrypt(json)`
2. `escaped = WWW.EscapeURL(cipher)`
3. body raw UTF-8: `data=` + `escaped`
4. `new WWW(url, postBytes)`

Tức request không gửi JSON plaintext.

### Response

Các coroutine như `WaitForLogin`, `WaitForCheckUser`, `WaitForGetUserInfo` đọc:

```text
www.text -> Aes.Decrypt(...) -> JsonMapper.ToObject<T>(...)
```

Response body vì vậy phải là **Base64 AES ciphertext thuần**, không bọc `data=`.

### AES đã xác nhận

Class `Aes` dùng `RijndaelManaged`:

```text
Mode      = CBC
Padding   = PKCS7
KeySize   = 128
BlockSize = 128
Encoding  = UTF-8
```

Default constructor lấy cùng một mảng 16 byte làm Key và IV.

```text
HEX:    03 05 1f 02 05 06 03 15 06 17 05 20 2a 1f 56 20
Base64: AwUfAgUGAxUGFwUgKh9WIA==
```

Key = IV = byte array trên.

## 3. `/Login`

### Client method

`HTTP::Login(OnRequest callback, string user, string pass)`:

```text
request = new HTTPLoginRequest()
request.User = user
request.Pass = pass
request.Version = GameManager.VERSION
json = JsonMapper.ToJson(request)
url = LoginURL + "/Login"
HTTP.UserInfo.User = user
SendRequest(url, json, callback, true)
```

### `HTTPLoginRequest`

Public property/schema suy ra trực tiếp từ metadata:

```text
User        : string
Pass        : string
AccessToken : string
Platform    : string
Version     : int32
```

Nhánh login thường chỉ set `User`, `Pass`, `Version`.

Nhánh Soha login set `User`, `AccessToken`, `Version` sau khi gọi API Soha ngoài game.

### `HTTPLoginResponse`

```text
ListUserServer   : List<int>
ErrorCode        : HTTP_ERROR_CODE
Token            : string
UserId           : string
SohaToken        : string
Servers          : List<ServerInfo>
ErrorMsg         : string
UrlUpdateAndroid : string
UrlIphoneAppstore: string
UrlIphoneJb      : string
UrlWPJb          : string
LoginCfg         : LoginConfig
```

`ServerInfo`:

```text
ServerID : int32
Name     : string
Url      : string
Status   : string
```

### Success code

`WaitForLogin.MoveNext` so sánh:

```text
ErrorCode == 1  => success
ErrorCode == 11 => VERSION_KHONG_DU / hiện popup update
```

Do đó **success = 1**.

Khi login success:

```text
HTTP.loginResponse = response
HTTP.UserInfo.AccessToken = response.Token
HTTP.UserInfo.PublisherUserDisplayName = response.ErrorMsg
StartCoroutine(GameManager.DownloadConfigAndCache())
```

### Cách bỏ tải config online

`GameManager.DownloadConfigAndCache` có nhánh đặc biệt:

```text
if (HTTP.LoginResponse.LoginCfg == null) {
    LoginForm.OnLoginSuccess();
    yield return null;
    stop;
}
```

Vì vậy local server có thể trả:

```json
"LoginCfg": null
```

để **không tải AssetBundle config từ server cũ** và chuyển thẳng sang form chọn server.

## 4. Soha login ngoài game

APK còn flow `HTTP.DirectLoginSoha` gọi HTTPS:

```text
https://soap.soha.vn/api/a/GET/auth/login?app_id=ba4b944aee28ea8b5c675ad0542f97f3&email={0}&password={1}&gver=2.0.0&sdkver=0.0.0&clientname=sohagame
```

Password được UTF-8 -> Base64 trước khi format URL.

Nếu API này trả `status == "success"`, client lấy:

```text
user_info.id
access_token
```

rồi tạo `HTTPLoginRequest` và gọi `/Login`.

Tuy nhiên `LoginForm.OnLoginBtnClick` trong bản Android hiện tại gọi `SohaSDKManager.Login()` thông qua Java plugin, nên để offline hoàn toàn sẽ cần **bypass/patch SohaSDKManager login** hoặc gọi thẳng `HTTP.Login`.

## 5. `/CheckUser`

### Client method

`HTTP::CheckUser(OnRequest callback, string serverUrl)`:

```text
LobbyURL = serverUrl
request.User  = HTTP.UserInfo.User
request.Token = HTTP.UserInfo.AccessToken
json = JsonMapper.ToJson(request)
SendRequest(LobbyURL + "/CheckUser", json, callback, true)
```

### `HTTPCheckUserRequest`

```text
User  : string
Token : string
```

### `HTTPCheckUserResponse`

Các property quan trọng đã xác nhận:

```text
LoginMessage      : List<string>
EventAnGaLuotCount: int32
ErrorCode         : HTTP_ERROR_CODE
Aid               : int32
UserInfo          : HTTPGetUserInfoResponse
ErrorMsg          : string
ServerID          : int32
```

Ngoài ra class còn field `servers : ServerInfo`.

Success cũng là `ErrorCode == 1`.

Khi success:

```text
HTTP.checkUserResponse = response
HTTP.UserInfo.AID = response.Aid
SelectServerForm.OnLobbyLoginSuccess()
```

## 6. Sau CheckUser

`SelectServerForm.OnLobbyLoginSuccess`:

1. lưu server id vào PlayerPrefs;
2. nếu server chưa có trong `LoginResponse.ListUserServer` thì có thể gọi `UserAppendServer`;
3. gọi `GameManager.LoadAllUserInfo(HTTP.WaitForGetUserInfo)`.

Để tránh request `UserAppendServer` trong prototype, local `/Login` nên để server offline ID `1` nằm trong:

```json
"ListUserServer": [1]
```

## 7. `/GetUserInfo`

### Request

`HTTP::GetUserInfo(callback, string[] properties)` tạo:

```text
Aid      = HTTP.UserInfo.AID
Token    = HTTP.UserInfo.AccessToken
Property = List<property>
```

`property`:

```text
Name : string
```

Sau đó gửi tới:

```text
LobbyURL + "/GetUserInfo"
```

### Property list được request khi login đầy đủ

`GameManager.LoadAllUserInfo` truyền đúng 21 tên:

```text
account
nhanVat
trangBi
voCong
orb
vatPhamTieuThu
giaTriThoiGian
doiHinh
giangHo
tanChuong
honNhanVat
mail
banbe
danhhieu
danhson
serverinfo
lienminh
kimcham
moiruou
longchau
amkhi
```

### `HTTPGetUserInfoResponse`

Các property chính:

```text
ServerInfo      : serverinfo
MoiRuou         : moiruou
KimCham         : List<kimcham>
LienMinh        : lienminh
DanhHieu        : danhhieu
Account         : account
NhanVat         : List<nhanvat>
HonNhanVat      : List<honNV>
TrangBi         : List<trangbi>
VoCong          : List<vocong>
Orb             : List<orb>
VatPhamTieuThu  : List<vatphamtieuthu>
DoiHinh         : doihinh
GiaTriThoiGian  : giatrithoigian
TanChuong       : List<tanchuong>
ErrorCode       : HTTP_ERROR_CODE
LuanKiem        : luankiem
GiangHo         : List<giangho>
DanhSon         : List<danhson>
Mails           : List<HTTPMail>
BanBe           : List<banbe>
LongChau        : List<longchau>
AmKhi           : List<amkhi>
ErrorMsg        : string
```

### Tối thiểu để flow không null ngay

`WaitForGetUserInfo` success branch dùng ngay:

```text
response.GiaTriThoiGian.TimeServer
response.Account.DisplayName
response.Account.Level
response.NhanVat
```

Nếu `NhanVat == null` hoặc `NhanVat.Count == 0`, client chuyển sang **FormName index 13** (nhánh tạo/chọn nhân vật ban đầu).

Nếu `NhanVat.Count > 0`, client chuyển sang **FormName index 3** (main gameplay flow) rồi đọc thêm nhiều dữ liệu khác.

Vì vậy milestone đầu tiên nên cố tình trả `NhanVat: []` để giảm số schema phải dựng và xác nhận login -> CheckUser -> GetUserInfo -> form tạo nhân vật trước.

## 8. Prototype response đề xuất

### `/Login`

```json
{
  "ListUserServer": [1],
  "ErrorCode": 1,
  "Token": "offline-token",
  "UserId": "offline-user",
  "SohaToken": "",
  "Servers": [
    {
      "ServerID": 1,
      "Name": "Offline",
      "Url": "http://<LOCAL-IP>:8000",
      "Status": "online"
    }
  ],
  "ErrorMsg": "Offline",
  "UrlUpdateAndroid": "",
  "UrlIphoneAppstore": "",
  "UrlIphoneJb": "",
  "UrlWPJb": "",
  "LoginCfg": null
}
```

### `/CheckUser`

```json
{
  "LoginMessage": [],
  "EventAnGaLuotCount": 0,
  "ErrorCode": 1,
  "Aid": 1,
  "UserInfo": null,
  "ErrorMsg": "",
  "ServerID": 1
}
```

### `/GetUserInfo` — milestone tạo nhân vật

```json
{
  "ErrorCode": 1,
  "ErrorMsg": "",
  "Account": {
    "DisplayName": "Offline",
    "Level": 1
  },
  "GiaTriThoiGian": {
    "TimeServer": "2026-08-18 00:00:00",
    "LatTheBai": 0
  },
  "NhanVat": []
}
```

`DateTime` format trên cần test runtime thực tế với LitJson của client; nếu deserialize không nhận thì sẽ reverse exporter/importer DateTime cụ thể.

## 9. Blocker kế tiếp

1. Client Android hiện gọi Java Soha SDK khi bấm login; cần patch/bypass để gọi `HTTP.Login` trực tiếp.
2. Cần redirect/patch `loginURL` cũ sang local server.
3. Sau đó mới test thật 3 endpoint trên thiết bị/emulator.
