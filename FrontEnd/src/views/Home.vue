<script setup>
// Placeholder logic for now
</script>

<template>
  <div class="home-view">
    <div class="welcome-banner glass-panel">
      <h2>Bem-vindo à Plataforma de Manutenção!</h2>
      <p>A interface base (Task 1) está implementada com sucesso. Este é o esqueleto onde as demais funcionalidades serão integradas.</p>
      
      <div class="actions">
        <button class="premium-btn">Visitar Alertas</button>
      </div>
    </div>
    
    <div class="placeholder-grid">
      <div class="card glass-panel" v-for="i in 3" :key="i">
        <div class="card-title"></div>
        <div class="card-content">
          <div class="line"></div>
          <div class="line w-75"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-banner {
  padding: 2rem;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
  border-left: 4px solid var(--color-primary);
}

.welcome-banner h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(to right, #fff, #93c5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.welcome-banner p {
  color: var(--color-text-muted);
  max-width: 600px;
  margin-bottom: 1.5rem;
}

.actions {
  display: flex;
  gap: 1rem;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.card {
  padding: 1.5rem;
  min-height: 150px;
}

.card-title {
  height: 20px;
  width: 40%;
  background-color: var(--color-surface-hover);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.card-content .line {
  height: 12px;
  background-color: var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
  width: 100%;
}

.card-content .line.w-75 {
  width: 75%;
}
</style>
