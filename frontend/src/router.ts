import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/chat/main-hall',
  },
  {
    path: '/chat/:room',
    component: () => import('./pages/ChatPage.vue'),
  },
  {
    path: '/tasks',
    component: () => import('./pages/TaskBoard.vue'),
  },
  {
    path: '/agents',
    component: () => import('./pages/AgentGallery.vue'),
  },
  {
    path: '/agents/:name',
    component: () => import('./pages/AgentProfile.vue'),
  },
  {
    path: '/ideas',
    component: () => import('./pages/IdeasFeed.vue'),
  },
  {
    path: '/tokens',
    component: () => import('./pages/TokenDashboard.vue'),
  },
  {
    path: '/violations',
    component: () => import('./pages/ViolationLog.vue'),
  },
  {
    path: '/dashboard',
    component: () => import('./pages/Dashboard.vue'),
  },
  {
    path: '/teams',
    component: () => import('./pages/TeamView.vue'),
  },
  {
    path: '/meetings',
    component: () => import('./pages/TeamLeaderMeeting.vue'),
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
