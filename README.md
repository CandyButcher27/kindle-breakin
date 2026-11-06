# kindle-breakin

Turn a jailbroken Kindle into an always-on e-ink desk display. The default display is a landscape dashboard of your AI coding spend (Claude Code by default). The same pipeline can show any picture you render on your PC.

The Kindle wakes every 30 minutes and downloads one PNG from your PC. It paints the PNG with FBInk, then goes back to sleep with Wi-Fi off. E-ink keeps the image without power, so the battery lasts.

> **Warning.** Jailbreaking can void your warranty and, if done wrong, can damage the device. Follow the official KindleModding guide for your exact model and firmware. Everything here is at your own risk.

## Tested on

| | |
| --- | --- |
| Kindle | Paperwhite 3 (7th gen, Wi-Fi), firmware 5.16.2.1.1 |
| Jailbreak | WinterBreak2 |
| PC | Windows 11, Node.js 24, Bun, Tailscale 1.104 |

Other jailbroken Kindles should work too. You measure your own screen in step 2.

## Requirements

- A Kindle that the [KindleModding Jailbreaking Wizard](https://kindlemodding.org/kindle-models) supports.
- A **data** USB cable. Many cables only charge. If Windows shows no Kindle drive, try another cable.
- A Windows PC with [Node.js 20+](https://nodejs.org), Git, Bun (`npm install -g bun`), and a free [Tailscale](https://tailscale.com) account.

## Layout

```
dashboard/           PC side: setup script, patch, .env template, scheduled tasks
kindle/scriptlets/   one-tap test scripts for the Kindle
kindle/kindletoken.conf   Kindle daemon config (URL, 30-min refresh)
pictures/            draw your own images and show them on the Kindle
browser-dashboard/   first attempt, an HTML page for the Kindle browser (kept for reference)
```

## Steps

### 1. Jailbreak the Kindle

1. Open the [Jailbreaking Wizard](https://kindlemodding.org/kindle-models). Enter your serial number prefix and firmware from **Settings → Device Options → Device Info**. Follow the method it gives you.
2. For WinterBreak2, as used here:
   1. Download `wb2.zip` and extract it to the root of the Kindle drive.
   2. Eject the Kindle and connect it to Wi-Fi.
   3. Open the browser. Look in the home-screen **⋮** menu: on 5.16 it is called **Web Browser**, not Experimental Browser.
   4. Go to `https://penguins184.xyz/wb2` and press **Jailbreak**.
3. Check that it worked: the Kindle restarts and a **JAILBROKEN** item appears in the library. A `libkh/` folder appears on the drive.
4. Delete any `update*.bin` or `update.bin.tmp.partial` files from the drive root.
5. Type `;kpm update` in the home-screen search bar.

### 2. Measure the screen

1. Copy `kindle/scriptlets/fbtest.sh` to the Kindle's `documents/` folder.
2. Eject, then tap **fbtest** in the library. The screen should say `FBINK TEST OK`.
3. Plug the Kindle back in and open `fbtest.txt` on the drive. Find the line `Variable fb info: 1072x1448, 8bpp @ rotation: 3`.
4. Write down width, height and rotation (rotation `3` means `270`). You enter them in step 3.

### 3. Set up the server on your PC

```powershell
git clone https://github.com/CandyButcher27/kindle-breakin.git
cd kindle-breakin
powershell -ExecutionPolicy Bypass -File dashboard/setup-kindle-ai-usage.ps1
```

The script does the following:
1. Clones [kindle-ai-usage](https://github.com/Kuberwastaken/kindle-ai-usage) into `dashboard/kindle-ai-usage/`, pinned to a tested commit. It uses LF line endings, because the Kindle shell fails on CRLF.
2. Applies `kindle-ai-usage.patch`. The patch adds `KINDLETOKEN_AGENTS`, so you can count only some agents.
3. Installs the server's dependencies and runs its tests.
4. Writes `dashboard/kindle-ai-usage/.env` with a fresh random ingest token.

Open that `.env` and set:
- `KINDLETOKEN_FRAMEBUFFER_WIDTH`, `_HEIGHT` and `_ROTATION` from step 2. Set `KINDLETOKEN_DISPLAY_WIDTH`/`_HEIGHT` to the same numbers swapped, for landscape.
- `KINDLETOKEN_AGENTS`: the agents to count, for example `claude-code` or `claude-code,codex`. Delete the line to count everything ccusage finds.

Start the server and push your usage once:

```powershell
cd dashboard/kindle-ai-usage
node --env-file=.env src/server.mjs                 # leave running
node --env-file=.env bin/kindletoken-collect.mjs    # in a second terminal
```

Open `http://localhost:8787/dashboard.png` to preview the dashboard.

### 4. Give the Kindle a fixed URL (Tailscale Funnel)

Your PC's IP address changes between Wi-Fi, Ethernet and phone data. Funnel gives the PC one fixed https address that works on any network. Only the dashboard image is exposed.

1. Install Tailscale (`winget install Tailscale.Tailscale`) and log in.
2. In the [admin console](https://login.tailscale.com/admin/dns), turn on **HTTPS Certificates**.
3. Run this in **PowerShell**. Git Bash rewrites the `/dashboard-kindle.png` path.

   ```powershell
   & "C:\Program Files\Tailscale\tailscale.exe" funnel --bg --set-path=/dashboard-kindle.png http://127.0.0.1:8787/dashboard-kindle.png
   ```

   On first use it prints a link that enables Funnel for your tailnet. Open it, then run the command again.
4. Your URL is `https://<pc-name>.<tailnet>.ts.net/dashboard-kindle.png`. `tailscale status --json` shows the name under `Self.DNSName`.

Put this URL in:
- `KINDLETOKEN_PUBLIC_URL` in `.env` (without the `/dashboard-kindle.png` part);
- `kindle/kindletoken.conf` (`DASHBOARD_URL`);
- the `URL=` line of `kindle/scriptlets/httpstest.sh` and `fbshow.sh`.

### 5. Test on the Kindle

Copy each scriptlet to `documents/`, eject, tap it, then plug the Kindle back in.

1. **httpstest**: the screen says `HTTPS OK` if the Kindle's `curl` can reach your URL.
2. **fbshow**: paints the dashboard once, so you can check orientation. The stock UI redraws over the first paint, so the script paints again after 5 seconds. You may still see the clock and battery bar during this test. The real install removes them.

If the image is upside down or sideways, change `KINDLETOKEN_FRAMEBUFFER_ROTATION` (`90` or `270`), restart the server, and tap **fbshow** again.

### 6. Install the dashboard on the Kindle

With the Kindle plugged in (replace `E:\` with its drive letter):

```powershell
cd dashboard/kindle-ai-usage
npm run kindle:install -- --kindle E:\ --url https://<pc-name>.<tailnet>.ts.net/dashboard-kindle.png
copy ..\..\kindle\kindletoken.conf E:\kindletoken\config\kindletoken.conf
```

1. Eject the Kindle.
2. Tap **kindletoken-refresh**. After about 15 seconds the stock UI stops and the dashboard fills the screen.
3. If it looks right, hold the power button for about 40 seconds to restart.
4. Tap **kindletoken-install**. The dashboard now survives reboots and refreshes at :05 and :35 every hour.

Press the power button at any time to refresh immediately.

### 7. Keep the PC side running (optional)

From an **Administrator** PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File dashboard/install-tasks.ps1
```

This creates two hidden scheduled tasks:
- `kindletoken-server` starts the server when you log in.
- `kindletoken-collect` pushes usage every 30 minutes, at :00 and :30.

Without them, the dashboard only updates while you run the server by hand.

## Getting the normal Kindle back

1. Hold the power button for about 40 seconds to restart.
2. The library is usable for about 25 seconds before the dashboard takes over. Tap **kindletoken-stop** in that time.
3. To remove the dashboard completely, tap **kindletoken-uninstall** instead.

USB storage does not mount while the dashboard is sleeping. Stop it first, then plug in.

## Show your own pictures

The Kindle shows whatever PNG is served at its URL, so you can show any picture you render.

```powershell
node pictures/claude.mjs                                  # renders pictures/claude-kindle.png
node pictures/serve.mjs pictures/claude-kindle.png        # stop the dashboard server first
```

Press the Kindle's power button and it shows the picture. To make your own, copy `claude.mjs` and change the SVG. Draw on a landscape canvas and keep the final `rotate(270)` and `b-w` steps, which match the framebuffer. Restart the dashboard server to switch back.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No Kindle drive in Windows | Use a data cable and a port directly on the PC. Wake and unlock the Kindle. |
| Scriptlet does nothing | The `.sh` file has CRLF line endings. Clone with `git -c core.autocrlf=false` or convert to LF. |
| Dashboard flashes for a split second, then the library returns | Normal in the fbshow test: the stock UI redraws over the image. |
| `FETCH FAILED` or the dashboard stops updating | Check the server is running and `https://<your-url>/dashboard-kindle.png` opens in a browser. |
| Funnel path shows `/C:/Program Files/Git/...` | You ran it in Git Bash. Use PowerShell, or prefix the command with `MSYS_NO_PATHCONV=1`. |
| `Register-ScheduledTask : Access is denied` | Run `install-tasks.ps1` from an Administrator PowerShell. |
| `fbink -e` segfaults | Known on this FBInk build. `fbtest.sh` still prints the framebuffer info. |

## Credits

- [kindle-ai-usage](https://github.com/Kuberwastaken/kindle-ai-usage) by Kuberwastaken: server, renderer and Kindle daemon. It is not vendored here. The setup script clones it and applies a small patch.
- [KindleModding](https://kindlemodding.org) and WinterBreak2 by Scam.Net and Penguins184.
- [FBInk](https://github.com/NiLuJe/FBInk) by NiLuJe, bundled with the jailbreak.
- [ccusage](https://github.com/ryoppippi/ccusage) for reading local agent usage.

## Versioning

Releases follow [Semantic Versioning](https://semver.org) and are tagged `vX.Y.Z`. See [CHANGELOG.md](CHANGELOG.md).
