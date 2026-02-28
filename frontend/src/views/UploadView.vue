<template>
  <div class="upload-page">
    <h1 class="page-title">Upload a Research Paper</h1>
    <p class="page-intro">
      Upload a PDF of a research paper and ResearchWiki will generate a concise,
      <a href="https://en.wikipedia.org" target="_blank">Wikipedia-style</a> summary page
      powered by <strong>Mistral AI</strong>.
    </p>

    <div
      class="upload-box"
      :class="{ active: isDragging, processing: isUploading }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
      @click="!isUploading && $refs.fileInput.click()"
    >
      <input ref="fileInput" type="file" accept=".pdf" hidden @change="handleFile" />

      <div v-if="isUploading" class="upload-progress">
        <div class="progress-text">{{ statusText }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="progress-hint">This may take a minute for long papers...</p>
      </div>

      <div v-else class="upload-prompt">
        <div class="upload-icon">⬆</div>
        <p><strong>Drop a PDF file here</strong> or click to browse</p>
        <p class="upload-hint">Supported: Research papers in PDF format</p>
      </div>
    </div>

    <div v-if="error" class="notice notice-error">
      <strong>Error:</strong> {{ error }}
    </div>

    <div class="info-section">
      <h2>How it works</h2>
      <table class="info-table">
        <tr>
          <th>Step</th>
          <th>Description</th>
        </tr>
        <tr>
          <td><strong>1. Parse</strong></td>
          <td>The PDF is parsed to extract text, figures, and structure</td>
        </tr>
        <tr>
          <td><strong>2. Summarize</strong></td>
          <td>Mistral AI reads the paper and produces a concise wiki-style summary</td>
        </tr>
        <tr>
          <td><strong>3. Generate</strong></td>
          <td>A Wikipedia-formatted HTML page is generated with key figures included</td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isDragging: false,
      isUploading: false,
      progress: 0,
      statusText: '',
      error: null,
    }
  },
  methods: {
    handleDrop(e) {
      this.isDragging = false
      const file = e.dataTransfer.files[0]
      if (file) this.upload(file)
    },
    handleFile(e) {
      const file = e.target.files[0]
      if (file) this.upload(file)
    },
    async upload(file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        this.error = 'Please upload a PDF file.'
        return
      }
      this.error = null
      this.isUploading = true
      this.progress = 10
      this.statusText = 'Uploading PDF...'

      const formData = new FormData()
      formData.append('file', file)

      try {
        this.progress = 20
        this.statusText = 'Parsing paper and extracting figures...'

        const res = await fetch('http://localhost:8000/papers/upload', {
          method: 'POST',
          body: formData,
        })

        this.progress = 80
        this.statusText = 'Generating wiki page...'

        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.detail || 'Upload failed')
        }

        const data = await res.json()
        this.progress = 100
        this.statusText = 'Done!'

        sessionStorage.setItem('lastResult', JSON.stringify(data))
        setTimeout(() => {
          this.$router.push({ name: 'result', params: { id: data.id } })
        }, 400)
      } catch (err) {
        this.error = err.message
        this.isUploading = false
        this.progress = 0
      }
    },
  },
}
</script>

<style scoped>
.page-title {
  font-size: 2em;
  margin-bottom: 0.5em;
}

.page-intro {
  margin-bottom: 1.5em;
  color: #54595d;
  max-width: 600px;
  line-height: 1.7;
}

.upload-box {
  border: 2px dashed #a2a9b1;
  border-radius: 2px;
  padding: 2.5em 2em;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #f8f9fa;
  margin-bottom: 1.5em;
}

.upload-box:hover,
.upload-box.active {
  border-color: #3366cc;
  background-color: #eaf3ff;
}

.upload-box.processing {
  cursor: default;
  border-color: #3366cc;
  border-style: solid;
  background-color: #eaf3ff;
}

.upload-icon {
  font-size: 2em;
  color: #3366cc;
  margin-bottom: 0.5em;
}

.upload-hint {
  font-size: 0.85em;
  color: #72777d;
  margin-top: 0.5em;
}

.progress-text {
  font-weight: bold;
  color: #3366cc;
  margin-bottom: 0.75em;
}

.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 6px;
  background: #eaecf0;
  border-radius: 3px;
  margin: 0 auto;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3366cc;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.progress-hint {
  font-size: 0.8em;
  color: #72777d;
  margin-top: 0.75em;
}

.notice {
  padding: 0.75em 1em;
  border-left: 4px solid;
  margin-bottom: 1.5em;
  font-size: 0.9em;
}

.notice-error {
  border-color: #d33;
  background-color: #fee7e6;
  color: #a00;
}

.info-section {
  margin-top: 2em;
}

.info-section h2 {
  font-size: 1.6em;
  margin-bottom: 0.75em;
}

.info-table {
  border-collapse: collapse;
  width: 100%;
}

.info-table th,
.info-table td {
  border: 1px solid #a2a9b1;
  padding: 0.6em 0.8em;
  text-align: left;
}

.info-table th {
  background-color: #eaecf0;
  font-weight: bold;
}
</style>
