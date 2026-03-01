# Chrome DevTools Protocol (CDP) — Complete Research Guide

> **What is CDP?** The Chrome DevTools Protocol is a low-level, JSON-over-WebSocket interface that lets external tools **programmatically instrument, inspect, debug, and profile** Chromium-based browsers. It is the same protocol that powers Chrome DevTools itself — meaning when you open DevTools in Chrome, you are already using CDP.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Launching Chrome with Remote Debugging](#2-launching-chrome-with-remote-debugging)
3. [HTTP Discovery Endpoints](#3-http-discovery-endpoints)
4. [WebSocket Connection](#4-websocket-connection)
5. [JSON Wire Format (Messages)](#5-json-wire-format-messages)
6. [Protocol Domains — The Full Picture](#6-protocol-domains--the-full-picture)
7. [Key Domains In Depth](#7-key-domains-in-depth)
   - [Page Domain](#71-page-domain)
   - [Input Domain](#72-input-domain)
   - [DOM Domain](#73-dom-domain)
   - [Network Domain](#74-network-domain)
   - [Runtime Domain](#75-runtime-domain)
   - [Target Domain](#76-target-domain)
   - [Emulation Domain](#77-emulation-domain)
   - [Security Domain](#78-security-domain)
8. [Screenshots & Video Recording](#8-screenshots--video-recording)
9. [How Puppeteer & Playwright Use CDP](#9-how-puppeteer--playwright-use-cdp)
10. [Protocol Versions](#10-protocol-versions)
11. [Security Considerations](#11-security-considerations)
12. [WebDriver BiDi — The Future](#12-webdriver-bidi--the-future)
13. [Quick Reference Cheat-Sheet](#13-quick-reference-cheat-sheet)
14. [CDP vs Playwright MCP Tools — Full Comparison](#14-cdp-vs-playwright-mcp-tools--full-comparison)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE                            │
│                                                             │
│  ┌──────────────┐    WebSocket (JSON)    ┌───────────────┐  │
│  │  CDP Client  │ ◄──────────────────► │  Chrome Browser │  │
│  │  (your code, │    ws://localhost:9222 │  --remote-     │  │
│  │  Puppeteer,  │                       │  debugging-    │  │
│  │  Playwright) │                       │  port=9222     │  │
│  └──────────────┘                       └───────────────┘  │
│         │                                      │            │
│         │  Sends Commands (JSON)               │            │
│         │  ◄── Receives Events (JSON)          │            │
│         │  ◄── Receives Responses (JSON)       │            │
└─────────────────────────────────────────────────────────────┘
```

**Key points:**

- **Client–Server model**: Chrome is the server; your script/tool is the client.
- **Full-duplex WebSocket**: A single persistent connection enables bidirectional, low-latency communication.
- **Not a simulation**: CDP sends real OS-level events to a real browser rendering engine. Screenshots are actual pixel captures from Chrome's compositor.
- **Domain-organized**: The protocol is split into logical **domains** (Page, DOM, Network, Input, Runtime, etc.). Each domain defines **commands** (client → browser) and **events** (browser → client).

---

## 2. Launching Chrome with Remote Debugging

To use CDP, Chrome must be started with the `--remote-debugging-port` flag.

### Platform-Specific Commands

**Windows:**
```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tmp\chrome-debug-profile"
```

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
```

### Important Flags

| Flag | Purpose |
|------|---------|
| `--remote-debugging-port=PORT` | **Required**. Enables CDP on the specified port. |
| `--user-data-dir=PATH` | **Recommended**. Isolates the debug session from your main profile. Since Chrome 136, this is required when using `--remote-debugging-port` on the default profile for security. |
| `--headless=new` | Runs Chrome without a visible UI (headless mode). |
| `--disable-gpu` | Disables GPU hardware acceleration (useful in headless/CI). |
| `--no-first-run` | Skips the "Welcome to Chrome" first-run dialog. |
| `--no-sandbox` | Disables the sandbox (sometimes needed in Docker). **Security risk — avoid in production.** |

### Headless Mode

```bash
chrome --headless=new --remote-debugging-port=9222 --user-data-dir=/tmp/headless-profile
```

Chrome's headless mode still uses the same Blink rendering engine and V8 JavaScript engine — the only difference is no visible window.

---

## 3. HTTP Discovery Endpoints

Once Chrome is running with `--remote-debugging-port=9222`, it exposes several HTTP endpoints for target discovery:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `http://localhost:9222/json/version` | GET | Returns browser metadata: user-agent, V8 version, WebKit version, and the **`webSocketDebuggerUrl`** for the browser-level target. |
| `http://localhost:9222/json/list` | GET | Returns a JSON array of all debuggable targets (tabs, service workers, extensions). Each entry includes `webSocketDebuggerUrl`. |
| `http://localhost:9222/json/new?url` | PUT | Opens a new tab (optionally at `url`) and returns its target info. |
| `http://localhost:9222/json/activate/{targetId}` | POST | Brings the specified target (tab) to the foreground. |
| `http://localhost:9222/json/close/{targetId}` | POST | Closes the specified target. |
| `http://localhost:9222/json/protocol` | GET | Returns the complete protocol schema (all domains, commands, events, types) as JSON. |

### Example: `/json/version` Response

```json
{
  "Browser": "Chrome/125.0.6422.60",
  "Protocol-Version": "1.3",
  "User-Agent": "Mozilla/5.0 ...",
  "V8-Version": "12.5.98",
  "WebKit-Version": "537.36",
  "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/b0b8a4fb-0d01-4e1d-afb5-8b8f0e..."
}
```

### Example: `/json/list` Response (One Tab)

```json
[
  {
    "description": "",
    "devtoolsFrontendUrl": "/devtools/inspector.html?ws=localhost:9222/devtools/page/...",
    "id": "7E32A4BF2...",
    "title": "Google",
    "type": "page",
    "url": "https://www.google.com/",
    "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/7E32A4BF2..."
  }
]
```

**Two levels of WebSocket URLs:**
- **Browser-level** (`/devtools/browser/{id}`): Can control browser-wide features, open/close tabs via the `Target` domain.
- **Page-level** (`/devtools/page/{id}`): Controls a single tab — this is what you typically connect to for page automation.

---

## 4. WebSocket Connection

### Connection Flow

```
1. Client sends HTTP Upgrade request to ws://localhost:9222/devtools/page/{targetId}
2. Chrome accepts → WebSocket connection established
3. Client sends JSON command messages
4. Chrome sends JSON response messages (matched by `id`)
5. Chrome sends JSON event messages (no `id`, has `method`)
6. Connection persists until client disconnects or target closes
```

### Why WebSocket?

| Feature | HTTP | WebSocket |
|---------|------|-----------|
| Connection | New per request | Persistent |
| Direction | Request → Response only | Full-duplex (bidirectional) |
| Latency | Higher (handshake per request) | Lower (single handshake) |
| Server push | Not possible | Events sent in real-time |
| Overhead | Headers with every request | Minimal framing |

CDP **requires** WebSocket because the browser must push asynchronous events to the client (e.g., "a network request just started", "the page finished loading", "a console message was logged") — this is impossible with plain HTTP.

### Minimal Node.js Connection Example

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:9222/devtools/page/TARGET_ID');

ws.on('open', () => {
  // Send a command: navigate to a URL
  ws.send(JSON.stringify({
    id: 1,
    method: 'Page.navigate',
    params: { url: 'https://example.com' }
  }));
});

ws.on('message', (data) => {
  const msg = JSON.parse(data);
  
  if (msg.id) {
    // This is a response to our command
    console.log('Response:', msg);
  } else if (msg.method) {
    // This is an event from the browser
    console.log('Event:', msg.method, msg.params);
  }
});
```

---

## 5. JSON Wire Format (Messages)

All CDP communication uses JSON messages. There are three types:

### 5.1 Command (Client → Browser)

```json
{
  "id": 1,
  "method": "Page.navigate",
  "params": {
    "url": "https://example.com"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | **Required**. Unique identifier to match request with response. |
| `method` | string | **Required**. Domain + command name, e.g. `"Page.navigate"`. |
| `params` | object | Optional. Parameters for the command. Structure varies per method. |

### 5.2 Response (Browser → Client)

**Success:**
```json
{
  "id": 1,
  "result": {
    "frameId": "A1B2C3D4E5",
    "loaderId": "F6G7H8I9J0"
  }
}
```

**Error:**
```json
{
  "id": 2,
  "error": {
    "code": -32000,
    "message": "Cannot navigate to invalid URL"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Matches the `id` from the command. |
| `result` | object | Present on success. Contains return values. |
| `error` | object | Present on failure. Contains `code` and `message`. |

### 5.3 Event (Browser → Client, unsolicited)

```json
{
  "method": "Network.requestWillBeSent",
  "params": {
    "requestId": "1000",
    "request": {
      "url": "https://example.com/api/data",
      "method": "GET",
      "headers": { ... }
    },
    "timestamp": 1633024800.123,
    "type": "XHR"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `method` | string | Domain + event name, e.g. `"Network.requestWillBeSent"`. |
| `params` | object | Event data. |

> **Note**: Events have NO `id` field. This is how you distinguish events from responses.

### Message Flow Diagram

```
Client                                  Browser (Chrome)
  │                                          │
  │──── {id:1, method:"Page.enable"} ──────►│
  │◄─── {id:1, result:{}}  ─────────────────│
  │                                          │
  │──── {id:2, method:"Page.navigate",  ───►│
  │      params:{url:"..."}}                 │
  │◄─── {id:2, result:{frameId:"..."}} ─────│
  │                                          │
  │◄─── {method:"Page.loadEventFired", ─────│  (event, no id)
  │      params:{timestamp:...}}             │
  │                                          │
  │◄─── {method:"Network.requestWillBe ─────│  (event, no id)
  │      Sent", params:{...}}                │
  │                                          │
```

---

## 6. Protocol Domains — The Full Picture

CDP is organized into **40+** domains. Here is the complete list:

| Domain | Category | Description |
|--------|----------|-------------|
| **Accessibility** | Inspection | Query accessibility tree |
| **Animation** | Inspection | Track CSS/Web Animations |
| **Audits** | Inspection | Detect issues (mixed content, deprecations) |
| **Autofill** | Interaction | Autofill management |
| **BackgroundService** | Inspection | Service worker background events |
| **BluetoothEmulation** | Emulation | Emulate Bluetooth devices |
| **Browser** | Control | Browser-level actions (version, crash, close) |
| **CacheStorage** | Storage | Cache API inspection |
| **Cast** | Control | Cast/media session management |
| **Console** | Inspection | Console message collection |
| **CSS** | Inspection | Stylesheet inspection and modification |
| **Database** | Storage | Web SQL database inspection |
| **Debugger** | Debug | JavaScript debugger (breakpoints, stepping) |
| **DeviceAccess** | Emulation | Device access emulation |
| **DeviceOrientation** | Emulation | Override device orientation sensors |
| **DOM** | Inspection | Read/write DOM tree |
| **DOMDebugger** | Debug | DOM breakpoints (subtree modified, attribute changed) |
| **DOMSnapshot** | Inspection | Snapshot entire DOM tree |
| **DOMStorage** | Storage | localStorage / sessionStorage |
| **Emulation** | Emulation | Device metrics, geolocation, touch, media |
| **EventBreakpoints** | Debug | Pause on specific events |
| **Extensions** | Control | Extension management |
| **Fetch** | Network | Network request interception (successor to Network.requestIntercepted) |
| **FileSystem** | Storage | File system access |
| **HeadlessExperimental** | Control | Headless-specific features |
| **HeapProfiler** | Performance | Heap memory profiling |
| **IndexedDB** | Storage | IndexedDB inspection |
| **Input** | Interaction | Mouse, keyboard, touch event dispatch |
| **Inspector** | Control | Inspector lifecycle |
| **IO** | Utility | Stream reading for blobs/traces |
| **LayerTree** | Inspection | Compositing layer information |
| **Log** | Inspection | Browser log entries |
| **Media** | Inspection | Media playback debugging |
| **Memory** | Performance | Memory pressure simulation |
| **Network** | Network | HTTP/HTTPS traffic monitoring and control |
| **Overlay** | Inspection | Visual overlays on inspected page |
| **Page** | Control | Page lifecycle, navigation, screenshots |
| **Performance** | Performance | Performance metrics collection |
| **PerformanceTimeline** | Performance | Performance timeline events |
| **Preload** | Network | Preload/prefetch monitoring |
| **Profiler** | Performance | CPU profiling |
| **PWA** | Inspection | Progressive Web App features |
| **Runtime** | Core | JavaScript execution and object inspection |
| **Schema** | Meta | Protocol schema information |
| **Security** | Security | Security state and certificate errors |
| **ServiceWorker** | Control | Service worker management |
| **Storage** | Storage | Unified storage management |
| **SystemInfo** | Inspection | GPU, CPU, memory info |
| **Target** | Control | Target discovery and session management |
| **Tethering** | Network | Port forwarding |
| **Tracing** | Performance | Chrome tracing (chrome://tracing) |
| **WebAudio** | Inspection | Web Audio API debugging |
| **WebAuthn** | Emulation | WebAuthn authenticator emulation |

> **Enabling a domain**: Most domains must be explicitly enabled before they emit events. For example, you must send `Network.enable` before you'll receive `Network.requestWillBeSent` events.

---

## 7. Key Domains In Depth

### 7.1 Page Domain

Controls page lifecycle — navigation, loading, frames, dialogs, screenshots, and screen recording.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Page.enable` | Enable page event reporting |
| `Page.navigate` | Navigate to a URL |
| `Page.reload` | Reload the current page |
| `Page.getFrameTree` | Get the frame hierarchy |
| `Page.getNavigationHistory` | Get navigation history entries |
| `Page.navigateToHistoryEntry` | Navigate to a specific history entry |
| `Page.captureScreenshot` | Capture a screenshot (returns base64 PNG/JPEG/WebP) |
| `Page.startScreencast` | Start streaming page frames |
| `Page.stopScreencast` | Stop streaming page frames |
| `Page.screencastFrameAck` | Acknowledge receipt of a screencast frame |
| `Page.printToPDF` | Print page to PDF |
| `Page.handleJavaScriptDialog` | Accept or dismiss a JS dialog (alert/confirm/prompt) |
| `Page.setDocumentContent` | Set the page's HTML content |
| `Page.bringToFront` | Bring the page to the foreground |

**Key Events:**

| Event | Description |
|-------|-------------|
| `Page.loadEventFired` | Fired when `window.onload` fires |
| `Page.domContentEventFired` | Fired when `DOMContentLoaded` fires |
| `Page.frameNavigated` | Fired when a frame navigates to a new URL |
| `Page.frameStartedLoading` | Fired when a frame starts loading |
| `Page.frameStoppedLoading` | Fired when a frame stops loading |
| `Page.javascriptDialogOpening` | Fired when a JS dialog (alert/confirm/prompt) appears |
| `Page.screencastFrame` | Fired with frame data during screencast |

---

### 7.2 Input Domain

Dispatches real OS-level input events to the page — mouse clicks, keyboard presses, and touch gestures.

#### `Input.dispatchMouseEvent`

Sends a mouse event at specific pixel coordinates.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | Yes | `"mousePressed"`, `"mouseReleased"`, `"mouseMoved"`, `"mouseWheel"` |
| `x` | number | Yes | X coordinate (CSS pixels, relative to viewport) |
| `y` | number | Yes | Y coordinate (CSS pixels, relative to viewport) |
| `button` | string | No | `"none"`, `"left"`, `"right"`, `"middle"`, `"back"`, `"forward"` |
| `clickCount` | integer | No | Number of clicks (1 = single, 2 = double) |
| `modifiers` | integer | No | Bitmask: Alt=1, Ctrl=2, Meta=4, Shift=8 |
| `deltaX` | number | No | X scroll delta (for `mouseWheel`) |
| `deltaY` | number | No | Y scroll delta (for `mouseWheel`) |
| `timestamp` | number | No | Event timestamp (seconds since epoch) |

**Example — Simulate a left click at (150, 300):**

```json
// Step 1: mousePressed
{
  "id": 10,
  "method": "Input.dispatchMouseEvent",
  "params": {
    "type": "mousePressed",
    "x": 150,
    "y": 300,
    "button": "left",
    "clickCount": 1
  }
}

// Step 2: mouseReleased (same coordinates)
{
  "id": 11,
  "method": "Input.dispatchMouseEvent",
  "params": {
    "type": "mouseReleased",
    "x": 150,
    "y": 300,
    "button": "left",
    "clickCount": 1
  }
}
```

> **Important**: A real "click" requires **two** messages: `mousePressed` + `mouseReleased`. Without the release, the browser treats it as a mouse-down hold.

#### `Input.dispatchKeyEvent`

Sends a keyboard event character by character.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | Yes | `"keyDown"`, `"keyUp"`, `"rawKeyDown"`, `"char"` |
| `key` | string | No | Key value (e.g., `"a"`, `"Enter"`, `"Tab"`) |
| `code` | string | No | Physical key code (e.g., `"KeyA"`, `"Enter"`) |
| `text` | string | No | Text generated by the key (for `char` events) |
| `modifiers` | integer | No | Bitmask: Alt=1, Ctrl=2, Meta=4, Shift=8 |
| `windowsVirtualKeyCode` | integer | No | Windows virtual key code |
| `nativeVirtualKeyCode` | integer | No | Native virtual key code |

**Example — Type the letter "H":**

```json
// keyDown
{ "id": 20, "method": "Input.dispatchKeyEvent", "params": { "type": "keyDown", "key": "H", "code": "KeyH", "text": "H", "modifiers": 8 } }
// char
{ "id": 21, "method": "Input.dispatchKeyEvent", "params": { "type": "char", "text": "H" } }
// keyUp
{ "id": 22, "method": "Input.dispatchKeyEvent", "params": { "type": "keyUp", "key": "H", "code": "KeyH" } }
```

#### `Input.dispatchTouchEvent`

Sends touch events for mobile emulation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | Yes | `"touchStart"`, `"touchEnd"`, `"touchMove"`, `"touchCancel"` |
| `touchPoints` | array | Yes | Array of touch point objects (`{x, y, id, ...}`) |
| `modifiers` | integer | No | Modifier keys bitmask |

---

### 7.3 DOM Domain

Provides read/write access to the page's Document Object Model.

**Key Concepts:**
- Every DOM node sent to the client gets a numeric **`nodeId`**.
- The backend tracks which nodes have been sent — events only fire for known nodes.
- Nodes can be resolved to their JavaScript `RemoteObject` wrapper via `DOM.resolveNode`.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `DOM.enable` | Enable DOM event tracking |
| `DOM.getDocument` | Get the root DOM node |
| `DOM.querySelector` | Find a node by CSS selector |
| `DOM.querySelectorAll` | Find all nodes matching a CSS selector |
| `DOM.getOuterHTML` | Get the outer HTML of a node |
| `DOM.setOuterHTML` | Set the outer HTML of a node |
| `DOM.setNodeValue` | Set a text node's value |
| `DOM.setAttributeValue` | Set an element's attribute |
| `DOM.removeAttribute` | Remove an element's attribute |
| `DOM.getAttributes` | Get all attributes of a node |
| `DOM.requestNode` | Request a node by its remote object ID |
| `DOM.resolveNode` | Get a JS RemoteObject for a DOM node |
| `DOM.describeNode` | Get node description without sending DOM events |
| `DOM.scrollIntoViewIfNeeded` | Scroll a node into the visible viewport |
| `DOM.focus` | Focus a node |
| `DOM.getBoxModel` | Get the CSS box model (content, padding, border, margin boxes) |

**Key Events:**

| Event | Description |
|-------|-------------|
| `DOM.attributeModified` | An attribute was changed |
| `DOM.attributeRemoved` | An attribute was removed |
| `DOM.childNodeInserted` | A child node was added |
| `DOM.childNodeRemoved` | A child node was removed |
| `DOM.documentUpdated` | The document was entirely replaced (e.g., after navigation) |

---

### 7.4 Network Domain

Monitors and controls all network activity — HTTP requests, responses, WebSockets, and more.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Network.enable` | Start tracking network activity |
| `Network.disable` | Stop tracking |
| `Network.getResponseBody` | Get the body of a completed response |
| `Network.setCacheDisabled` | Disable/enable browser cache |
| `Network.clearBrowserCache` | Clear the browser cache |
| `Network.clearBrowserCookies` | Clear all cookies |
| `Network.getCookies` | Get cookies for the current domain |
| `Network.setCookie` | Set a cookie |
| `Network.setExtraHTTPHeaders` | Add custom headers to all requests |
| `Network.setUserAgentOverride` | Override the User-Agent header |
| `Network.emulateNetworkConditions` | Simulate slow network (3G, offline, etc.) |
| `Network.setBlockedURLs` | Block specific URLs from loading |

**Key Events:**

| Event | Description |
|-------|-------------|
| `Network.requestWillBeSent` | A request is about to be sent |
| `Network.responseReceived` | A response was received (headers) |
| `Network.loadingFinished` | Request fully completed |
| `Network.loadingFailed` | Request failed |
| `Network.dataReceived` | Data chunk received |
| `Network.webSocketCreated` | A WebSocket connection was created |
| `Network.webSocketFrameSent` | A WebSocket frame was sent |
| `Network.webSocketFrameReceived` | A WebSocket frame was received |

---

### 7.5 Runtime Domain

Provides JavaScript execution capabilities and object inspection.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Runtime.enable` | Enable runtime event reporting |
| `Runtime.evaluate` | Evaluate a JavaScript expression |
| `Runtime.callFunctionOn` | Call a function on a specific object |
| `Runtime.getProperties` | Get properties of a remote object |
| `Runtime.awaitPromise` | Wait for a Promise to resolve |
| `Runtime.releaseObject` | Release a remote object reference |

**Example — Execute JavaScript:**

```json
{
  "id": 30,
  "method": "Runtime.evaluate",
  "params": {
    "expression": "document.title",
    "returnByValue": true
  }
}
```

**Response:**
```json
{
  "id": 30,
  "result": {
    "result": {
      "type": "string",
      "value": "My Page Title"
    }
  }
}
```

**Key Events:**

| Event | Description |
|-------|-------------|
| `Runtime.consoleAPICalled` | `console.log()`, `console.error()`, etc. was called |
| `Runtime.exceptionThrown` | An uncaught exception occurred |

---

### 7.6 Target Domain

Manages targets — pages, iframes, service workers, browser itself. Essential for multi-tab/multi-context scenarios.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Target.getTargets` | List all available targets |
| `Target.createTarget` | Open a new tab/page |
| `Target.closeTarget` | Close a target |
| `Target.attachToTarget` | Attach to a target to send commands |
| `Target.detachFromTarget` | Detach from a target |
| `Target.setDiscoverTargets` | Enable/disable automatic target discovery |

**Key Events:**

| Event | Description |
|-------|-------------|
| `Target.targetCreated` | A new target was created |
| `Target.targetDestroyed` | A target was destroyed |
| `Target.targetInfoChanged` | Target info was updated |
| `Target.receivedMessageFromTarget` | A message from an attached target |

---

### 7.7 Emulation Domain

Overrides device/environment settings — essential for mobile testing, responsive design, and geolocation testing.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Emulation.setDeviceMetricsOverride` | Override screen width, height, devicePixelRatio, mobile flag |
| `Emulation.clearDeviceMetricsOverride` | Reset to real device metrics |
| `Emulation.setGeolocationOverride` | Override GPS coordinates |
| `Emulation.setTouchEmulationEnabled` | Enable/disable touch event emulation |
| `Emulation.setEmulatedMedia` | Override media type (print, screen) and features (prefers-color-scheme) |
| `Emulation.setTimezoneOverride` | Override timezone |
| `Emulation.setLocaleOverride` | Override locale |
| `Emulation.setCPUThrottlingRate` | Throttle CPU (e.g., 4x slower) |
| `Emulation.setUserAgentOverride` | Override the user agent string |

---

### 7.8 Security Domain

Tracks security state and handles certificate errors.

**Key Commands:**

| Command | Description |
|---------|-------------|
| `Security.enable` | Enable security event tracking |
| `Security.setIgnoreCertificateErrors` | Ignore all certificate errors (useful for testing with self-signed certs) |

**Key Events:**

| Event | Description |
|-------|-------------|
| `Security.securityStateChanged` | The page's security state changed (e.g., mixed content detected) |

---

## 8. Screenshots & Video Recording

This is how browser preview tools capture what you see.

### 8.1 `Page.captureScreenshot` — Single Screenshot

Captures the current state of the page as a base64-encoded image.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"png"` | `"jpeg"`, `"png"`, or `"webp"` |
| `quality` | integer | — | JPEG/WebP quality (0–100) |
| `clip` | Viewport | — | Capture a specific region: `{x, y, width, height, scale}` |
| `fromSurface` | boolean | `true` | Capture from compositing surface (not just the view) |
| `captureBeyondViewport` | boolean | `false` | Capture full page (including off-screen content) |
| `optimizeForSpeed` | boolean | `false` | Optimize encoding speed over file size |

**Example — Full-page screenshot:**

```json
{
  "id": 40,
  "method": "Page.captureScreenshot",
  "params": {
    "format": "png",
    "captureBeyondViewport": true
  }
}
```

**Response:**
```json
{
  "id": 40,
  "result": {
    "data": "iVBORw0KGgoAAAANSUhEUgAA..."  // base64-encoded PNG
  }
}
```

The `data` field can be decoded to get the actual image file.

### 8.2 `Page.startScreencast` — Video Recording

Continuously streams rendered frames as a sequence of images, which can be stitched into a video/animation (e.g., WebP).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"jpeg"` | `"jpeg"` or `"png"` |
| `quality` | integer | — | JPEG quality (0–100) |
| `maxWidth` | integer | — | Max frame width in pixels |
| `maxHeight` | integer | — | Max frame height in pixels |
| `everyNthFrame` | integer | — | Capture every Nth frame (higher = fewer frames, better perf) |

**Flow:**

```
Client                                Browser
  │                                      │
  │── Page.startScreencast ─────────────►│
  │                                      │
  │◄── Page.screencastFrame ─────────────│  (base64 JPEG frame #1)
  │── Page.screencastFrameAck ──────────►│  (must acknowledge!)
  │                                      │
  │◄── Page.screencastFrame ─────────────│  (frame #2)
  │── Page.screencastFrameAck ──────────►│
  │                                      │
  │    ... (continues until stopped)     │
  │                                      │
  │── Page.stopScreencast ──────────────►│
```

**`Page.screencastFrame` event data:**

```json
{
  "method": "Page.screencastFrame",
  "params": {
    "data": "/9j/4AAQSkZJRg...",     // base64-encoded JPEG frame
    "metadata": {
      "offsetTop": 0,
      "pageScaleFactor": 1,
      "deviceWidth": 1920,
      "deviceHeight": 1080,
      "scrollOffsetX": 0,
      "scrollOffsetY": 0,
      "timestamp": 1633024800.456
    },
    "sessionId": 42
  }
}
```

> **Critical**: You **must** send `Page.screencastFrameAck` with the `sessionId` after receiving each frame, or Chrome will stop sending new frames.

---

## 9. How Puppeteer & Playwright Use CDP

### Puppeteer (by Google)

Puppeteer is a **direct abstraction layer** over CDP:

```
Your Test Code  →  Puppeteer API  →  CDP over WebSocket  →  Chrome
```

- Built by the Chrome DevTools team specifically for CDP.
- `page.click(selector)` translates to `DOM.querySelector` + `DOM.getBoxModel` + `Input.dispatchMouseEvent`.
- `page.screenshot()` translates to `Page.captureScreenshot`.
- Advanced users can access raw CDP via `page.createCDPSession()`.

```javascript
// Direct CDP access in Puppeteer
const client = await page.createCDPSession();
await client.send('Network.emulateNetworkConditions', {
  offline: false,
  downloadThroughput: 1.5 * 1024 * 1024 / 8,  // 1.5 Mbps
  uploadThroughput: 750 * 1024 / 8,             // 750 Kbps
  latency: 40
});
```

### Playwright (by Microsoft)

Playwright has a **layered architecture** supporting multiple browsers:

```
Your Test Code  →  Playwright Client  →  Playwright Server  →  Browser Protocol
                                                                    ├── CDP (Chromium)
                                                                    ├── W1 Protocol (Firefox)
                                                                    └── W1 Protocol (WebKit)
```

- Uses CDP **only** for Chromium-based browsers.
- Uses its own custom "W1 Protocol" for Firefox and WebKit (patched browser builds).
- Playwright Server acts as an intermediary, translating high-level commands to the appropriate protocol.
- Direct CDP access available for Chromium: `browser.newBrowserCDPSession()`.

```javascript
// Direct CDP access in Playwright (Chromium only)
const client = await page.context().newCDPSession(page);
await client.send('Animation.enable');
client.on('Animation.animationCreated', (event) => {
  console.log('Animation created:', event);
});
```

### Comparison

| Feature | Puppeteer | Playwright |
|---------|-----------|------------|
| Protocol | CDP only | CDP (Chromium) + W1 (Firefox, WebKit) |
| Browser support | Chrome/Chromium | Chrome, Firefox, Safari (WebKit) |
| Direct CDP access | `page.createCDPSession()` | `context.newCDPSession(page)` |
| Built by | Google Chrome team | Microsoft |
| Language | Node.js (primary) | Node.js, Python, Java, .NET |

---

## 10. Protocol Versions

| Version | Identifier | Description |
|---------|------------|-------------|
| **Stable (1.3)** | `1.3` | Tagged at Chrome 64. Subset of the full protocol — no experimental or deprecated items. Recommended for production tooling. |
| **Tip-of-Tree** | `tot` | Latest development version. Full protocol capabilities. Changes frequently — **no backward compatibility guarantee**. |
| **V8 Inspector** | `v8` | For debugging/profiling Node.js (V8 engine only). |

**Where protocol definitions live:**
- Canonical `.pdl` (Protocol Definition Language) files in the [Chromium source tree](https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/public/devtools_protocol/)
- Compiled JSON + TypeScript definitions on [GitHub](https://github.com/nicedoc/devtools-protocol)
- Published to npm: `devtools-protocol` package

**Version scheme**: Historically `0.0.<revision>` (e.g., `0.0.1134390`). Moving toward `1.0.0-<chrome-version>` (e.g., `1.0.0-125.0.6422.60`).

---

## 11. Security Considerations

> [!CAUTION]
> **CDP has NO built-in authentication**. Anyone who can reach the debugging port has **full control** of the browser — they can read/write files, execute arbitrary code, steal cookies, and more.

### Known Vulnerabilities (Historical)

| CVE | Year | Impact |
|-----|------|--------|
| CVE-2021-30618 | 2021 | Remote code execution via XSS + clickjacking on DevTools frontend — attacker could read/write local files and achieve persistent access |
| CVE-2017-15393 | 2017 | Referer leakage through crafted HTML page exploiting DevTools remote debugging |
| Chrome 136 changes | 2024 | Cookie theft via remote debugging prompted Chrome to require `--user-data-dir` with `--remote-debugging-port` |

### Attack Vectors

1. **No authentication**: Any process on the same machine (or network, if port is exposed) can connect.
2. **`/json/new` endpoint**: Any website can open `chrome://` or `file://` URLs if the debugging port is reachable.
3. **Cookie theft**: Attackers can use `Network.getCookies` to steal all session cookies.
4. **Arbitrary code execution**: `Runtime.evaluate` can run any JavaScript in any context.
5. **File system access**: On Windows, `file://` URLs can leak NTLM hashes.
6. **Debugger API abuse**: Malicious extensions using `chrome.debugger` can escalate privileges.

### Best Practices

| Practice | Description |
|----------|-------------|
| **Never expose the port publicly** | Bind only to `localhost`. Never open port 9222 to the internet. |
| **Use `--user-data-dir`** | Always use an isolated profile for debugging sessions. |
| **Use SSH tunnels or VPN** | If remote debugging is needed, tunnel the connection securely. |
| **Keep Chrome updated** | Security patches are regularly released. |
| **Disable when not needed** | Don't leave remote debugging enabled permanently. |
| **Monitor connections** | Log connections to the debugging port to detect unauthorized access. |

---

## 12. WebDriver BiDi — The Future

**WebDriver BiDi** is a W3C standard being developed as a **cross-browser, stable, bidirectional** alternative to CDP.

| Aspect | CDP | WebDriver BiDi |
|--------|-----|-----------------|
| Standardization | Chromium-specific | W3C standard |
| Browser support | Chrome/Chromium only | Chrome, Firefox, Safari (planned) |
| Stability | Breaking changes possible (tip-of-tree) | Stable, versioned spec |
| Communication | WebSocket + JSON | WebSocket + JSON |
| Event support | Yes | Yes (both push and pull) |
| Maturity | Production-ready | Under active development |

Selenium 4+ and Playwright are adopting WebDriver BiDi alongside CDP support. Eventually, WebDriver BiDi may reduce the need for direct CDP usage in testing tools.

---

## 13. Quick Reference Cheat-Sheet

### Common Operations

| What you want to do | CDP Command |
|---------------------|-------------|
| Navigate to a URL | `Page.navigate({url: "..."})` |
| Take a screenshot | `Page.captureScreenshot({format: "png"})` |
| Click at (x, y) | `Input.dispatchMouseEvent({type: "mousePressed", x, y, button: "left"})` + `mouseReleased` |
| Type text | `Input.dispatchKeyEvent({type: "keyDown/char/keyUp", ...})` per character |
| Run JavaScript | `Runtime.evaluate({expression: "..."})` |
| Get page title | `Runtime.evaluate({expression: "document.title", returnByValue: true})` |
| Find element by CSS | `DOM.querySelector({nodeId: rootId, selector: "..."})` |
| Get element position | `DOM.getBoxModel({nodeId: ...})` |
| Intercept network | `Fetch.enable({patterns: [...]})` |
| Block URLs | `Network.setBlockedURLs({urls: [...]})` |
| Emulate mobile | `Emulation.setDeviceMetricsOverride({width, height, deviceScaleFactor, mobile: true})` |
| Set geolocation | `Emulation.setGeolocationOverride({latitude, longitude, accuracy})` |
| Ignore SSL errors | `Security.setIgnoreCertificateErrors({ignore: true})` |
| Get cookies | `Network.getCookies()` |
| Record video | `Page.startScreencast({format: "jpeg", quality: 80})` |
| Print to PDF | `Page.printToPDF()` |

### Connection Quick Start

```bash
# 1. Launch Chrome
chrome --remote-debugging-port=9222 --user-data-dir=/tmp/debug

# 2. Discover targets
curl http://localhost:9222/json/list

# 3. Connect via WebSocket
#    Use the webSocketDebuggerUrl from step 2
wscat -c ws://localhost:9222/devtools/page/TARGET_ID

# 4. Send commands as JSON
{"id":1,"method":"Page.navigate","params":{"url":"https://example.com"}}
```

---

## 14. CDP vs Playwright MCP Tools — Full Comparison

This section compares **raw CDP** (the low-level protocol you learned above) with **Playwright MCP Tools** (the high-level API that AI agents actually call). Understanding both is critical because Playwright MCP is built *on top of* CDP — every Playwright tool eventually becomes CDP commands.

### 14.1 Architecture: Where Each Lives

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ABSTRACTION LAYERS                         │
│                                                                   │
│  Layer 3 ──► Playwright MCP Tools    (AI agent calls these)       │
│              browser_click, browser_navigate, browser_snapshot     │
│                           │                                       │
│  Layer 2 ──► Playwright API          (auto-wait, selectors, etc.) │
│              page.click(), page.goto(), page.screenshot()         │
│                           │                                       │
│  Layer 1 ──► Chrome DevTools Protocol (raw JSON over WebSocket)   │
│              Input.dispatchMouseEvent, Page.navigate, etc.        │
│                           │                                       │
│  Layer 0 ──► Chrome Browser Engine   (Blink + V8 + Compositor)    │
└─────────────────────────────────────────────────────────────────────┘
```

**Raw CDP** = Layer 1 (you talk directly to the browser)  
**Playwright MCP Tools** = Layer 3 (the AI agent talks to a high-level API that handles everything below)

### 14.2 Complete Tool-by-Tool Mapping

Every Playwright MCP tool maps to one or more CDP commands. Here's the full breakdown:

#### Navigation & Page Lifecycle

| Playwright MCP Tool | What It Does | CDP Commands Used Underneath | Key Difference |
|---------------------|-------------|------------------------------|----------------|
| `browser_navigate` | Go to a URL and wait for load | `Page.navigate` + listen for `Page.loadEventFired` / `Page.domContentEventFired` | **MCP auto-waits** for the page to fully load. CDP gives you `Page.navigate` and you must manually wait for the right event. |
| `browser_go_back` | Browser back button | `Page.getNavigationHistory` + `Page.navigateToHistoryEntry` | MCP = one call. CDP = two calls + index calculation. |
| `browser_go_forward` | Browser forward button | `Page.getNavigationHistory` + `Page.navigateToHistoryEntry` | Same as above. |
| `browser_wait` | Wait for a condition | `Runtime.evaluate` (polling) or event listeners | MCP accepts human-readable conditions. CDP requires you to build your own polling loop. |

#### Interaction (Click, Type, Fill, Select)

| Playwright MCP Tool | What It Does | CDP Commands Used Underneath | Key Difference |
|---------------------|-------------|------------------------------|----------------|
| `browser_click` | Click an element by selector/ref | `DOM.querySelector` → `DOM.getBoxModel` → `DOM.scrollIntoViewIfNeeded` → `Input.dispatchMouseEvent` (mousePressed + mouseReleased) | **MCP does 5+ things automatically**: find element, scroll into view, check visibility, check enabled state, calculate center coordinates, dispatch click. With CDP you do ALL of this manually. |
| `browser_type` | Type text into focused element | `Input.dispatchKeyEvent` × 3 per character (keyDown + char + keyUp) | MCP: one call with full string. CDP: **3 messages per character** (typing "Hello" = 15 CDP messages). |
| `browser_fill` | Clear field + set value | `DOM.focus` + `Input.insertText` or `Runtime.evaluate` to set `.value` + dispatch `input`/`change` events | MCP handles clearing existing text, focusing, and dispatching all necessary DOM events. CDP requires manual orchestration. |
| `browser_select_option` | Select dropdown value | `Runtime.evaluate` (set `selectedIndex` + dispatch `change` event) | MCP understands `<select>` elements natively. CDP requires JS injection. |
| `browser_hover` | Hover over element | `DOM.querySelector` → `DOM.getBoxModel` → `Input.dispatchMouseEvent` (mouseMoved) | MCP: one call. CDP: 3+ calls with coordinate math. |
| `browser_drag` | Drag element to target | Multiple `Input.dispatchMouseEvent` calls (mousePressed → mouseMoved × N → mouseReleased) | MCP: one call with source + target. CDP: sequence of 10+ precisely-timed mouse events. |
| `browser_press_key` | Press a keyboard key | `Input.dispatchKeyEvent` (keyDown + keyUp) | MCP: `"Enter"`. CDP: two messages with correct `key`, `code`, `windowsVirtualKeyCode` values. |

#### Observation & Inspection

| Playwright MCP Tool | What It Does | CDP Commands Used Underneath | Key Difference |
|---------------------|-------------|------------------------------|----------------|
| `browser_snapshot` | Get accessibility tree snapshot | `Accessibility.getFullAXTree` or `DOM.getDocument` + `Accessibility.queryAXTree` | **This is the most important MCP tool for AI agents.** Returns a structured text representation of the page (roles, names, values) — not pixels. CDP returns raw node data you'd need to parse yourself. |
| `browser_take_screenshot` | Capture page as image | `Page.captureScreenshot` | Nearly 1:1 mapping. MCP adds auto-formatting and file handling. |
| `browser_console_messages` | Get console log output | `Runtime.enable` + listen for `Runtime.consoleAPICalled` events | MCP: returns collected messages as a list. CDP: you must enable the domain, subscribe to events, and accumulate messages yourself. |
| `browser_get_text` | Get visible text content | `Runtime.evaluate({expression: "document.body.innerText"})` | MCP: one call. CDP: same, but you manage the evaluation context. |
| `browser_get_html` | Get page HTML | `DOM.getDocument` + `DOM.getOuterHTML` | MCP: one call. CDP: two calls (get root node, then get HTML). |

#### Tab & Browser Management

| Playwright MCP Tool | What It Does | CDP Commands Used Underneath | Key Difference |
|---------------------|-------------|------------------------------|----------------|
| `browser_tab_list` | List all open tabs | `Target.getTargets` | Nearly 1:1, but MCP returns a clean formatted list. |
| `browser_tab_new` | Open new tab | `Target.createTarget` + `Target.attachToTarget` | MCP handles the attachment automatically. |
| `browser_tab_select` | Switch to a tab | `Target.activateTarget` | Nearly 1:1. |
| `browser_tab_close` | Close a tab | `Target.closeTarget` | Nearly 1:1. |
| `browser_close` | Close the browser | `Browser.close` | 1:1 mapping. |

#### Advanced

| Playwright MCP Tool | What It Does | CDP Commands Used Underneath | Key Difference |
|---------------------|-------------|------------------------------|----------------|
| `browser_evaluate` / `browser_run_code` | Execute JavaScript | `Runtime.evaluate` | Nearly 1:1, but MCP handles serialization of complex return values. |
| `browser_file_upload` | Upload a file to `<input type="file">` | `DOM.setFileInputFiles` | MCP handles the file path resolution and element targeting. |
| `browser_handle_dialog` | Accept/dismiss alert/confirm/prompt | `Page.handleJavaScriptDialog` | 1:1, but MCP manages the event subscription (`Page.javascriptDialogOpening`) automatically. |
| `browser_resize` | Resize viewport | `Emulation.setDeviceMetricsOverride` | MCP: width × height. CDP: requires all metric fields (width, height, deviceScaleFactor, mobile). |
| `browser_install` | Install Playwright browsers | N/A (downloads browser binaries) | Not a CDP concept at all — this is Playwright infrastructure. |

### 14.3 What Playwright Handles That CDP Doesn't

| Concern | Raw CDP | Playwright MCP |
|---------|---------|----------------|
| **Auto-waiting** | ❌ You must manually wait for elements to appear, be visible, be enabled, and be stable | ✅ Every action auto-waits with configurable timeout |
| **Element targeting** | ❌ CSS selector → nodeId → coordinates → dispatch event | ✅ Pass a selector or accessibility ref, done |
| **Scroll into view** | ❌ Must call `DOM.scrollIntoViewIfNeeded` explicitly | ✅ Automatic before every interaction |
| **Actionability checks** | ❌ You must check: visible? enabled? not obscured? stable? | ✅ All checks performed automatically |
| **Cross-browser** | ❌ Chromium only | ✅ Chromium, Firefox, WebKit |
| **Retry logic** | ❌ You build it yourself | ✅ Built-in retry on actionability failures |
| **Frame handling** | ❌ Must manually manage frame hierarchy and sessions | ✅ Selectors pierce through frames |
| **Shadow DOM** | ❌ Must use `DOM.describeNode` with `pierce` option | ✅ Selectors pierce shadow DOM by default |
| **File downloads** | ❌ Must intercept network + handle blob | ✅ Handled with download events |
| **Auth / cookies** | ❌ `Network.setCookie` per cookie | ✅ `storageState` save/restore |
| **Accessibility snapshots** | ❌ `Accessibility.getFullAXTree` returns raw nodes you must parse | ✅ Returns clean, LLM-readable text tree |

### 14.4 The "Click" Comparison — A Deep Dive

Let's compare what happens when you want to click a button with `id="submit-btn"`:

**Playwright MCP (1 call):**
```
browser_click(selector="#submit-btn")
```

**Raw CDP (6+ calls, in sequence):**
```json
// 1. Get the document root
{"id":1, "method":"DOM.getDocument"}
// Response: {"result":{"root":{"nodeId":1}}}

// 2. Find the element
{"id":2, "method":"DOM.querySelector", "params":{"nodeId":1, "selector":"#submit-btn"}}
// Response: {"result":{"nodeId":42}}

// 3. Scroll it into view
{"id":3, "method":"DOM.scrollIntoViewIfNeeded", "params":{"nodeId":42}}

// 4. Get its position
{"id":4, "method":"DOM.getBoxModel", "params":{"nodeId":42}}
// Response: {"result":{"model":{"content":[100,200,250,200,250,230,100,230]}}}
// You must calculate center: x=(100+250)/2=175, y=(200+230)/2=215

// 5. Mouse down
{"id":5, "method":"Input.dispatchMouseEvent", "params":{"type":"mousePressed", "x":175, "y":215, "button":"left", "clickCount":1}}

// 6. Mouse up
{"id":6, "method":"Input.dispatchMouseEvent", "params":{"type":"mouseReleased", "x":175, "y":215, "button":"left", "clickCount":1}}
```

That's **6 sequential round-trips** vs **1 MCP call**. And the CDP version doesn't include any waiting, visibility checks, or error handling.

### 14.5 The "Snapshot" Comparison — Why It Matters for AI

**Raw CDP accessibility tree** (what you get from `Accessibility.getFullAXTree`):
```json
{
  "nodes": [
    {"nodeId":"1", "role":{"value":"WebArea"}, "name":{"value":"Login Page"}, "childIds":["2","3"]},
    {"nodeId":"2", "role":{"value":"textbox"}, "name":{"value":"Username"}, "properties":[{"name":"focused","value":{"value":true}}]},
    {"nodeId":"3", "role":{"value":"button"}, "name":{"value":"Sign In"}, "properties":[{"name":"disabled","value":{"value":false}}]}
  ]
}
```

**Playwright MCP `browser_snapshot`** (what the AI agent sees):
```
- page [Login Page]
  - textbox "Username" [focused]
  - button "Sign In"
```

The MCP snapshot is **instantly understandable** by an LLM. The raw CDP output requires parsing, filtering, and reformatting.

### 14.6 When to Use Each

| Scenario | Use Raw CDP | Use Playwright MCP Tools |
|----------|-------------|-------------------------|
| AI agent testing a website | ❌ | ✅ Best choice — designed for this |
| Quick UI automation | ❌ Too verbose | ✅ |
| Network traffic interception | ✅ Full control with `Fetch` domain | ⚠️ Limited tooling |
| Performance profiling | ✅ `Performance`, `Tracing` domains | ❌ Not exposed |
| Device emulation | ✅ Granular `Emulation` domain | ⚠️ `browser_resize` only |
| Console/error monitoring | ⚠️ Possible but manual | ✅ `browser_console_messages` |
| Cookie manipulation | ✅ Full CRUD via `Network` domain | ⚠️ Not directly exposed in MCP |
| Screenshot capture | ✅ More format options | ✅ Simpler |
| Debugging JavaScript | ✅ `Debugger` domain breakpoints | ❌ Not exposed |
| Accessibility testing | ⚠️ Raw AX tree | ✅ Clean snapshots |
| Cross-browser testing | ❌ Chromium only | ✅ All browsers |
| Building a testing framework | ✅ Maximum flexibility | ✅ If using Playwright |

### 14.7 How They Work Together in Our QA Agent

In our Playwright QA agent (`playwright.py`), we use **both layers**:

```
┌──────────────────────────────────────────────────────────────┐
│                    QA Agent Architecture                     │
│                                                              │
│  ┌─────────────┐     ┌─────────────────────────────────┐    │
│  │ LLM (Claude)│────►│ Playwright MCP Tools             │    │
│  │             │     │ • browser_navigate               │    │
│  │ Decides     │     │ • browser_click                  │    │
│  │ what to do  │     │ • browser_snapshot               │    │
│  │ next based  │     │ • browser_type                   │    │
│  │ on snapshot │     │ • browser_evaluate (advanced)    │    │
│  │ results     │     └──────────┬──────────────────────┘    │
│  └─────────────┘                │                           │
│                                 ▼                           │
│                    ┌─────────────────────────┐              │
│                    │  Playwright Server       │              │
│                    │  (translates to CDP)     │              │
│                    └──────────┬──────────────┘              │
│                               │ WebSocket                   │
│                               ▼                             │
│                    ┌─────────────────────────┐              │
│                    │  Chrome Browser          │              │
│                    │  --remote-debugging-port │              │
│                    └─────────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
```

**The flow for a single test step:**
1. Agent calls `browser_snapshot` → gets accessibility tree
2. Agent reads the tree, decides what to do (e.g., "click Login button")
3. Agent calls `browser_click(ref="Login")` → Playwright translates to CDP
4. Under the hood: `DOM.querySelector` → `DOM.getBoxModel` → `Input.dispatchMouseEvent`
5. Agent calls `browser_snapshot` again → verifies the result
6. Repeat until test is complete

### 14.8 Summary Table

| Aspect | Raw CDP | Playwright MCP Tools |
|--------|---------|---------------------|
| **Level** | Low-level protocol | High-level AI-friendly API |
| **Communication** | JSON over WebSocket | Function calls via MCP server |
| **Targeting** | nodeId + pixel coordinates | CSS selectors / accessibility refs |
| **Waiting** | Manual | Automatic |
| **Error handling** | Manual | Built-in retries |
| **Browser support** | Chromium only | Chromium + Firefox + WebKit |
| **Learning curve** | Steep | Gentle |
| **Flexibility** | Maximum (40+ domains) | Limited to exposed tools (~25) |
| **AI-friendliness** | ❌ Raw JSON data | ✅ Designed for LLM consumption |
| **Performance** | Slightly faster (no abstraction) | Slightly slower (but auto-waits save total time) |
| **Use case** | Framework builders, deep debugging | Test automation, AI agents |

> **Bottom line**: Playwright MCP Tools are CDP with training wheels, intelligence, and cross-browser superpowers. Every `browser_click` you call is `Input.dispatchMouseEvent` at its core — but with 50+ lines of waiting, scrolling, and safety logic you'd otherwise write yourself.

---

## References

- [Chrome DevTools Protocol Viewer (Official)](https://chromedevtools.github.io/devtools-protocol/)
- [Chrome DevTools Protocol — GitHub Repository](https://github.com/nicedoc/devtools-protocol)
- [Puppeteer Documentation](https://pptr.dev)
- [Playwright Documentation](https://playwright.dev)
- [WebDriver BiDi Specification](https://w3c.github.io/webdriver-bidi/)
- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
