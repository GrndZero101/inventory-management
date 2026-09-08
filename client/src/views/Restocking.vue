<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            min="0"
            max="20000"
            step="100"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendationRows.length }})</h3>
        </div>

        <div v-if="recommendationRows.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <template v-else>
          <div class="budget-summary">
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.budgetUsed') }}</span>
              <span class="summary-value">{{ currencySymbol }}{{ budgetUsed.toLocaleString() }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.budgetRemaining') }}</span>
              <span class="summary-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}</span>
            </div>
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th>{{ t('restocking.table.demandGap') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.suggestedQty') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in recommendationRows" :key="row.item_sku">
                  <td><input type="checkbox" v-model="row.selected" /></td>
                  <td><strong>{{ row.item_sku }}</strong></td>
                  <td>{{ row.item_name }}</td>
                  <td>
                    <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                  </td>
                  <td>{{ row.demand_gap }}</td>
                  <td>{{ currencySymbol }}{{ row.unit_cost.toFixed(2) }}</td>
                  <td>{{ row.suggested_qty }}</td>
                  <td>{{ currencySymbol }}{{ row.line_total.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="place-order-bar">
            <button
              class="btn-place-order"
              :disabled="selectedRows.length === 0 || submitting"
              @click="placeOrder"
            >
              {{ t('restocking.placeOrder') }}
            </button>
            <div v-if="confirmationMessage" class="confirmation-message">
              {{ confirmationMessage }}
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(5000)
    const submitting = ref(false)
    const confirmationMessage = ref('')
    const recommendationRows = ref([])
    let confirmationTimer = null

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const computeRecommendations = () => {
      const candidates = forecasts.value
        .map(f => ({ ...f, demand_gap: f.forecasted_demand - f.current_demand }))
        .filter(f => f.demand_gap > 0)

      candidates.sort((a, b) => {
        const aIncreasing = a.trend === 'increasing'
        const bIncreasing = b.trend === 'increasing'
        if (aIncreasing !== bIncreasing) return aIncreasing ? -1 : 1
        return b.demand_gap - a.demand_gap
      })

      const rows = []
      let remainingBudget = budget.value

      for (const item of candidates) {
        const maxAffordableQty = Math.floor(remainingBudget / item.unit_cost)
        const suggestedQty = Math.min(item.demand_gap, maxAffordableQty)

        // Keep scanning even after a skip/partial fill so a later cheaper item
        // can still make use of any leftover budget.
        if (suggestedQty > 0) {
          const lineTotal = suggestedQty * item.unit_cost
          rows.push({
            item_sku: item.item_sku,
            item_name: item.item_name,
            trend: item.trend,
            demand_gap: item.demand_gap,
            unit_cost: item.unit_cost,
            suggested_qty: suggestedQty,
            line_total: lineTotal,
            selected: true
          })
          remainingBudget -= lineTotal
        }
      }

      return rows
    }

    const refreshRecommendations = () => {
      const freshRows = computeRecommendations()
      const previousSelection = new Map(recommendationRows.value.map(r => [r.item_sku, r.selected]))
      recommendationRows.value = freshRows.map(row => ({
        ...row,
        selected: previousSelection.has(row.item_sku) ? previousSelection.get(row.item_sku) : true
      }))
    }

    watch(budget, refreshRecommendations)
    watch(forecasts, refreshRecommendations)

    const selectedRows = computed(() => recommendationRows.value.filter(r => r.selected))

    const budgetUsed = computed(() => {
      return selectedRows.value.reduce((sum, r) => sum + r.line_total, 0)
    })

    const budgetRemaining = computed(() => budget.value - budgetUsed.value)

    const placeOrder = async () => {
      if (selectedRows.value.length === 0) return
      submitting.value = true
      try {
        const payload = {
          items: selectedRows.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.suggested_qty,
            unit_cost: r.unit_cost,
            line_total: r.line_total
          })),
          budget: budget.value
        }
        await api.createRestockOrder(payload)
        confirmationMessage.value = t('restocking.orderSubmitted')
        if (confirmationTimer) clearTimeout(confirmationTimer)
        confirmationTimer = setTimeout(() => {
          confirmationMessage.value = ''
        }, 4000)
        await loadForecasts()
        refreshRecommendations()
      } catch (err) {
        error.value = 'Failed to submit restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(async () => {
      await loadForecasts()
      refreshRecommendations()
    })

    return {
      t,
      loading,
      error,
      budget,
      currencySymbol,
      recommendationRows,
      selectedRows,
      budgetUsed,
      budgetRemaining,
      submitting,
      confirmationMessage,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-controls {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  /* track height/radius kept as literals: 3px is intentionally half of the 6px
     track height (fully-rounded pill), not a match for the radius scale */
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
}

.budget-readout {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
  min-width: 100px;
  text-align: right;
}

.empty-state {
  padding: var(--space-7);
  text-align: center;
  color: var(--color-muted);
  font-size: 0.938rem;
}

.budget-summary {
  display: flex;
  gap: var(--space-7);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-bg-alt);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
}

.place-order-bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-5);
}

.btn-place-order {
  background: var(--color-accent);
  color: var(--color-surface);
  border: none;
  padding: 0.625rem var(--space-6);
  border-radius: var(--radius-md);
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-place-order:hover:not(:disabled) {
  background: var(--color-accent-strong);
}

.btn-place-order:disabled {
  background: var(--color-border-strong);
  cursor: not-allowed;
}

.confirmation-message {
  color: #059669;
  font-weight: 600;
  font-size: 0.938rem;
}
</style>
