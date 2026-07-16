-- Phase 207: VTO Load Test Script for wrk
-- Usage: wrk -t4 -c10 -d30s -s scripts/load_test_vto.lua http://localhost:8001/api/v2/garment/vto/tryon
--
-- This script sends multipart/form-data POST requests with a tiny test image
-- to simulate concurrent VTO try-on requests.

-- Tiny 1x1 red pixel PNG (67 bytes, valid PNG)
local tiny_png = "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"

local boundary = "----LoadTestBoundary" .. tostring(os.time())
local content_type = "multipart/form-data; boundary=" .. boundary

-- Build multipart body
local function build_body()
    local parts = {}
    parts[#parts+1] = "--" .. boundary .. "\r\n"
    parts[#parts+1] = 'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    parts[#parts+1] = "Content-Type: image/png\r\n\r\n"
    parts[#parts+1] = tiny_png
    parts[#parts+1] = "\r\n--" .. boundary .. "\r\n"
    parts[#parts+1] = 'Content-Disposition: form-data; name="angle"\r\n\r\n'
    parts[#parts+1] = "front"
    parts[#parts+1] = "\r\n--" .. boundary .. "\r\n"
    parts[#parts+1] = 'Content-Disposition: form-data; name="garment_type"\r\n\r\n'
    parts[#parts+1] = "tshirt"
    parts[#parts+1] = "\r\n--" .. boundary .. "\r\n"
    parts[#parts+1] = 'Content-Disposition: form-data; name="garment_color"\r\n\r\n'
    parts[#parts+1] = "#3366cc"
    parts[#parts+1] = "\r\n--" .. boundary .. "--\r\n"
    return table.concat(parts)
end

local body = build_body()

-- Counter for tracking results
local results = {ok = 0, fail = 0, timeout = 0}

request = function()
    return wrk.format("POST", nil, {
        ["Content-Type"] = content_type,
        ["Authorization"] = "Bearer supersecrettoken",
    }, body)
end

response = function(status, headers, body)
    if status == 200 or status == 202 then
        results.ok = results.ok + 1
    elseif status == 429 then
        results.fail = results.fail + 1  -- rate limited
    else
        results.fail = results.fail + 1
    end
end

done = function(summary, latency, requests)
    print("═══════════════════════════════════════════")
    print("VTO Load Test Results")
    print("═══════════════════════════════════════════")
    print(string.format("  Requests:    %d total", summary.requests))
    print(string.format("  Duration:    %.1fs", summary.duration / 1e6))
    print(string.format("  Transfer:    %.2f KB", summary.bytes / 1024))
    print(string.format("  RPS:         %.2f req/s", summary.requests / (summary.duration / 1e6)))
    print(string.format("  Latency avg: %.1f ms", latency.mean / 1000))
    print(string.format("  Latency p50: %.1f ms", latency:percentile(50) / 1000))
    print(string.format("  Latency p99: %.1f ms", latency:percentile(99) / 1000))
    print(string.format("  Latency max: %.1f ms", latency.max / 1000))
    print(string.format("  Success:     %d (%.1f%%)", results.ok, results.ok / (results.ok + results.fail) * 100))
    print(string.format("  Failed:      %d", results.fail))
    print(string.format("  Errors:      %d", summary.errors.connect + summary.errors.read + summary.errors.write + summary.errors.timeout))
    print("═══════════════════════════════════════════")
end
