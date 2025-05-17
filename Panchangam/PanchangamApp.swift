import SwiftUI

@main
struct PanchangamApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        // No window needed
        Settings {
            EmptyView()
        }
    }
}
