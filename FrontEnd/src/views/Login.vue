<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();

const username = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

const login = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = 'Por favor, preencha usuário e senha.';
    return;
  }
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await api.post('auth/token/', {
      username: username.value,
      password: password.value
    });
    
    // Save tokens
    localStorage.setItem('access_token', response.data.access);
    if(response.data.refresh) {
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    
    // Redirect to home
    router.push('/');
  } catch (error) {
    console.error('Login error', error);
    if (error.response && error.response.status === 401) {
      errorMessage.value = 'Credenciais inválidas. Tente novamente.';
    } else {
      errorMessage.value = 'Erro ao conectar no servidor. Tente mais tarde.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="login-wrapper">
    <div class="login-container glass-panel">
      <div class="login-header">
        <div class="logo-icon"></div>
        <h2>Maintainix</h2>
        <p>Acesse o painel de telemetria</p>
      </div>
      
      <form class="login-form" @submit.prevent="login">
        <!-- Error Message -->
        <transition name="fade">
          <div v-if="errorMessage" class="error-alert">
            <svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            {{ errorMessage }}
          </div>
        </transition>

        <div class="form-group">
          <label for="username">Usuário</label>
          <div class="input-with-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            <input 
              id="username" 
              type="text" 
              v-model="username" 
              placeholder="Ex: joao.silva" 
              autocomplete="username"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password">Senha</label>
          <div class="input-with-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
            <input 
              id="password" 
              type="password" 
              v-model="password" 
              placeholder="Sua senha secreta" 
              autocomplete="current-password"
            />
          </div>
        </div>

        <button type="submit" class="premium-btn w-full mt-4" :disabled="isLoading">
          <span v-if="!isLoading">Entrar na Plataforma</span>
          <span v-else class="loader-spinner"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top left, #1e293b, #0f172a 70%);
  position: relative;
  overflow: hidden;
}

/* Background decorations */
.login-wrapper::before {
  content: '';
  position: absolute;
  top: -20%;
  left: -10%;
  width: 50vw;
  height: 50vw;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
  border-radius: 50%;
}
.login-wrapper::after {
  content: '';
  position: absolute;
  bottom: -20%;
  right: -10%;
  width: 60vw;
  height: 60vw;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
  border-radius: 50%;
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 3rem 2rem;
  z-index: 10;
  border-top: 1px solid rgba(255,255,255,0.1);
  border-left: 1px solid rgba(255,255,255,0.05);
}

.login-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--color-primary), #8b5cf6);
  border-radius: 12px;
  margin: 0 auto 1rem;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
}

.login-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.25rem;
  letter-spacing: -0.5px;
}

.login-header p {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-icon .icon {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: #64748b;
  pointer-events: none;
}

input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.75rem;
  background-color: rgba(15, 23, 42, 0.5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.95rem;
  transition: all var(--transition-fast);
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  background-color: rgba(15, 23, 42, 0.8);
}

input::placeholder {
  color: #475569;
}

.w-full {
  width: 100%;
}

.mt-4 {
  margin-top: 1rem;
}

.error-alert {
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  padding: 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.icon-sm {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* Spinner Animation */
.loader-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
