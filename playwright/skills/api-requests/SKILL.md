---
name: api-requests
description: Use this skill when the test case involves submitting API requests, SOAP calls, or using a Postman collection as part of the test flow.
---

# API Requests Skill

A guide for handling SOAP/REST API requests within a test case using Postman
collections. This skill covers reading collections, building requests, and
executing them via `browser_run_code` with human approval.

## When to Use This Skill

Use this skill when:
- The test case mentions submitting a SOAP request or API call
- The test plan references a Postman collection
- A test step requires data setup via an API before UI interaction
- You need to verify an API response as part of the test

## Available Tools

| Tool | Purpose | Safe? |
|------|---------|-------|
| `list_postman_collections()` | See what collections exist | ✅ Safe |
| `read_postman_collection(name)` | Get overview of all requests in a collection | ✅ Safe |
| `get_postman_request(collection, request)` | Get full details of one request | ✅ Safe |
| `build_curl_command(method, url, headers, body)` | Build curl + fetch() snippet for review | ✅ Safe |

All these tools are **read-only**. They parse Postman JSON files but never
send any HTTP requests. Actual execution happens via `browser_run_code`.

## Step-by-Step Process

### 1. Discover Available Collections

```
list_postman_collections()
```

This shows all `.json` files in `playwright/postman/` with their names,
descriptions, and request counts.

### 2. Browse a Collection

```
read_postman_collection('my_collection')
```

This returns an overview of every request: method, URL, headers, and a
body preview (truncated to 200 chars). Use this to find the right request.

### 3. Get Full Request Details

```
get_postman_request('my_collection', 'CreateRecord')
```

This returns the **full** request body (not truncated), all headers, and
the complete URL. You need this for SOAP XML bodies.

### 4. Build the Executable Request

```
build_curl_command(
    method='POST',
    url='https://api.example.com/soap',
    headers='Content-Type: text/xml, SOAPAction: CreateRecord',
    body='<xml>...</xml>'
)
```

This generates:
- A `curl` command (for human reference)
- A `browser_run_code` fetch() snippet (for execution)

### 5. Human Reviews the Request

> ⚠️ MANDATORY: The human MUST see and approve the full request before execution.

Show the output of `build_curl_command` to the human via the normal HITL flow.
The human will see:
- The complete URL
- All headers
- The full request body (XML/JSON)
- Whether to approve, edit, or reject

### 6. Execute via `browser_run_code`

If approved, use `browser_run_code` with the fetch() snippet.
The result will contain `{ status, statusText, body }`.

Verify the response:
- Check HTTP status (200-299 = success)
- Parse the response body for expected values
- Report the result in the test step

## SOAP-Specific Tips

### SOAP Request Structure

SOAP requests typically use:
- Method: `POST`
- Header: `Content-Type: text/xml; charset=utf-8`
- Header: `SOAPAction: <action name>` (varies by service)
- Body: XML envelope

### Common SOAP XML Template

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <!-- Authentication or session tokens go here -->
  </soap:Header>
  <soap:Body>
    <ns:MethodName xmlns:ns="http://example.com/namespace">
      <ns:Param1>value1</ns:Param1>
      <ns:Param2>value2</ns:Param2>
    </ns:MethodName>
  </soap:Body>
</soap:Envelope>
```

### Replacing Variables in Postman Bodies

Postman collections may use `{{variable}}` placeholders. When you see these:
1. Check if the test case provides the value.
2. Check if Message 3 (Employee Agent) provides test data values.
3. If not found, ask the human during HITL approval what value to use.
4. Replace the placeholder before building the request.

## Safety Rules

1. **NEVER send an API request without human approval.** Always use
   `build_curl_command` first, then `browser_run_code` with HITL.
2. **NEVER modify the Postman collection files.** They are read-only reference.
3. **Show the FULL body** — do not truncate XML/JSON. The human needs to see
   everything before approving.
4. **Log the response** — include the API response status and body in the
   test report for traceability.
