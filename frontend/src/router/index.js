import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'upload',
      component: () => import('../views/UploadView.vue'),
    },
    {
      path: '/result/:id?',
      name: 'result',
      component: () => import('../views/ResultView.vue'),
    },
    {
      path: '/papers',
      name: 'papers',
      component: () => import('../views/PapersView.vue'),
    },
  ],
})

export default router
