<template>
  <div class="papers-page">
    <div class="header-row">
      <h1 class="page-title">All Papers</h1>
      <button @click="cleanDb" class="clean-db-btn" :disabled="cleaning">
        {{ cleaning ? 'Cleaning...' : 'Clean DB' }}
      </button>
    </div>
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
      cleaning: false,
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
    async cleanDb() {
      if (!confirm('Are you sure you want to delete all papers from the database?')) return;
      this.cleaning = true;
      try {
        const res = await fetch('http://localhost:8000/papers/', { method: 'DELETE' });
        if (res.ok) {
          const data = await res.json();
          this.papers = [];
          alert(data.message || 'Database cleaned successfully.');
        } else {
          alert('Failed to clean database.');
        }
      } catch (e) {
        console.error(e);
        alert('Error cleaning database.');
      }
      this.cleaning = false;
    }
  },
}
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25em;
}

.page-title {
  font-size: 2em;
  margin: 0;
}

.clean-db-btn {
  background-color: #d33;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.clean-db-btn:hover:not(:disabled) {
  background-color: #b22;
}

.clean-db-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
