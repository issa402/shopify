import {
  Page, Layout, Card, DataTable, Badge, Text,
  BlockStack, InlineGrid, Box,
} from '@shopify/polaris'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Demo revenue data keeps the dashboard useful before live Shopify data is connected.
const revenueData = [
  { day: 'Mon', revenue: 4200, ai_actions: 23 },
  { day: 'Tue', revenue: 5800, ai_actions: 31 },
  { day: 'Wed', revenue: 4900, ai_actions: 28 },
  { day: 'Thu', revenue: 7200, ai_actions: 45 },
  { day: 'Fri', revenue: 8100, ai_actions: 52 },
  { day: 'Sat', revenue: 9400, ai_actions: 61 },
  { day: 'Sun', revenue: 6300, ai_actions: 38 },
]

const recentOrders = [
  ['#10234', 'Alice Johnson', '$240.00', <Badge tone="success">Fulfilled</Badge>],
  ['#10233', 'Bob Chen', '$89.00', <Badge tone="attention">Pending</Badge>],
  ['#10232', 'Maria Garcia', '$520.00', <Badge tone="success">Fulfilled</Badge>],
  ['#10231', 'James Lee', '$145.00', <Badge tone="critical">Refunded by AI</Badge>],
]

const agentStats = [
  { name: 'Support Agent', status: 'Active', resolutions: 18, cost: '$0.89' },
  { name: 'Logistics Agent', status: 'Active', resolutions: 7, cost: '$0.34' },
  { name: 'Finance Agent', status: 'Idle', resolutions: 4, cost: '$0.21' },
]

export default function Dashboard() {
  return (
    <Page title="NexusOS Dashboard" subtitle="Your autonomous commerce operating system">
      {/* KPI Row */}
      <Layout>
        <Layout.Section>
          <InlineGrid columns={4} gap="400">
            <KPICard title="Today's Revenue" value="$9,400" change="+18%" positive />
            <KPICard title="AI Actions Today" value="61" change="vs 38 avg" positive />
            <KPICard title="Pending Approvals" value="2" change="Requires action" positive={false} />
            <KPICard title="LLM Cost Today" value="$1.44" change="-71% vs baseline" positive />
          </InlineGrid>
        </Layout.Section>

        {/* Revenue Chart */}
        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text as="h2" variant="headingMd">Revenue & AI Actions (Last 7 Days)</Text>
            <div style={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={revenueData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
                    name === 'revenue' ? `$${v.toLocaleString()}` : v, name
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
          {/* InlineGrid replaces the removed Layout.Section oneHalf prop in current Polaris. */}
          <InlineGrid columns={{ xs: 1, md: 2 }} gap="400">
            <Card>
              <BlockStack gap="400">
                <Text as="h2" variant="headingMd">Recent Orders</Text>
                <DataTable
                  columnContentTypes={['text', 'text', 'numeric', 'text']}
                  headings={['Order', 'Customer', 'Total', 'Status']}
                  rows={recentOrders}
                />
              </BlockStack>
            </Card>

            <Card>
              <BlockStack gap="300">
                <Text as="h2" variant="headingMd">Agent Swarm Status</Text>
                {agentStats.map(agent => (
                  <Box key={agent.name} padding="300" background="bg-surface-secondary" borderRadius="200">
                    <InlineGrid columns="1fr auto auto auto" gap="300" alignItems="center">
                      <Text variant="bodyMd" fontWeight="semibold" as="span">{agent.name}</Text>
                      <Badge tone={agent.status === 'Active' ? 'success' : undefined}>{agent.status}</Badge>
                      <Text variant="bodySm" tone="subdued" as="span">{agent.resolutions} resolved</Text>
                      <Text variant="bodySm" as="span">{agent.cost}</Text>
                    </InlineGrid>
                  </Box>
                ))}
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
