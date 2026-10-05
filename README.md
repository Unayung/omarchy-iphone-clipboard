# iPhone Clipboard for Omarchy

在 iPhone 複製，到 Omarchy 貼上（反過來也行）。走 Tailscale，用 iOS 的「背面輕點」觸發。

## 需求

- Omarchy 4（Quattro）
- 電腦和 iPhone 都在同一個 Tailscale 網路
- `python3`、`wl-clipboard`、`qrencode`（Omarchy 預設都有）

## 安裝

```bash
gh auth setup-git   # 私人 repo：讓 git clone 用 gh 的登入
omarchy plugin add https://github.com/Unayung/omarchy-iphone-clipboard --enable
```

1. 點 bar 上的剪貼簿圖示 → 「啟用服務」（等同執行 `./setup`，裝成 systemd user service）
2. 用 iPhone 相機掃面板上的 QR code，在安裝頁：
   - 先複製網址
   - 再安裝兩個捷徑，匯入時貼上網址
3. 設定 → 輔助使用 → 觸控 → 背面輕點：點兩下「傳到電腦」、點三下「從電腦拿」

多台 Omarchy 各裝一次，每台都會產生自己的 token。iPhone 上每台電腦各匯入一組捷徑，記得改名區分。

## 運作方式

- `clip-server.py` 只綁 Tailscale IP，`POST` 寫入剪貼簿（`wl-copy`），`GET` 讀出剪貼簿（`wl-paste`，有圖片優先回圖片）
- token 存在 `~/.config/iphone-clipboard/token`，捷徑用 `?t=` 或 `X-Token` 帶上
- 捷徑檔是通用的（網址在匯入時才問），所以 `shortcuts/` 裡簽好名的檔案每台都能用

## 移除

```bash
~/.config/omarchy/plugins/io.github.unayung.iphone-clipboard/setup --remove
omarchy plugin remove io.github.unayung.iphone-clipboard
```

## 重新產生捷徑（需要一台 Mac）

```bash
tools/sign-on-mac.sh <mac-ssh-host>   # 產生 + 用 `shortcuts sign --mode anyone` 簽名，輸出到 shortcuts/
```
