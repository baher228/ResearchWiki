<template>
  <div class="papers-page">
    <h1 class="page-title">All Papers</h1>
    <p class="page-intro">
      A list of all research papers that have been processed into wiki-style summaries.
    </p>

    <div v-if="loading" class="loading-state">Loading...</div>

    <div v-else-if="papers.length === 0" class="empty-state">
      <p>No papers have been uploaded yet.</p>
      <p><router-link to="/">Upload your first paper</router-link> to get started.</p>
    </div>

    <table v-else class="papers-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Figures</th>
          <th>Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="paper in papers" :key="paper.id" @click="openPaper(paper)" class="clickable-row">
          <td class="title-cell">{{ paper.title }}</td>
          <td>{{ paper.images_used }}/{{ paper.images_extracted }}</td>
          <td>{{ formatDate(paper.created_at) }}</td>
          <td>
            <a v-if="paper.html_url" :href="getFullUrl(paper.html_url)" target="_blank" class="action-link" @click.stop>Wiki ↗</a>
            <span class="sep" v-if="paper.html_url">|</span>
            <a href="#" class="action-link" @click.prevent.stop="openPaper(paper)">View</a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      papers: [],
      loading: true,
    }
  },
  async created() {
    try {
      const res = await fetch('http://localhost:8000/papers/')
      if (res.ok) this.papers = await res.json()
    } catch (e) { console.error(e) }
    this.loading = false
  },
  methods: {
    openPaper(paper) {
      const url = this.getFullUrl(paper.html_url)
      window.location.href = url
    },
    getFullUrl(url) {
      if (url.startsWith('http')) return url
      return 'http://localhost:8000' + url
    },
    formatDate(iso) {
      return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    },
  },
}
</script>

<style scoped>
.page-title {
  font-size: 2em;
  margin-bottom: 0.25em;
}

.page-intro {
  color: #54595d;
  margin-bottom: 1.5em;
}

.papers-table {
  width: 100%;
  border-collapse: collapse;
}

.papers-table th,
.papers-table td {
  border: 1px solid #a2a9b1;
  padding: 0.6em 0.8em;
  text-align: left;
  font-size: 0.9em;
}

.papers-table th {
  background-color: #eaecf0;
  font-weight: bold;
}

.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background-color: #eaf3ff;
}

.title-cell {
  max-width: 400px;
  font-weight: 500;
}

.action-link {
  color: #3366cc;
  text-decoration: none;
  font-size: 0.85em;
}

.action-link:hover {
  text-decoration: underline;
}

.sep {
  color: #a2a9b1;
  margin: 0 0.25em;
}

.loading-state,
.empty-state {
  padding-top: 3em;
  text-align: center;
  color: #54595d;
}
</style>
