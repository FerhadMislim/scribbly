```
# Run from the repository root: /home/ferhad/scribbly

# Upload fresh
upload_id=$(curl --fail-with-body -s -X 'POST' 'http://localhost:8000/api/v1/artwork/upload' \
  -H 'X-User-Id: test-user-123' \
  -F 'file=@./ai-engine/output/flowers.jpeg;type=image/jpeg' | jq -r .upload_id)
# Generate
task_id=$(curl --fail-with-body -s -X 'POST' 'http://localhost:8000/api/v1/generate/image' \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: test-user-123' \
  -d "{\"upload_id\": \"$upload_id\", \"style_id\": \"pixar_3d\", \"custom_prompt\": \"a charming 3D Pixar-style bouquet of colorful flowers, soft cinematic lighting, expressive shapes, vibrant petals, whimsical garden atmosphere, highly detailed, polished animated movie look\"}" | jq -r .task_id)
echo "Task: $task_id"
sleep 5
curl --fail-with-body -s -X "GET" "http://localhost:8000/api/v1/tasks/$task_id"

# Generate hand-drawn pencil style
task_id=$(curl --fail-with-body -s -X POST 'http://localhost:8000/api/v1/generate/image' \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: test-user-123' \
  -d "{\"upload_id\": \"$upload_id\", \"style_id\": \"hand_drawn_pencil\", \"custom_prompt\": \"a hand-drawn pencil sketch of a bouquet of flowers, soft graphite shading, natural sketchbook texture, elegant cross-hatching, detailed petals\"}" | jq -r '.task_id')
echo "Task: $task_id"
sleep 5
curl --fail-with-body -s -X "GET" "http://localhost:8000/api/v1/tasks/$task_id"
```


