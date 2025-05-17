import Cocoa

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var scriptURL: URL?
    var refreshTimer: Timer? // refresh every hour
    var lastRefreshTime: Date?


    func applicationDidFinishLaunching(_ notification: Notification) {
        print("🚀 App Launched")
        if let scriptsURL = Bundle.main.resourceURL {
            print("📁 scripts folder path = \(scriptsURL.path)")
            let exists = FileManager.default.fileExists(atPath: scriptsURL.path)
            print("📦 scripts folder exists in bundle: \(exists)")
        }


        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        // 🔁 Get the .py script from bundle
        guard let url = getPythonScriptURL() else {
            print("❌ Could not find script")
            return
        }

        scriptURL = url // assign to property for later access

        // 🕒 Parse dynamic refresh interval from filename
        let refreshInterval = parseRefreshInterval(from: url.lastPathComponent)
        print("🕑 Refresh interval: \(refreshInterval) seconds")

        // ⏱ Start repeating timer
        refreshTimer = Timer.scheduledTimer(withTimeInterval: refreshInterval, repeats: true) { [weak self] _ in
            guard let self = self, let scriptURL = self.scriptURL else {
                print("❌ scriptURL not available during scheduled refresh")
                return
            }
            self.refreshMenuBar(using: scriptURL)
        }

        // ⏱ Initial load
        refreshMenuBar(using: url)

        // 💤 Refresh if waking from sleep / unlock
        let center = NSWorkspace.shared.notificationCenter
        center.addObserver(self, selector: #selector(handleWake), name: NSWorkspace.didWakeNotification, object: nil)
        center.addObserver(self, selector: #selector(handleWake), name: NSWorkspace.sessionDidBecomeActiveNotification, object: nil)
    }

    
    func parseRefreshInterval(from path: String) -> TimeInterval {
        let filename = URL(fileURLWithPath: path).lastPathComponent

        let regex = try! NSRegularExpression(pattern: "\\.(\\d+)([smhd])\\.", options: [])
        if let match = regex.firstMatch(in: filename, options: [], range: NSRange(location: 0, length: filename.utf16.count)) {
            let numberRange = Range(match.range(at: 1), in: filename)!
            let unitRange = Range(match.range(at: 2), in: filename)!
            let value = Int(filename[numberRange]) ?? 60
            let unit = filename[unitRange]

            switch unit {
                case "s": return TimeInterval(value)
                case "m": return TimeInterval(value * 60)
                case "h": return TimeInterval(value * 3600)
                case "d": return TimeInterval(value * 86400)
                default:  return 3600  // fallback
            }
        }

        return 3600  // default: 1 hour
    }

    @objc func handleWake() {
        print("💡 System woke or user unlocked")

        guard let scriptURL = scriptURL else {
            print("❌ scriptURL unavailable")
            return
        }

        let interval = parseRefreshInterval(from: scriptURL.lastPathComponent)

        if let last = lastRefreshTime {
            let elapsed = Date().timeIntervalSince(last)
            if elapsed >= interval {
                print("🔁 Wake-triggered refresh (elapsed \(elapsed) ≥ interval \(interval))")
                refreshMenuBar(using: scriptURL)
            } else {
                print("⏱ Wake-triggered check skipped (only \(elapsed) seconds passed)")
            }
        } else {
            print("🔁 No previous refresh — refreshing now")
            refreshMenuBar(using: scriptURL)
        }
    }


    func refreshMenuBar(using scriptURL: URL) {
        print("🔁 Refreshing with script: \(scriptURL.lastPathComponent)")

        let output = runPythonScript(scriptURL: scriptURL)
        print("Full Python Output:\n\(output)")

        let lines = output.components(separatedBy: .newlines)

        var titleText: String?
        var moonImagePath: String?
        var chartImagePaths: [String] = []

        let menu = NSMenu()
        var passedSeparator = false

        for line in lines {
            if line == "---" {
                menu.addItem(NSMenuItem.separator())
                passedSeparator = true
            } else if line.starts(with: "IMAGE-FILE: ") {
                let path = String(line.dropFirst("IMAGE-FILE: ".count)).trimmingCharacters(in: .whitespaces)
                if !passedSeparator && moonImagePath == nil {
                    moonImagePath = path
                    print("🌓 Moon image path captured: \(path)")
                } else {
                    chartImagePaths.append(path)
                    print("🌠 Chart image path captured: \(path)")
                }
            } else if titleText == nil {
                titleText = line
            }else if passedSeparator {
                let isRight = line.starts(with: "RIGHT:")
                let text = isRight ? String(line.dropFirst(6)) : line

                let view = NSView(frame: NSRect(x: 0, y: 0, width: 380, height: 24))

                let label = NSTextField(labelWithString: text)
                label.font = NSFont.systemFont(ofSize: 13)
                label.textColor = isRight ? NSColor.secondaryLabelColor : NSColor.labelColor
                label.alignment = isRight ? .right : .left
                label.isBezeled = false
                label.drawsBackground = false
                label.isEditable = false

                if isRight {
                    label.frame = NSRect(x: 100, y: 4, width: 270, height: 16)
                } else {
                    label.frame = NSRect(x: 10, y: 4, width: 260, height: 16)
                }

                view.addSubview(label)

                // Add refresh button only to the first non-RIGHT row
                if menu.items.filter({ $0.view != nil }).isEmpty && !isRight {
                    let button = NSButton(title: "↻ പുതുക്കൂ", target: self, action: #selector(handleManualRefresh))
                    button.font = NSFont.systemFont(ofSize: 13, weight: .medium)
                    button.bezelStyle = .regularSquare
                    button.setButtonType(.momentaryPushIn)
                    button.isBordered = true
                    button.toolTip = "Refresh Now"
                    button.frame = NSRect(x: 280, y: 2, width: 80, height: 20)
                    view.addSubview(button)
                }

                let item = NSMenuItem()
                item.view = view
                menu.addItem(item)
            }
        }

        for path in chartImagePaths {
            if FileManager.default.fileExists(atPath: path),
               let image = NSImage(contentsOfFile: path) {
                image.size = NSSize(width: 400, height: 400)
                let imageView = NSImageView(image: image)
                imageView.frame = NSRect(x: 0, y: 0, width: 400, height: 400)

                let container = NSView(frame: imageView.frame)
                container.addSubview(imageView)

                let item = NSMenuItem()
                item.view = container
                menu.addItem(item)
            } else {
                print("⚠️ Chart image missing: \(path)")
            }
        }

        if let button = statusItem?.button, let title = titleText {
            if let path = moonImagePath,
               FileManager.default.fileExists(atPath: path),
               let icon = NSImage(contentsOfFile: path) {

                let fullAttrString = NSMutableAttributedString()

                let imgAttachment = NSTextAttachment()
                icon.size = NSSize(width: 16, height: 16)
                imgAttachment.image = icon
                let imgBounds = CGRect(x: 0, y: -3, width: 16, height: 16)
                imgAttachment.bounds = imgBounds

                fullAttrString.append(NSAttributedString(attachment: imgAttachment))
                fullAttrString.append(NSAttributedString(string: " " + title))

                button.attributedTitle = fullAttrString
            } else {
                button.title = title
            }
        }

        statusItem?.menu = menu
        lastRefreshTime = Date()
        
        // Add separator and Quit option
        menu.addItem(NSMenuItem.separator())

        let creditItem = NSMenuItem(title: "രചന - ശ്രീരാം പോഴത് മേനോൻ", action: nil, keyEquivalent: "")
        creditItem.isEnabled = false
        menu.addItem(creditItem)
        
        let quitItem = NSMenuItem(title: "പഞ്ചാംഗം അടക്കൂ ❌", action: #selector(quitApp), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

    }
    
    @objc func quitApp() {
        NSApp.terminate(nil)
    }

    @objc func handleManualRefresh() {
        if let scriptURL = getPythonScriptURL() {
            print("↻ പുതുക്കി")
            refreshMenuBar(using: scriptURL)
        }
    }
    
    func getPythonScriptURL() -> URL? {
        guard let scriptsURL = Bundle.main.resourceURL else {
            return nil
        }

        // Find the first script matching *.1h.py, *.5m.py etc.
        let matches = try? FileManager.default.contentsOfDirectory(at: scriptsURL, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.range(of: #"^\w+\.\d+[smhd]\.py$"#, options: .regularExpression) != nil }

        return matches?.first
    }


    func runPythonScript(scriptURL: URL) -> String {
        let process = Process()
        let pipe = Pipe()
        let errorPipe = Pipe()

        process.executableURL = URL(fileURLWithPath: "/bin/zsh")//might be problematic for app store listing as we are calling shell to run venv. Otherwise after making scriptURL dynamic, GUI is not working. Terminal call was working even then.
        process.arguments = [
            "-c",
            "source /Users/user/venv/bin/activate && python3 '\(scriptURL.path)'"
        ]
        process.standardOutput = pipe
        process.standardError = errorPipe

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            return "Error"
        }

        let outputData = pipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

        let output = String(data: outputData, encoding: .utf8) ?? "N/A"
        let errorOutput = String(data: errorData, encoding: .utf8) ?? ""

        if !errorOutput.isEmpty {
            print("🐍 Python Error:\n\(errorOutput)")
        }

        print("⚠️ Final Output Being Returned:\n\(output)")
        return output.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
