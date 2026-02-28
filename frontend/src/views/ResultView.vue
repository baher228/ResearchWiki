<template>
  <div class="result-page">
    <div v-if="loading" class="loading-state">
      <p>Loading paper...</p>
    </div>

    <div v-else-if="paper">
      <h1 class="page-title">{{ paper.title }}</h1>

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

      <div class="tab-bar">
        <span
          :class="['tab', { active: tab === 'preview' }]"
          @click="tab = 'preview'"
          >Article preview</span
        >
        <span
          :class="['tab', { active: tab === 'markdown' }]"
          @click="tab = 'markdown'"
          >Markdown source</span
        >
      </div>

      <div
        v-if="tab === 'preview'"
        class="article-body"
        v-html="renderedHtml"
      ></div>

      <pre v-else class="source-view">{{ paper.markdown }}</pre>

      <div class="article-footer">
        <router-link to="/">← Upload another paper</router-link>
        <span class="sep">|</span>
        <router-link to="/papers">All papers</router-link>
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
      tab: "preview",
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
        return;
      }
    }
    if (id) {
      try {
        const res = await fetch(`http://localhost:8000/papers/${id}`);
        if (res.ok) this.paper = await res.json();
      } catch (e) {
        console.error(e);
      }
    }
    this.loading = false;
  },
  methods: {
    formatDate(iso) {
      return new Date(iso).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    },
  },
};
</script>

<style scoped>
.page-title {
  font-size: 2.2em;
  margin-bottom: 0.15em;
}

.article-meta {
  color: #54595d;
  font-size: 0.85em;
  margin-bottom: 1.25em;
  padding-bottom: 0.75em;
  border-bottom: 1px solid #eaecf0;
}

.notice {
  padding: 0.75em 1em;
  border-left: 4px solid;
  margin-bottom: 1.5em;
  font-size: 0.9em;
}

.notice-info {
  border-color: #3366cc;
  background-color: #eaf3ff;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid #a2a9b1;
  margin-bottom: 1.25em;
}

.tab {
  padding: 0.5em 1.25em;
  cursor: pointer;
  font-size: 0.9em;
  color: #3366cc;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
}

.tab:hover {
  background-color: #eaecf0;
}

.tab.active {
  color: #202122;
  border-bottom-color: #3366cc;
  background-color: #fff;
  font-weight: 500;
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

.source-view {
  background-color: #f8f9fa;
  border: 1px solid #eaecf0;
  padding: 1em;
  font-family: monospace;
  font-size: 0.85em;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  color: #202122;
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
</style>
