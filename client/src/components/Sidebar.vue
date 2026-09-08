<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="brand">
      <div class="brand-mark">{{ companyInitial }}</div>
      <div class="brand-text">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <nav class="nav-list">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        :class="{ active: $route.path === item.path }"
        :title="item.label"
      >
        <component :is="item.icon" class="nav-icon" :size="20" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <button class="collapse-toggle" @click="toggleCollapsed" :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
      <ChevronLeft v-if="!isCollapsed" :size="18" />
      <ChevronRight v-else :size="18" />
    </button>
  </aside>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Wallet,
  TrendingUp,
  RefreshCw,
  FileBarChart,
  ChevronLeft,
  ChevronRight
} from '@lucide/vue'
import { useI18n } from '../composables/useI18n'

const STORAGE_KEY = 'sidebar-collapsed'

export default {
  name: 'Sidebar',
  components: {
    LayoutDashboard,
    Package,
    ShoppingCart,
    Wallet,
    TrendingUp,
    RefreshCw,
    FileBarChart,
    ChevronLeft,
    ChevronRight
  },
  setup() {
    const { t } = useI18n()
    const isCollapsed = ref(false)

    // localStorage can throw (e.g. private browsing / storage disabled) - fall back to expanded rather than breaking the app
    onMounted(() => {
      try {
        isCollapsed.value = window.localStorage.getItem(STORAGE_KEY) === 'true'
      } catch (err) {
        isCollapsed.value = false
      }
    })

    const toggleCollapsed = () => {
      isCollapsed.value = !isCollapsed.value
      try {
        window.localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
      } catch (err) {
        // ignore persistence failures, in-memory state still works for this session
      }
    }

    const companyInitial = computed(() => (t('nav.companyName') || '').charAt(0))

    const navItems = computed(() => [
      { path: '/', label: t('nav.overview'), icon: 'LayoutDashboard' },
      { path: '/inventory', label: t('nav.inventory'), icon: 'Package' },
      { path: '/orders', label: t('nav.orders'), icon: 'ShoppingCart' },
      { path: '/spending', label: t('nav.finance'), icon: 'Wallet' },
      { path: '/demand', label: t('nav.demandForecast'), icon: 'TrendingUp' },
      { path: '/restocking', label: t('nav.restocking'), icon: 'RefreshCw' },
      { path: '/reports', label: t('nav.reports'), icon: 'FileBarChart' }
    ])

    return {
      t,
      isCollapsed,
      toggleCollapsed,
      companyInitial,
      navItems
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  height: 100vh;
  position: sticky;
  top: 0;
  z-index: 50;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 64px;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  min-height: 70px;
  overflow: hidden;
}

.brand-mark {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-accent-strong);
  color: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  white-space: nowrap;
}

.brand-text h1 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.75rem;
  color: var(--color-muted);
  font-weight: 400;
}

.sidebar.collapsed .brand-text {
  display: none;
}

.nav-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  color: var(--color-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--color-ink);
  background: var(--color-bg-alt);
}

.nav-link.active {
  color: var(--color-accent-strong);
  background: var(--color-accent-soft);
  border-left-color: var(--color-accent-strong);
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar.collapsed .nav-link {
  justify-content: center;
  padding: var(--space-3) 0;
}

.sidebar.collapsed .nav-label {
  display: none;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin: var(--space-3);
  padding: var(--space-2);
  background: var(--color-bg-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-toggle:hover {
  color: var(--color-ink);
  border-color: var(--color-border-strong);
}

/* Below tablet/narrow-laptop width, force icon-only mode to reclaim horizontal
   space for data tables, regardless of the manual collapse preference. The
   toggle button is hidden here since there's nothing left to toggle. */
@media (max-width: 1024px) {
  .sidebar {
    width: 64px;
  }

  .sidebar .brand-text,
  .sidebar .nav-label {
    display: none;
  }

  .sidebar .nav-link {
    justify-content: center;
    padding: var(--space-3) 0;
  }

  .collapse-toggle {
    display: none;
  }
}
</style>
