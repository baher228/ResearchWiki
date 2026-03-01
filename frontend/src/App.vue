<template>
  <div id="app">
    <header class="wiki-header">
      <router-link to="/" class="header-logo">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/103px-Wikipedia-logo-v2.svg.png" alt="Logo" class="logo-image" />
        <span class="header-logo-text">WikiResearch</span>
      </router-link>
      <div class="search-container">
        <input type="text" v-model="searchQuery" @keyup.enter="handleSearch" placeholder="Search WikiResearch" class="search-bar" />
      </div>
      <nav class="header-nav">
        <router-link to="/" class="header-link">Upload</router-link>
        <router-link to="/papers" class="header-link">Papers</router-link>
      </nav>
    </header>
    <div class="wiki-body">
      <router-view :key="$route.fullPath" />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: ''
    }
  },
  methods: {
    handleSearch() {
      if (this.searchQuery.trim()) {
        this.$router.push({ path: '/papers', query: { q: this.searchQuery.trim() } })
      } else {
        this.$router.push({ path: '/papers' })
      }
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Linux+Libertine&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Lato, Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #202122;
  background-color: #f8f9fa;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.wiki-header {
  height: 50px;
  background-color: #ffffff;
  border-bottom: 1px solid #eaecf0;
  display: flex;
  align-items: center;
  padding: 0 1.5em;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-logo {
  text-decoration: none;
  display: flex;
  align-items: center;
}

.header-logo-text {
  font-family: "Linux Libertine", Georgia, Times, serif;
  font-size: 1.4em;
  font-weight: normal;
  color: #000;
  letter-spacing: -0.5px;
}

.logo-image {
  height: 35px;
  margin-right: 8px;
}

.search-container {
  margin-left: 2em;
  flex: 1;
  max-width: 400px;
}

.search-bar {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #a2a9b1;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
}

.search-bar:focus {
  border-color: #3366cc;
}

.header-nav {
  display: flex;
  gap: 0;
  margin-left: 2em;
  border-left: 1px solid #eaecf0;
}

.header-link {
  padding: 0 1.25em;
  height: 50px;
  line-height: 50px;
  text-decoration: none;
  color: #3366cc;
  font-size: 0.9em;
  border-bottom: 3px solid transparent;
  transition: background-color 0.15s;
}

.header-link:hover {
  background-color: #eaecf0;
}

.header-link.router-link-exact-active {
  border-bottom-color: #3366cc;
  color: #202122;
  font-weight: 500;
}

.wiki-body {
  flex: 1;
  max-width: 100%;
  margin: 0;
  width: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  min-height: calc(100vh - 50px);
}

.upload-view, .papers-view {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding: 2em 1.5em;
}

h1, h2, h3, h4, h5 {
  font-family: "Linux Libertine", Georgia, Times, serif;
  font-weight: normal;
  color: #000;
}

h1, h2 {
  border-bottom: 1px solid #eaecf0;
  padding-bottom: 0.25em;
}

a {
  color: #3366cc;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
