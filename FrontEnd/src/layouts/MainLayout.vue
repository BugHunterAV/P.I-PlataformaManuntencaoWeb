<script setup>
</script>

<template>
  <div class="layout-container">
    <!-- Sidebar -->
    <aside class="sidebar glass-panel">
      <div class="logo">
        <div class="logo-icon"></div>
        <h2>Maintainix</h2>
      </div>
      
      <nav class="nav-menu">
        <router-link to="/" class="nav-item active">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
          Home (Dashboard)
        </router-link>
        <span class="nav-placeholder">
          <!-- Future routes -->
          <div class="nav-item skeleton"></div>
          <div class="nav-item skeleton"></div>
          <div class="nav-item skeleton"></div>
        </span>
      </nav>
      
      <div class="user-profile">
        <div class="avatar"></div>
        <div class="user-info">
          <p class="name">Operador</p>
          <p class="role">Manutenção</p>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="header glass-panel">
        <div class="header-left">
          <h1 class="page-title">Plataforma de Manutenção Web</h1>
        </div>
        <div class="header-right">
          <button class="icon-btn">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
            <span class="badge">3</span>
          </button>
        </div>
      </header>

      <!-- Page Content Area -->
      <div class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: radial-gradient(circle at top right, #1e293b, #0f172a);
}

/* Sidebar Styling */
.sidebar {
  width: 280px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-radius: 0;
  border-top: none;
  border-bottom: none;
  border-left: none;
  z-index: 10;
}

.logo {
  padding: 2rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-primary), #60a5fa);
  border-radius: 8px;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
}

.logo h2 {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(to right, #fff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.nav-menu {
  flex: 1;
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-item:hover, .nav-item.active {
  background-color: var(--color-surface-hover);
  color: var(--color-text);
}

.nav-item.active {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--color-primary);
  border-left: 3px solid var(--color-primary);
}

.nav-item .icon {
  width: 20px;
  height: 20px;
}

.skeleton {
  height: 44px;
  background: linear-gradient(90deg, #334155 25%, #475569 50%, #334155 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  opacity: 0.3;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.user-profile {
  padding: 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--color-primary);
  background-image: linear-gradient(135deg, var(--color-primary), #8b5cf6);
}

.user-info .name {
  font-weight: 600;
  font-size: 0.95rem;
}

.user-info .role {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

/* Main Content Styling */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* Header */
.header {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  z-index: 5;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.icon-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background-color: var(--color-surface-hover);
  color: var(--color-text);
}

.icon-btn .icon {
  width: 24px;
  height: 24px;
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background-color: var(--color-danger);
  color: white;
  font-size: 0.65rem;
  font-weight: bold;
  height: 18px;
  min-width: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-surface);
}

/* Page Container */
.page-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
