import QtQuick 6.11
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// 伺服器由 systemd 跑（./setup 安裝），這裡只顯示狀態、QR code 和複製網址
Panel {
  id: root
  moduleName: "io.github.unayung.iphone-clipboard"
  ipcTarget: "io.github.unayung.iphone-clipboard"
  manageIpc: false

  readonly property string pluginDir: Qt.resolvedUrl(".").toString().replace("file://", "")
  readonly property string qrPath: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/iphone-clipboard-qr.png"
  readonly property color foreground: bar ? bar.foreground : Color.foreground
  readonly property color dim: Qt.darker(foreground, 1.55)
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family

  property string status: "unknown"   // active / inactive / failed / unknown
  property string installUrl: ""
  property int qrVersion: 0
  property string noteKey: ""
  readonly property bool active: status === "active"
  readonly property string serverUrl: installUrl.replace("/install?", "/?")

  function refresh() {
    if (checker.running) return
    checker.command = ["bash", "-c",
      's=$(systemctl --user is-active iphone-clipboard.service); echo "$s"; ' +
      '[ "$s" = active ] || exit 0; ' +
      'u=$(python3 ' + Util.shellQuote(pluginDir + "clip-server.py") + ' url) || exit 0; echo "$u"; ' +
      'qrencode -s 8 -m 2 -o ' + Util.shellQuote(qrPath) + ' "$u"']
    checker.running = true
  }

  function copy(text, key) {
    Quickshell.execDetached(["bash", "-c", "printf %s " + Util.shellQuote(text) + " | wl-copy"])
    noteKey = key
  }

  onOpenedChanged: if (opened) { noteKey = ""; refresh(); Qt.callLater(function() { keyCatcher.forceActiveFocus() }) }
  Component.onCompleted: refresh()

  Timer { interval: 60000; running: true; repeat: true; onTriggered: root.refresh() }
  Timer { id: afterSetup; interval: 3000; onTriggered: root.refresh() }

  Process {
    id: checker
    running: false
    command: []
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var lines = text.trim().split("\n")
        root.status = lines[0] || "unknown"
        root.installUrl = lines.length > 1 ? lines[1] : ""
        if (root.installUrl) root.qrVersion++
      }
    }
  }

  Process {
    id: setupProc
    running: false
    command: ["bash", "-c", Util.shellQuote(root.pluginDir + "setup")]
    onExited: function(code) { root.noteKey = code === 0 ? "note.enabled" : "note.enableFailed"; afterSetup.start() }
  }

  Commons.Translations { id: strings; directory: Qt.resolvedUrl("i18n") }

  IpcHandler {
    target: root.ipcTarget
    function toggle(): void { root.toggle() }
    function status(): string { return root.status }
  }

  component ActionButton: Rectangle {
    id: btn
    property string label
    signal clicked()
    Layout.fillWidth: true
    implicitHeight: Style.space(34)
    radius: Style.space(6)
    color: area.containsMouse ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.16)
                              : Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.08)
    Text {
      anchors.centerIn: parent
      text: btn.label
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Style.font.body
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; onClicked: btn.clicked() }
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: String.fromCodePoint(0xF06C8)
    opacity: root.active ? 1 : 0.45
    onPressed: function(buttonCode) { root.toggle() }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(300))
    contentHeight: panel.fittedContentHeight(column.implicitHeight + Style.space(24), Style.space(560))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
    }

    ColumnLayout {
      id: column
      anchors.fill: parent
      anchors.margins: Style.space(12)
      spacing: Style.space(8)

      Text {
        text: strings.t("panel.title")
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: Style.font.title
        font.bold: true
      }

      Text {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        color: root.dim
        font.family: root.fontFamily
        font.pixelSize: Style.font.body
        text: root.active ? strings.t("panel.running") : strings.t("panel.stopped").arg(root.status)
      }

      Image {
        visible: root.active && root.installUrl !== ""
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: Style.space(220)
        Layout.preferredHeight: Style.space(220)
        source: visible ? "file://" + root.qrPath + "?v=" + root.qrVersion : ""
        cache: false
        smooth: false
        fillMode: Image.PreserveAspectFit
      }

      ActionButton {
        visible: !root.active
        label: setupProc.running ? strings.t("button.installing") : strings.t("button.enable")
        onClicked: if (!setupProc.running) setupProc.running = true
      }
      ActionButton {
        visible: root.active && root.installUrl !== ""
        label: strings.t("button.copyInstall")
        onClicked: root.copy(root.installUrl, "note.installCopied")
      }
      ActionButton {
        visible: root.active && root.installUrl !== ""
        label: strings.t("button.copyServer")
        onClicked: root.copy(root.serverUrl, "note.serverCopied")
      }

      Text {
        visible: root.noteKey !== ""
        text: strings.t(root.noteKey)
        color: root.dim
        font.family: root.fontFamily
        font.pixelSize: Style.font.body
      }
    }
  }
}
