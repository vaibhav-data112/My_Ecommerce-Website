# Plan: Feature 11 — Product Image Upload

## Context

After feature 09, admin could only set a product image via a URL field. This feature lets the admin upload an actual image file from their computer (jpg/jpeg/png/webp, max 5 MB). The uploaded file is saved to `static/uploads/products/` with a UUID-prefixed safe filename. The existing `image_url` DB column is reused — it stores either a full URL **or** a local path like `uploads/products/xyz.jpg`. Display logic in templates handles both formats plus the grey letter-box placeholder fallback.

---

## Step 1 — `admin.py` — file upload constants + `_save_uploaded_image()`

Add at the top of `admin.py` (alongside existing imports; add `os`, `uuid`, `secure_filename`):

```python
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER    = os.path.join('static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_BYTES   = 5 * 1024 * 1024   # 5 MB
```

### `_save_uploaded_image()` helper

```python
def _save_uploaded_image():
    """Validate and save an uploaded image file. Returns (path, error)."""
    file = request.files.get('image_file')
    if not file or not file.filename:
        return None, None   # no file chosen — not an error

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return None, 'Invalid file type. Allowed types: jpg, jpeg, png, webp.'

    data = file.read()
    if len(data) > MAX_FILE_BYTES:
        return None, 'File too large. Maximum size is 5 MB.'

    safe_name   = secure_filename(file.filename)
    unique_name = f'{uuid.uuid4().hex}_{safe_name}'    # prevents overwrite collisions
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)           # auto-create folder if missing
    with open(os.path.join(UPLOAD_FOLDER, unique_name), 'wb') as f:
        f.write(data)

    return f'uploads/products/{unique_name}', None
```

### `_validate_product_form()` — call `_save_uploaded_image` inside

At the end of the existing validation (after price/stock checks pass), add:

```python
if error is None:
    uploaded_path, upload_error = _save_uploaded_image()
    if upload_error:
        error = upload_error
    elif uploaded_path:
        image_url = uploaded_path   # uploaded file wins over URL field
```

If both URL and file are provided, the uploaded file takes priority (overwrites `image_url`).

---

## Step 2 — `templates/admin/product_form.html` — file input + current image preview

### Add `enctype="multipart/form-data"` to the `<form>` tag

```html
<form method="post" enctype="multipart/form-data">
```

### Add file input group (after the image_url field)

```html
<div class="form-group">
    <label>Upload Image File <small style="color:#888;">(jpg, jpeg, png, webp — max 5 MB)</small></label>

    {% if product is defined and product['image_url'] %}
    <div style="margin-bottom:.5rem;">
        <small style="color:#555;">Current image:</small><br>
        {% if product['image_url'].startswith('http') %}
            <img src="{{ product['image_url'] }}" alt="Current image"
                 style="max-height:80px;max-width:160px;border-radius:4px;margin-top:.25rem;">
        {% else %}
            <img src="{{ url_for('static', filename=product['image_url']) }}" alt="Current image"
                 style="max-height:80px;max-width:160px;border-radius:4px;margin-top:.25rem;">
        {% endif %}
    </div>
    {% endif %}

    <input type="file" name="image_file" accept=".jpg,.jpeg,.png,.webp"
           style="padding:.3rem 0;">
</div>
```

The `product is defined` guard means the preview only shows on the Edit form, not Add.

---

## Step 3 — Display logic in catalog templates

The `image_url` column now contains either:
- A full URL: `https://…`
- A local path: `uploads/products/abc123_photo.jpg`
- Empty / None (placeholder)

Existing catalog templates already used `image_url` for the `<img>` `src`. The only change needed: when the value is a local path (does not start with `http`), generate the URL via `url_for('static', filename=image_url)`.

Template pattern (product card / detail):

```jinja
{% if product.image_url %}
    {% if product.image_url.startswith('http') %}
        <img src="{{ product.image_url }}" alt="{{ product.name }}">
    {% else %}
        <img src="{{ url_for('static', filename=product.image_url) }}" alt="{{ product.name }}">
    {% endif %}
{% else %}
    {# grey letter-box placeholder — unchanged from before #}
    <div class="product-placeholder">{{ product.name[0] }}</div>
{% endif %}
```

---

## Step 4 — `.gitignore`

Add the uploads folder so committed files stay small:

```
static/uploads/products/
```

---

## Files Modified

| File | What changes |
|------|-------------|
| `admin.py` | Add `UPLOAD_FOLDER`, `ALLOWED_EXTENSIONS`, `MAX_FILE_BYTES`, `_save_uploaded_image()`, call it inside `_validate_product_form()` |
| `templates/admin/product_form.html` | `enctype` on form; current-image preview; file input |
| `templates/products/list.html` | Display logic: `http` URL vs local path vs placeholder |
| `templates/products/detail.html` | Same display logic update |
| `.gitignore` | Exclude `static/uploads/products/` |

---

## No DB changes

Feature 11 reuses the existing `image_url` column in `products`. The column stores either a URL string or a relative path string — both are plain text, no schema change needed.

---

## Validation rules

| Check | Action on failure |
|-------|------------------|
| Extension not in `{jpg, jpeg, png, webp}` | Return error, nothing saved |
| File size > 5 MB (checked after `file.read()`) | Return error, nothing saved |
| No file chosen | `(None, None)` — fall through to URL field; not an error |
| Both URL and file provided | Uploaded file wins (overwrites `image_url`) |

---

## Reused Utilities

| Utility | Purpose |
|---------|---------|
| `werkzeug.utils.secure_filename` | Sanitise original filename before saving |
| `uuid.uuid4().hex` | Unique prefix to prevent filename collisions |
| `os.makedirs(..., exist_ok=True)` | Auto-create upload folder on first use |
| `_validate_product_form()` | Already called by `add_product` and `edit_product` routes — no route changes needed |

---

## Backward Compatibility

- Products that already have an `http…` URL → unchanged; display logic checks `startswith('http')`.
- Products with no image → placeholder letter-box still shows.
- Deleting a product does not clean up its uploaded file (backlog item — noted in spec).
