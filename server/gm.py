from __future__ import annotations

import json
from typing import Any

from state import GM_GROUP_DEFAULTS, START_HEROES, SaveStore


def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def gm_html() -> str:
    starter_options = "".join(f'<option value="{code}">{code}</option>' for code in START_HEROES)
    group_options = "".join(f'<option value="{name}">{name}</option>' for name in GM_GROUP_DEFAULTS)
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DMC GM Tool</title>
<style>
body{{font-family:Segoe UI,Arial;background:#111827;color:#e5e7eb;margin:0}} .wrap{{max-width:1250px;margin:auto;padding:20px}}
h1{{margin:0 0 8px}} .muted{{color:#9ca3af}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-top:16px}}
.card{{background:#1f2937;border:1px solid #374151;border-radius:12px;padding:14px}} label{{display:block;font-size:12px;color:#9ca3af;margin-top:8px}}
input,select,textarea,button{{box-sizing:border-box;width:100%;background:#111827;color:#f9fafb;border:1px solid #4b5563;border-radius:7px;padding:9px}}
button{{cursor:pointer;background:#2563eb;border:0;font-weight:600;margin-top:10px}} button.danger{{background:#b91c1c}} button.alt{{background:#4b5563}}
textarea{{min-height:180px;font-family:Consolas,monospace}} .row{{display:grid;grid-template-columns:1fr 1fr;gap:8px}} #status{{white-space:pre-wrap;background:#0b1220;padding:10px;border-radius:8px;margin-top:12px}}
</style></head><body><div class="wrap">
<h1>Đại Minh Chủ — GM Tool</h1><div class="muted">Chỉ dành cho server local/offline. Thay đổi được lưu thẳng vào save hiện tại.</div>
<div id="status">Đang tải...</div>
<div class="grid">
<div class="card"><h3>Tài khoản / tài nguyên</h3>
<label>Tên</label><input id="DisplayName"><div class="row"><div><label>Level</label><input id="Level" type="number"></div><div><label>VIP</label><input id="Vip" type="number"></div></div>
<div class="row"><div><label>Vàng / KNB (Account.Vang)</label><input id="Vang" type="number"></div><div><label>Bạc</label><input id="Bac" type="number"></div></div>
<div class="row"><div><label>Exp</label><input id="Exp" type="number"></div><div><label>ExpMax</label><input id="ExpMax" type="number"></div></div>
<button onclick="saveAccount()">Lưu tài khoản</button></div>

<div class="card"><h3>Thể lực / lượt chơi</h3>
<div class="row"><div><label>LuotNV</label><input id="LuotNV" type="number"></div><div><label>LuotNVMax</label><input id="LuotNVMax" type="number"></div></div>
<div class="row"><div><label>LuotTD</label><input id="LuotTD" type="number"></div><div><label>LuotTDMax</label><input id="LuotTDMax" type="number"></div></div>
<label>LatTheBai</label><input id="LatTheBai" type="number"><button onclick="saveTime()">Lưu lượt/thể lực</button></div>

<div class="card"><h3>Nhân vật chính</h3><label>Starter</label><select id="starter">{starter_options}</select>
<div class="row"><div><label>Level</label><input id="heroLevel" type="number" value="1"></div><div><label>Exp</label><input id="heroExp" type="number" value="0"></div></div>
<button onclick="setHero()">Đặt nhân vật chính</button>
<h4>Thêm nhân vật raw</h4><textarea id="heroJson">{{"Name":"NV_MaCode","Level":1,"Exp":0}}</textarea><button onclick="addHero()">Thêm nhân vật</button></div>

<div class="card"><h3>Đồ / Võ công / hệ thống</h3><label>Group</label><select id="group">{group_options}</select>
<textarea id="groupJson">[]</textarea><button class="alt" onclick="loadGroup()">Nạp group</button><button onclick="saveGroup()">Ghi đè group</button>
<div class="muted">Dùng raw JSON để test cả TrangBi, VoCong, Orb, vật phẩm, KimCham, LongChau, AmKhi... khi schema đang được reverse dần.</div></div>

<div class="card"><h3>Thêm item nhanh</h3><label>Group list</label><select id="itemGroup">{group_options}</select>
<textarea id="itemJson">{{"Name":"ITEM_CODE","SoLuong":1}}</textarea><button onclick="addItem()">Thêm item</button></div>

<div class="card"><h3>Account test / reset</h3><label>Tên account test mới</label><input id="newName" value="TestGM">
<button class="danger" onclick="resetAccount()">Tạo/reset account local</button><div class="muted">Hiện server vẫn là một active local account; nút này tạo lại save sạch để test nhanh.</div></div>

<div class="card"><h3>Raw save editor</h3><textarea id="rawSave"></textarea><button class="alt" onclick="loadRaw()">Nạp raw save</button><button class="danger" onclick="saveRaw()">Ghi toàn bộ raw save</button></div>
</div></div>
<script>
let state={{}};
async function api(path, body){{const r=await fetch(path,{{method:body?'POST':'GET',headers:{{'Content-Type':'application/json'}},body:body?JSON.stringify(body):undefined}});const t=await r.text();let j;try{{j=JSON.parse(t)}}catch(e){{throw Error(t)}}if(!r.ok||j.ok===false)throw Error(j.error||t);return j;}}
function n(id){{return Number(document.getElementById(id).value||0)}} function v(id){{return document.getElementById(id).value}}
function msg(x){{document.getElementById('status').textContent=typeof x==='string'?x:JSON.stringify(x,null,2)}}
async function refresh(){{try{{state=(await api('/gm/api/state')).state; const a=state.account,t=state.time_values; for(const k of ['DisplayName','Level','Vip','Vang','Bac','Exp','ExpMax'])document.getElementById(k).value=a[k]??''; for(const k of ['LuotNV','LuotNVMax','LuotTD','LuotTDMax','LatTheBai'])document.getElementById(k).value=t[k]??0; if(state.main_hero){{document.getElementById('starter').value=state.main_hero.Name;document.getElementById('heroLevel').value=state.main_hero.Level;document.getElementById('heroExp').value=state.main_hero.Exp;}} loadGroup();loadRaw();msg('GM ready — '+state.save_file)}}catch(e){{msg('ERROR: '+e)}}}}
async function saveAccount(){{try{{await api('/gm/api/account',{{DisplayName:v('DisplayName'),Level:n('Level'),Vip:n('Vip'),Vang:n('Vang'),Bac:n('Bac'),Exp:n('Exp'),ExpMax:n('ExpMax')}});await refresh()}}catch(e){{msg(e.toString())}}}}
async function saveTime(){{try{{await api('/gm/api/time',{{LuotNV:n('LuotNV'),LuotNVMax:n('LuotNVMax'),LuotTD:n('LuotTD'),LuotTDMax:n('LuotTDMax'),LatTheBai:n('LatTheBai')}});await refresh()}}catch(e){{msg(e.toString())}}}}
async function setHero(){{try{{await api('/gm/api/main-hero',{{code:v('starter'),level:n('heroLevel'),exp:n('heroExp')}});await refresh()}}catch(e){{msg(e.toString())}}}}
async function addHero(){{try{{await api('/gm/api/add-hero',JSON.parse(v('heroJson')));await refresh()}}catch(e){{msg(e.toString())}}}}
function loadGroup(){{if(!state.groups)return;document.getElementById('groupJson').value=JSON.stringify(state.groups[v('group')],null,2)}}
async function saveGroup(){{try{{await api('/gm/api/group',{{name:v('group'),value:JSON.parse(v('groupJson'))}});await refresh()}}catch(e){{msg(e.toString())}}}}
async function addItem(){{try{{await api('/gm/api/add-item',{{name:v('itemGroup'),item:JSON.parse(v('itemJson'))}});await refresh()}}catch(e){{msg(e.toString())}}}}
async function resetAccount(){{if(!confirm('Reset toàn bộ save hiện tại?'))return;try{{await api('/gm/api/reset',{{DisplayName:v('newName')}});await refresh()}}catch(e){{msg(e.toString())}}}}
function loadRaw(){{if(state.raw)document.getElementById('rawSave').value=JSON.stringify(state.raw,null,2)}}
async function saveRaw(){{if(!confirm('Ghi đè TOÀN BỘ save?'))return;try{{await api('/gm/api/raw',JSON.parse(v('rawSave')));await refresh()}}catch(e){{msg(e.toString())}}}}
document.getElementById('group').onchange=loadGroup; refresh();
</script></body></html>"""


def handle_gm_api(store: SaveStore, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    if path == "/gm/api/state": return {"ok": True, "state": store.gm_snapshot()}
    if path == "/gm/api/account": store.gm_update_account(body)
    elif path == "/gm/api/time": store.gm_update_time(body)
    elif path == "/gm/api/main-hero": store.gm_set_main_hero(str(body.get("code", "")), int(body.get("level", 1)), int(body.get("exp", 0)))
    elif path == "/gm/api/add-hero": store.gm_add_hero(body)
    elif path == "/gm/api/group": store.gm_set_group(str(body.get("name", "")), body.get("value"))
    elif path == "/gm/api/add-item": store.gm_add_group_item(str(body.get("name", "")), dict(body.get("item") or {}))
    elif path == "/gm/api/reset": store.gm_reset(str(body.get("DisplayName") or "Offline"))
    elif path == "/gm/api/raw": store.gm_replace_raw(body)
    else: return {"ok": False, "error": f"Unknown GM route: {path}"}
    return {"ok": True, "state": store.gm_snapshot()}
