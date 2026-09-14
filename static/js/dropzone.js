/**
 * Progressive drag-and-drop enhancement for <input type="file"> fields.
 * No dependencies (no Alpine/HTMX needed) - finds every file input on the
 * page, wraps it in a drop zone, and shows an image preview or filename
 * chip. Falls back to the plain native file input if JS fails to load,
 * so nothing is ever broken, just less convenient.
 *
 * Usage: add class="dropzone-input" to any <input type="file"> and this
 * script does the rest automatically on page load.
 */
(function () {
    function humanFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        const units = ['KB', 'MB', 'GB'];
        let i = -1;
        do { bytes /= 1024; i++; } while (bytes >= 1024 && i < units.length - 1);
        return bytes.toFixed(1) + ' ' + units[i];
    }

    function enhance(input) {
        if (input.dataset.dropzoneReady) return;
        input.dataset.dropzoneReady = 'true';

        const wrapper = document.createElement('div');
        wrapper.className = 'dropzone-wrapper';
        input.parentNode.insertBefore(wrapper, input);

        const zone = document.createElement('div');
        zone.className = 'dropzone-area';
        zone.innerHTML = `
            <i class="bi bi-cloud-arrow-up dropzone-icon"></i>
            <div class="dropzone-text">
                <strong>Click to browse</strong> or drag a file here
            </div>
            <div class="dropzone-hint text-secondary small">
                ${input.accept && input.accept.includes('image') ? 'PNG or JPG' : 'Any file'} - up to 5MB
            </div>
        `;
        const preview = document.createElement('div');
        preview.className = 'dropzone-preview d-none';

        wrapper.appendChild(zone);
        wrapper.appendChild(preview);
        wrapper.appendChild(input);
        input.classList.add('dropzone-native-input');

        function showFile(file) {
            if (!file) {
                preview.classList.add('d-none');
                zone.classList.remove('d-none');
                return;
            }
            zone.classList.add('d-none');
            preview.classList.remove('d-none');
            const isImage = file.type.startsWith('image/');
            preview.innerHTML = '';

            if (isImage) {
                const img = document.createElement('img');
                img.className = 'dropzone-image-preview';
                const reader = new FileReader();
                reader.onload = (e) => { img.src = e.target.result; };
                reader.readAsDataURL(file);
                preview.appendChild(img);
            }
            const info = document.createElement('div');
            info.className = 'dropzone-file-info';
            info.innerHTML = `
                <i class="bi ${isImage ? 'bi-image' : 'bi-file-earmark'}"></i>
                <span>${file.name}</span>
                <span class="text-secondary small">(${humanFileSize(file.size)})</span>
                <button type="button" class="btn btn-sm btn-link text-danger dropzone-remove" aria-label="Remove file">
                    <i class="bi bi-x-circle"></i>
                </button>
            `;
            preview.appendChild(info);
            info.querySelector('.dropzone-remove').addEventListener('click', () => {
                input.value = '';
                showFile(null);
            });
        }

        zone.addEventListener('click', () => input.click());
        input.addEventListener('change', () => showFile(input.files[0]));

        ['dragenter', 'dragover'].forEach(evt => {
            zone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dropzone-active');
            });
        });
        ['dragleave', 'drop'].forEach(evt => {
            zone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dropzone-active');
            });
        });
        zone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length) {
                input.files = files;
                showFile(files[0]);
            }
        });

        // If editing an existing record with a file already set, show its name.
        if (input.dataset.existingFilename) {
            zone.classList.add('d-none');
            preview.classList.remove('d-none');
            preview.innerHTML = `
                <div class="dropzone-file-info">
                    <i class="bi bi-file-earmark-check text-success"></i>
                    <span>Current file: ${input.dataset.existingFilename}</span>
                    <span class="text-secondary small">(choose a new file to replace it)</span>
                </div>
            `;
        }
    }

    function init() {
        document.querySelectorAll('input[type="file"].dropzone-input').forEach(enhance);
    }

    document.addEventListener('DOMContentLoaded', init);
    // Re-scan after HTMX-style or dynamic content swaps, if any occur.
    document.addEventListener('dropzone:rescan', init);
})();
