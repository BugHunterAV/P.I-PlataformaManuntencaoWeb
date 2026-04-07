import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from '../layouts/MainLayout.vue';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: Home,
      },
      // Future routes (Ativos, Telemetria, Alertas) will go here
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Route Guards
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token');
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if (to.name === 'Login' && isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;
