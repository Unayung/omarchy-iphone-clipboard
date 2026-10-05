#!/usr/bin/env python3
# 產生兩個「未簽名」的通用捷徑到 tools/unsigned/。網址（含 ?t=token）在匯入時由 iOS 詢問，所以一份檔案每台機器共用。
# 簽名只能在 Mac 上做：tools/sign-on-mac.sh <mac-ssh-host>
import plistlib, uuid
from pathlib import Path

OUT = Path(__file__).parent / "unsigned"
U = lambda: str(uuid.uuid4()).upper()


def var(name, uid):  # 引用前一個動作的輸出（整個欄位就是這個變數）
    return {"Value": {"OutputName": name, "OutputUUID": uid, "Type": "ActionOutput"},
            "WFSerializationType": "WFTextTokenAttachment"}


def text_var(name, uid):  # 嵌在文字欄位裡的變數（URL 欄位要這種）
    return {"Value": {"string": "￼", "attachmentsByRange": {"{0, 1}": {"OutputName": name, "OutputUUID": uid, "Type": "ActionOutput"}}},
            "WFSerializationType": "WFTextTokenString"}


def act(ident, **params):
    return {"WFWorkflowActionIdentifier": f"is.workflow.actions.{ident}", "WFWorkflowActionParameters": params}


def workflow(actions, glyph):
    return {"WFWorkflowActions": actions, "WFWorkflowClientVersion": "2605.0.5", "WFWorkflowMinimumClientVersion": 900,
            "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": glyph},
            "WFWorkflowImportQuestions": [{
                "ActionIndex": 0, "Category": "Parameter", "ParameterKey": "WFTextActionText", "DefaultValue": "",
                "Text": "貼上 Omarchy 剪貼簿面板（或安裝頁）上的網址，開頭是 http://100. 結尾有 ?t="}],
            "WFWorkflowInputContentItemClasses": [], "WFWorkflowTypes": []}


def url_action():
    uid = U()
    return uid, act("gettext", UUID=uid, WFTextActionText="")


def send():
    u, url = url_action()
    c, d = U(), U()
    return workflow([
        url,
        act("getclipboard", UUID=c),
        act("downloadurl", UUID=d, WFURL=text_var("Text", u), WFHTTPMethod="POST", WFHTTPBodyType="File",
            WFRequestVariable=var("Clipboard", c)),
    ], 59511)


def fetch():
    u, url = url_action()
    d = U()
    return workflow([
        url,
        act("downloadurl", UUID=d, WFURL=text_var("Text", u), WFHTTPMethod="GET"),
        act("setclipboard", WFInput=var("Contents of URL", d)),
    ], 59512)


OUT.mkdir(exist_ok=True)
for name, wf in (("傳到電腦", send()), ("從電腦拿", fetch())):
    (OUT / f"{name}.shortcut").write_bytes(plistlib.dumps(wf, fmt=plistlib.FMT_BINARY))
    print(OUT / f"{name}.shortcut")
