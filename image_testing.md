# IMAGE INTEGRATION — TEST AGENT RULES

You are the Test Agent responsible for validating image integrations. Follow these rules exactly. Do not overcomplicate.

## Image Handling Rules
- Always use base64-encoded images for all tests and requests.
- Accepted formats: JPEG, PNG, WEBP only.
- Do not use SVG, BMP, HEIC, or other formats.
- Do not upload blank, solid-color, or uniform-variance images.
- Every image must contain real visual features — objects, edges, textures, shadows.
- If the image is not PNG/JPEG/WEBP, transcode it to PNG or JPEG before upload.
  - If you read a .jpg but the content is actually PNG after conversion/compression — this is invalid. Always re-detect and update the MIME after transformations.
- If the image is animated (GIF, APNG, WEBP animation), extract the first frame only.
- Resize large images to reasonable bounds (avoid oversized payloads).

## Testing
Read `/app/image_testing.md` and `/app/image-testing.md` (if available) for instructions on testing image attachments.
