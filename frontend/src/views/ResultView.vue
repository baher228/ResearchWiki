<template>
  <div class="result-page">
    <div v-if="loading" class="loading-state">
      <p>Loading paper...</p>
    </div>

    <div v-else-if="paper" class="paper-content-wrapper">
      <div class="centered-content">
        <div class="article-meta">
          <em>From ResearchWiki — AI-generated summary</em>
          <span v-if="paper.created_at">
            · {{ formatDate(paper.created_at) }}</span
          >
        </div>

        <div class="notice notice-info">
          <strong>Summary statistics:</strong>
          {{ paper.images_used }} figure(s) referenced from
          {{ paper.images_extracted }} extracted.
          <a v-if="paper.html_url" :href="fullHtmlUrl" target="_blank"
            >View full wiki page ↗</a
          >
        </div>
      </div>

      <div class="article-preview-frame">
        <iframe
          v-if="htmlContent"
          :srcdoc="htmlContent"
          class="wiki-iframe"
          :style="{ height: iframeHeight }"
          frameborder="0"
          scrolling="no"
        ></iframe>
        <p v-else-if="loadingHtml" class="empty-state">Loading wiki page...</p>
        <p v-else class="empty-state">No preview available.</p>
      </div>

      <div class="centered-content">
        <div class="article-footer">
          <router-link to="/">← Upload another paper</router-link>
          <span class="sep">|</span>
          <router-link to="/papers">All papers</router-link>
        </div>

        <div class="linked-papers">
          <h3>Linked Papers</h3>

          <div v-if="generatingLinks" class="loading-links">
            <p>Loading linked papers...</p>
          </div>
          <div v-else-if="paper.related_papers && paper.related_papers.length > 0">
            <ul>
              <li v-for="rp in paper.related_papers" :key="rp.id">
                <router-link :to="'/result/' + rp.id">{{ rp.title }}</router-link>
                <div class="evidence">Confidence: {{ rp.score }} — {{ rp.evidence }}</div>
              </li>
            </ul>
          </div>
          <div v-else>
            <p class="empty-links">No linked papers found.</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Paper not found. <router-link to="/">Upload one</router-link>.</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      paper: null,
      loading: true,
      htmlContent: null,
      loadingHtml: false,
      generatingLinks: false,
      iframeHeight: 'calc(100vh - 120px)',
    };
  },
  computed: {
    fullHtmlUrl() {
      if (!this.paper?.html_url) return "";
      if (this.paper.html_url.startsWith("http")) return this.paper.html_url;
      return "http://localhost:8000" + this.paper.html_url;
    },
    renderedHtml() {
      if (!this.paper?.markdown) return "";
      return this.paper.markdown
        .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
        .replace(/^### (.+)$/gm, "<h3>$1</h3>")
        .replace(/^## (.+)$/gm, "<h2>$1</h2>")
        .replace(/^# (.+)$/gm, "<h1>$1</h1>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/_(.+?)_/g, "<em>$1</em>")
        .replace(/^- (.+)$/gm, "<li>$1</li>")
        .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => {
          const fullSrc = src.startsWith("/")
            ? `http://localhost:8000${src}`
            : src;
          return `<div class="wiki-figure center"><img src="${fullSrc}" alt="${alt}" /><div class="wiki-caption">${alt}</div></div>`;
        })
        .replace(/\n{2,}/g, "<br /><br />")
        .replace(/^---$/gm, "<hr />");
    },
  },
  async created() {
    const id = this.$route.params.id;
    const cached = sessionStorage.getItem("lastResult");
    if (cached) {
      const data = JSON.parse(cached);
      if (!id || data.id === id) {
        this.paper = data;
        this.loading = false;
        this.loadHtmlContent(this.paper.id);
        this.checkAndGenerateLinks(this.paper.id);
        return;
      }
    }
    if (id) {
      try {
        const res = await fetch(`http://localhost:8000/papers/${id}`);
        if (res.ok) {
          this.paper = await res.json();
          this.loadHtmlContent(this.paper.id);
          this.checkAndGenerateLinks(this.paper.id);
        }
      } catch (e) {
        console.error(e);
      }
    }
    this.loading = false;
  },
  mounted() {
    window.addEventListener("message", this.handleMessage);
  },
  beforeUnmount() {
    window.removeEventListener("message", this.handleMessage);
  },
  methods: {
    async handleMessage(event) {
      if (event.data && event.data.type === "resize" && event.data.height) {
        this.iframeHeight = event.data.height + 20 + "px"; // add a small buffer
      } else if (event.data && event.data.type === "explain" && event.data.text) {
        try {
          const res = await fetch("http://localhost:8000/papers/description", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: event.data.text })
          });
          if (!res.ok) throw new Error("Explanation request failed");
          const data = await res.json();
          event.source.postMessage({ type: "explanation_result", markdown: data.markdown }, "*");
        } catch (err) {
          console.error("Explanation error in Vue:", err);
          event.source.postMessage({ type: "explanation_error" }, "*");
        }
      }
    },
    async loadHtmlContent(id) {
      if (!id) return;
      this.loadingHtml = true;
      try {
        const res = await fetch(`http://localhost:8000/papers/${id}/html`);
        if (res.ok) {
          this.htmlContent = await res.text();
        } else {
          console.error("Failed to fetch HTML content");
        }
      } catch (e) {
        console.error("Error fetching HTML content:", e);
      } finally {
        this.loadingHtml = false;
      }
    },
    formatDate(iso) {
      return new Date(iso).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    },
    async checkAndGenerateLinks(id) {
      if (!this.paper.related_papers || this.paper.related_papers.length === 0) {
        this.generatingLinks = true;
        try {
          const res = await fetch(`http://localhost:8000/papers/${id}/generate-links`, {
            method: 'POST'
          });
          if (res.ok) {
            this.paper.related_papers = await res.json();
            const cached = sessionStorage.getItem("lastResult");
            if (cached) {
              const data = JSON.parse(cached);
              if (data.id === id) {
                data.related_papers = this.paper.related_papers;
                sessionStorage.setItem("lastResult", JSON.stringify(data));
              }
            }
          }
        } catch (e) {
          console.error("Failed to generate links:", e);
        } finally {
          this.generatingLinks = false;
        }
      }
    },
  },
};
</script>

<style scoped>
.result-page {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.paper-content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.centered-content {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 0 1.5em;
}

.article-meta {
  color: #54595d;
  font-size: 0.85em;
  margin-bottom: 0;
  padding-bottom: 0.75em;
  padding-top: 2em;
  border-bottom: 1px solid #eaecf0;
}

.notice {
  margin: 1.5em 1.5em;
  padding: 0.75em 1em;
  border-left: 4px solid;
  font-size: 0.9em;
}

.notice-info {
  border-color: #3366cc;
  background-color: #eaf3ff;
}


.article-preview-frame {
  width: 100%;
  flex: 1;
  display: flex;
  margin-top: 0;
}

.wiki-iframe {
  width: 100%;
  min-height: calc(100vh - 120px);
  border: none;
  border-top: 1px solid #eaecf0;
  border-bottom: 1px solid #eaecf0;
  overflow: hidden;
}

.article-body {
  line-height: 1.7;
}

.article-body :deep(h1),
.article-body :deep(h2),
.article-body :deep(h3),
.article-body :deep(h4) {
  font-family: "Linux Libertine", Georgia, Times, serif;
  font-weight: normal;
  color: #000;
  margin-top: 1.5em;
  margin-bottom: 0.25em;
}

.article-body :deep(h2) {
  font-size: 1.6em;
  border-bottom: 1px solid #eaecf0;
  padding-bottom: 0.25em;
}

.article-body :deep(h3) {
  font-size: 1.3em;
}

.article-body :deep(hr) {
  border: none;
  border-top: 1px solid #eaecf0;
  margin: 1.5em 0;
}

.article-body :deep(li) {
  margin-left: 1.5em;
  margin-bottom: 0.25em;
}

.article-body :deep(strong) {
  font-weight: 600;
}

.article-body :deep(.wiki-figure) {
  margin: 1.5em auto;
  background-color: #f8f9fa;
  border: 1px solid #c8ccd1;
  padding: 0.5em;
  text-align: center;
  max-width: 90%;
}

.article-body :deep(.wiki-figure img) {
  max-width: 100%;
  border: 1px solid #c8ccd1;
  margin-bottom: 0.5em;
}

.article-body :deep(.wiki-caption) {
  color: #54595d;
  font-size: 0.9em;
  line-height: 1.4;
  text-align: left;
  padding-top: 0.25em;
}


.article-footer {
  margin-top: 2em;
  padding-top: 1em;
  border-top: 1px solid #eaecf0;
  font-size: 0.9em;
}

.sep {
  color: #a2a9b1;
  margin: 0 0.5em;
}

.loading-state,
.empty-state {
  padding-top: 4em;
  text-align: center;
  color: #54595d;
}

.linked-papers {
  margin-top: 2.5em;
  padding-top: 1.5em;
  border-top: 1px solid #eaecf0;
}

.linked-papers h3 {
  font-family: "Linux Libertine", Georgia, Times, serif;
  font-size: 1.4em;
  margin-bottom: 0.75em;
}

.loading-links {
  color: #72777d;
  font-style: italic;
  font-size: 0.9em;
}

.linked-papers ul {
  list-style-type: none;
  padding-left: 0;
}

.linked-papers li {
  margin-bottom: 0.75em;
  padding: 0.75em;
  background-color: #f8f9fa;
  border: 1px solid #eaecf0;
  border-radius: 2px;
}

.linked-papers li a {
  font-weight: 500;
  text-decoration: none;
  color: #3366cc;
}

.linked-papers li a:hover {
  text-decoration: underline;
}

.evidence {
  font-size: 0.85em;
  color: #54595d;
  margin-top: 0.35em;
}

.empty-links {
  color: #72777d;
  font-size: 0.9em;
}
</style>
