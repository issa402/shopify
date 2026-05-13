import {
  Page, Layout, Card, DataTable, Badge, Text,
  BlockStack, InlineGrid, Box, Banner, Spinner,
} from '@shopify/polaris'
import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { apiGet, formatMoney } from '../api'

interface DashboardResponse {
  setup_required: boolean
  merchant: null | { id: string; shop_domain: string }
  metrics: {
    revenue_today: number
    orders_today: number
    ai_actions_today: number
    pending_approvals: number
    llm_cost_today_usd: number
    autonomous_rate_pct: number
  }
  revenue_series: Array<{ day: string; revenue: number; ai_actions: number }>
  recent_orders: Array<{
    order_number: string
    customer_email: string
    total_price: number
    financial_status: string
    fulfillment_status: string
  }>
  agent_stats: Array<{ name: string; status: string; resolutions: number; cost_usd: number }>
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    apiGet<DashboardResponse>('/dashboard')
      .then(setData)
      .catch(err => setError(err instanceof Error ? err.message : 'Dashboard API failed'))
  }, [])

  if (error) {
    return <Page title="NexusOS Dashboard"><Banner tone="critical"><Text as="p">{error}</Text></Banner></Page>
  }

  if (!data) {
    return (
      <Page title="NexusOS Dashboard">
        <Box padding="500"><Spinner accessibilityLabel="Loading dashboard" /></Box>
      </Page>
    )
  }

  const recentOrders = data.recent_orders.map(order => [
    order.order_number,
    order.customer_email || 'Unknown customer',
    formatMoney(order.total_price),
    <Badge tone={order.financial_status === 'paid' ? 'success' : 'attention'}>
      {order.financial_status || order.fulfillment_status || 'Unknown'}
    </Badge>,
  ])

  return (
    <Page
      title="NexusOS Dashboard"
      subtitle={data.merchant ? data.merchant.shop_domain : 'Connect Shopify to start live commerce automation'}
    >
      <Layout>
        {data.setup_required && (
          <Layout.Section>
            <Banner tone="warning">
              <Text as="p">
                No installed Shopify merchant exists in the NexusOS database yet. The app is running, but live metrics stay at zero until OAuth/webhooks create merchant data.
              </Text>
            </Banner>
          </Layout.Section>
        )}

        <Layout.Section>
          <InlineGrid columns={4} gap="400">
            <KPICard title="Today's Revenue" value={formatMoney(data.metrics.revenue_today)} change={`${data.metrics.orders_today} orders`} positive />
            <KPICard title="AI Actions Today" value={String(data.metrics.ai_actions_today)} change={`${data.metrics.autonomous_rate_pct}% autonomous`} positive />
            <KPICard title="Pending Approvals" value={String(data.metrics.pending_approvals)} change="Requires review" positive={data.metrics.pending_approvals === 0} />
            <KPICard title="LLM Cost Today" value={formatMoney(data.metrics.llm_cost_today_usd)} change="From decision ledger" positive />
          </InlineGrid>
        </Layout.Section>

        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text as="h2" variant="headingMd">Revenue & AI Actions (Last 7 Days)</Text>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.revenue_series} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <defs>
                      <linearGradient id="revenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#008060" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#008060" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(v: number, name: string) => [
                      name === 'revenue' ? formatMoney(v) : v, name,
                    ]} />
                    <Area type="monotone" dataKey="revenue" stroke="#008060" fill="url(#revenue)" strokeWidth={2} />
                    <Area type="monotone" dataKey="ai_actions" stroke="#5c6ac4" fill="none" strokeWidth={1.5} strokeDasharray="4 2" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </BlockStack>
          </Card>
        </Layout.Section>

        <Layout.Section>
          <InlineGrid columns={{ xs: 1, md: 2 }} gap="400">
            <Card>
              <BlockStack gap="400">
                <Text as="h2" variant="headingMd">Recent Orders</Text>
                {recentOrders.length > 0 ? (
                  <DataTable
                    columnContentTypes={['text', 'text', 'numeric', 'text']}
                    headings={['Order', 'Customer', 'Total', 'Status']}
                    rows={recentOrders}
                  />
                ) : (
                  <Text as="p" tone="subdued">No Shopify orders have been ingested yet.</Text>
                )}
              </BlockStack>
            </Card>

            <Card>
              <BlockStack gap="300">
                <Text as="h2" variant="headingMd">Agent Swarm Status</Text>
                {data.agent_stats.length > 0 ? data.agent_stats.map(agent => (
                  <Box key={agent.name} padding="300" background="bg-surface-secondary" borderRadius="200">
                    <InlineGrid columns="1fr auto auto auto" gap="300" alignItems="center">
                      <Text variant="bodyMd" fontWeight="semibold" as="span">{agent.name}</Text>
                      <Badge tone={agent.status === 'Active' ? 'success' : undefined}>{agent.status}</Badge>
                      <Text variant="bodySm" tone="subdued" as="span">{agent.resolutions} decisions</Text>
                      <Text variant="bodySm" as="span">{formatMoney(agent.cost_usd)}</Text>
                    </InlineGrid>
                  </Box>
                )) : (
                  <Text as="p" tone="subdued">No AI decisions are recorded yet.</Text>
                )}
              </BlockStack>
            </Card>
          </InlineGrid>
        </Layout.Section>
      </Layout>
    </Page>
  )
}

function KPICard({ title, value, change, positive }: {
  title: string; value: string; change: string; positive: boolean
}) {
  return (
    <Card>
      <BlockStack gap="100">
        <Text variant="bodySm" tone="subdued" as="p">{title}</Text>
        <Text variant="heading2xl" fontWeight="bold" as="p">{value}</Text>
        <Text variant="bodySm" tone={positive ? 'success' : 'critical'} as="p">{change}</Text>
      </BlockStack>
    </Card>
  )
}
