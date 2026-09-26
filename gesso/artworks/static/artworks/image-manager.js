(() => {
  const csrfToken = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? '';

  const post = async (url, body) => {
    const response = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() }, body });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
    return data;
  };

  let counter = 0;

  document.addEventListener('alpine:init', () => {
    window.Alpine.data('imageManager', (configId) => ({
      config: JSON.parse(document.getElementById(configId).textContent),
      tiles: [],
      over: false,

      init() {
        this.tiles = this.config.tiles.map((data) => this.tile(data));
      },

      tile(data) {
        const values = Object.fromEntries(
          this.config.fields.map((field) => [field.name, data[field.name] ?? (field.type === 'checkbox' ? false : '')]),
        );
        return {
          key: `tile-${counter++}`,
          id: data.id ?? null,
          thumb: data.thumb ?? null,
          preview: null,
          file: null,
          url: null,
          progress: 0,
          state: 'ready',
          error: '',
          note: '',
          values,
        };
      },

      get ids() {
        return this.tiles
          .filter((tile) => tile.id)
          .map((tile) => tile.id)
          .join(',');
      },

      hasFiles(event) {
        return [...(event.dataTransfer?.types ?? [])].includes('Files');
      },

      drop(event) {
        this.over = false;
        if (this.hasFiles(event)) this.add(event.dataTransfer.files);
      },

      add(files) {
        for (const file of files) {
          this.tiles.push(this.tile({}));
          this.upload(this.tiles[this.tiles.length - 1], file, `${this.config.base}upload/`);
        }
      },

      replace(tile, file) {
        if (file) this.upload(tile, file, `${this.config.base}${tile.id}/replace/`);
      },

      retry(tile) {
        this.upload(tile, tile.file, tile.url);
      },

      upload(tile, file, url) {
        if (tile.preview) URL.revokeObjectURL(tile.preview);
        Object.assign(tile, {
          preview: URL.createObjectURL(file),
          file,
          url,
          progress: 0,
          state: 'uploading',
          error: '',
          note: '',
        });
        const body = new FormData();
        body.append('file', file);
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.setRequestHeader('X-CSRFToken', csrfToken());
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) tile.progress = event.loaded / event.total;
        };
        xhr.upload.onload = () => {
          tile.state = 'processing';
        };
        xhr.onload = () => {
          let data = {};
          try {
            data = JSON.parse(xhr.responseText);
          } catch {}
          if (xhr.status >= 200 && xhr.status < 300) {
            URL.revokeObjectURL(tile.preview);
            Object.assign(tile, { id: data.id, thumb: data.thumb, preview: null, file: null, state: 'ready' });
            this.saveOrder();
          } else {
            Object.assign(tile, { state: 'error', error: data.error || 'Upload failed.' });
          }
        };
        xhr.onerror = () => {
          Object.assign(tile, { state: 'error', error: 'Upload failed. Check your connection.' });
        };
        xhr.send(body);
      },

      async save(tile) {
        const body = new FormData();
        for (const field of this.config.fields) {
          const value = tile.values[field.name];
          if (field.type !== 'checkbox') body.append(field.name, value);
          else if (value) body.append(field.name, 'on');
        }
        try {
          await post(`${this.config.base}${tile.id}/`, body);
          tile.note = 'Saved';
          setTimeout(() => tile.note === 'Saved' && (tile.note = ''), 1500);
        } catch (error) {
          tile.note = error.message;
        }
      },

      async remove(tile) {
        if (!window.confirm('Delete this image?')) return;
        if (tile.id) {
          try {
            await post(`${this.config.base}${tile.id}/delete/`);
          } catch (error) {
            tile.note = error.message;
            return;
          }
        }
        if (tile.preview) URL.revokeObjectURL(tile.preview);
        this.tiles = this.tiles.filter((other) => other !== tile);
      },

      reordered() {
        const order = [...this.$refs.grid.querySelectorAll('[data-key]')].map((el) => el.dataset.key);
        this.tiles = [...this.tiles].sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key));
        this.saveOrder();
      },

      saveOrder() {
        const ids = this.tiles.filter((tile) => tile.id).map((tile) => tile.id);
        return post(`${this.config.base}order/`, JSON.stringify({ ids })).catch(() => {});
      },
    }));
  });
})();
