## 1. Backend - Retrain Endpoint

- [x] 1.1 Add `POST /inbox/retrain` endpoint in `routes/inbox.py`
- [x] 1.2 Implement selective update logic (only update if new confidence > current)
- [x] 1.3 Return HTMX response with updated table and toast

## 2. Frontend - Retrain Button

- [x] 2.1 Add Retrain button to `inbox.html` toolbar (btn-secondary, left of Commit)
- [x] 2.2 Wire button to `POST /inbox/retrain` endpoint with HTMX

## 3. Testing

- [x] 3.1 Test retrain with no approved transactions (shows toast)
- [x] 3.2 Test retrain preserves manually edited fields
- [x] 3.3 Test retrain updates when new confidence is higher
- [x] 3.4 Run lint and typecheck
