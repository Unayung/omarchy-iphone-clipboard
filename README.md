# iPhone Clipboard for Omarchy

Copy on your iPhone, paste on Omarchy, and the other way round. It runs over Tailscale and is triggered by iOS Back Tap.

## Requirements

- Omarchy 4 (Quattro)
- The computer and the iPhone on the same Tailscale network
- `python3`, `wl-clipboard` and `qrencode` (all included in Omarchy)

## Install

```bash
omarchy plugin add https://github.com/Unayung/omarchy-iphone-clipboard --enable
```

1. Click the clipboard icon on the bar and press **Enable service**. This runs `./setup`, which installs and starts a systemd user service.
2. Scan the QR code in the panel with the iPhone camera. On the page that opens:
   - copy the URL first
   - install both shortcuts, pasting the URL when the import asks for it
3. Settings → Accessibility → Touch → Back Tap: set Double Tap to **Send to Computer** and Triple Tap to **Get from Computer**.

With several Omarchy machines, install the plugin on each one. Every machine generates its own token, so import a separate pair of shortcuts per machine and rename them to tell them apart.

## How it works

- `clip-server.py` listens only on the machine's Tailscale IPv4 address (port 8766, override with `CLIP_PORT`).
- `POST` puts the request body on the clipboard with `wl-copy` and shows a notification.
- `GET` returns the clipboard through `wl-paste`, preferring an image when one is on it.
- The token lives in `~/.config/iphone-clipboard/token`. Shortcuts send it as `?t=` or in an `X-Token` header.
- The shortcut files are generic (the URL is asked for at import), so the signed files in `shortcuts/` work on every machine.

## Security

Anyone who has the token and can reach the machine over your tailnet can read and replace your clipboard. That includes passwords copied from a password manager. Keep this in mind:

- The server binds only to the Tailscale address, and Tailscale encrypts the traffic. Plain HTTP never leaves the tailnet.
- If your tailnet is shared with other people (a company tailnet, or a machine shared out to other users), the token is the only thing protecting your clipboard. Treat the install URL and the QR code like a password.
- To revoke access, delete `~/.config/iphone-clipboard/token` and restart the service with `systemctl --user restart iphone-clipboard`. A new token is generated and old shortcuts stop working.
- `CLIP_BIND` lets you bind another address. Binding anything outside Tailscale exposes the clipboard over unencrypted HTTP, so don't.

## Languages

The panel, the notification and the iPhone install page follow the language picked under Setup > Language. English and Traditional Chinese (`zh-TW`) are included. Other languages fall back to English. To add one, copy `i18n/en.json` to `i18n/<code>.json` (codes are listed in `$OMARCHY_PATH/default/i18n/locales.json`) and translate the values.

## Uninstall

```bash
~/.config/omarchy/plugins/io.github.unayung.iphone-clipboard/setup --remove
omarchy plugin remove io.github.unayung.iphone-clipboard
```

## Regenerating the shortcuts (needs a Mac)

```bash
tools/sign-on-mac.sh <mac-ssh-host>   # builds the shortcuts, signs them with `shortcuts sign --mode anyone`, writes to shortcuts/
```
