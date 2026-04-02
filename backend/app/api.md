```
# Upload fresh
upload_id=$(curl -s -X 'POST' 'http://localhost:8000/api/v1/artwork/upload' \
  -H 'X-User-Id: test-user-123' \
  -F 'file=@/Users/ferhad/scribbly/ai-engine/output/flowers.jpeg' | jq -r .upload_id)
# Generate
task_id=$(curl -s -X 'POST' 'http://localhost:8000/api/v1/generate/image' \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: test-user-123' \
  -d "{\"upload_id\": \"$upload_id\", \"style_id\": \"sketch\", \"custom_prompt\": \"flowers\"}" | jq -r .task_id)
echo "Task: $task_id"
sleep 5
curl -s -X "GET" "http://localhost:8000/api/v1/tasks/$task_id"
```
