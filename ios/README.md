# iOS

SwiftUI iOS application for Scribbly.

## Getting Started

### Prerequisites

- Xcode 15+
- Swift 5.9+
- iOS 17+ deployment target

### Setup

1. Open `ios/Scribbly.xcodeproj` in Xcode
2. Select a simulator (iPhone 15 Pro recommended)
3. Press `Cmd + R` to build and run

## Project Structure

```
ios/
├── Scribbly/
│   ├── App/
│   │   └── ScribblyApp.swift
│   ├── Views/
│   │   ├── Upload/
│   │   ├── Styles/
│   │   ├── Gallery/
│   │   └── Settings/
│   ├── ViewModels/
│   ├── Models/
│   ├── Services/
│   │   ├── APIClient.swift
│   │   ├── AuthManager.swift
│   │   └── StorageService.swift
│   └── Resources/
│       ├── Assets.xcassets
│       └── Info.plist
├── Scribbly.xcodeproj
└── README.md
```

## Configuration

The API base URL is configured via `Info.plist`:

```xml
<key>APIBaseURL</key>
<string>https://api.scribbly.app/api/v1</string>
```

## Dependencies

This project uses native frameworks only:
- SwiftUI (UI)
- Foundation (Networking via URLSession)
- PhotosUI (Photo picker)
- VisionKit (Document scanning)

No third-party Swift Package Manager dependencies required.

## Building

```bash
# Via Xcode
xcodebuild -project Scribbly.xcodeproj -scheme Scribbly -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 15 Pro' build

# Via Fastlane (if configured)
fastlane ios build
```

## Testing

```bash
# Unit tests
xcodebuild test -project Scribbly.xcodeproj -scheme Scribbly
```
