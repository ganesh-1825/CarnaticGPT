# Register first
try {
    Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/register' -Method POST -ContentType 'application/json' -Body '{"username":"demouser","password":"demopass123"}'
    Write-Output "Registered successfully"
} catch {
    Write-Output "Registration skipped (user may already exist)"
}

# Login
$login = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method POST -ContentType 'application/x-www-form-urlencoded' -Body 'username=demouser&password=demopass123'
$token = $login.access_token
$headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }
Write-Output "LOGIN OK. Token received."
Write-Output ""

# Test 1: Valid Carnatic Question
Write-Output "========================================"
Write-Output "TEST 1: Valid Carnatic Question"
Write-Output "Query: Tell me about Raga Kalyani"
Write-Output "========================================"
$body1 = '{"conversation_id":"demo-test-1","message":"Tell me about Raga Kalyani"}'
$r1 = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method POST -Headers $headers -Body $body1
Write-Output "Confidence: $($r1.confidence)"
Write-Output "Detected Raga: $($r1.detected_raga)"
$resp1 = $r1.response
if ($resp1.Length -gt 300) { $resp1 = $resp1.Substring(0, 300) + "..." }
Write-Output "Response: $resp1"
Write-Output "Citations: $($r1.citations.Count)"
foreach ($c in $r1.citations) {
    Write-Output "  - $($c.book_name) | Page $($c.page) | Score $($c.score)"
}
Write-Output ""

# Test 2: PDF/Theory Retrieval
Write-Output "========================================"
Write-Output "TEST 2: PDF/Document Retrieval"
Write-Output "Query: What are the structural features of Melakarta ragas?"
Write-Output "========================================"
$body2 = '{"conversation_id":"demo-test-2","message":"What are the structural features of Melakarta ragas in South Indian classical music?"}'
$r2 = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method POST -Headers $headers -Body $body2
Write-Output "Confidence: $($r2.confidence)"
$resp2 = $r2.response
if ($resp2.Length -gt 300) { $resp2 = $resp2.Substring(0, 300) + "..." }
Write-Output "Response: $resp2"
Write-Output "Citations: $($r2.citations.Count)"
foreach ($c in $r2.citations) {
    Write-Output "  - $($c.book_name) | Page $($c.page) | Score $($c.score)"
}
Write-Output ""

# Test 3: Audio Request
Write-Output "========================================"
Write-Output "TEST 3: Audio Request"
Write-Output "Query: Play Bhairavi raga audio"
Write-Output "========================================"
$body3 = '{"conversation_id":"demo-test-3","message":"Play Bhairavi raga audio"}'
$r3 = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method POST -Headers $headers -Body $body3
Write-Output "Confidence: $($r3.confidence)"
Write-Output "Detected Raga: $($r3.detected_raga)"
$resp3 = $r3.response
if ($resp3.Length -gt 300) { $resp3 = $resp3.Substring(0, 300) + "..." }
Write-Output "Response: $resp3"
Write-Output ""

# Test 4: Random Off-Topic
Write-Output "========================================"
Write-Output "TEST 4: Random Off-Topic Text"
Write-Output "Query: What is the capital of France?"
Write-Output "========================================"
$body4 = '{"conversation_id":"demo-test-4","message":"What is the capital of France?"}'
$r4 = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method POST -Headers $headers -Body $body4
Write-Output "Confidence: $($r4.confidence)"
Write-Output "Response: $($r4.response)"
Write-Output ""

Write-Output "========================================"
Write-Output "ALL 4 TESTS COMPLETE"
Write-Output "========================================"
