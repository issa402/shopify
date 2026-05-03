import {
  Page, Layout, Card, DataTable, Badge, Text,
  BlockStack, Tabs,
  InlineGrid,
} from '@shopify/polaris'
import { useState } from 'react'

const agentDecisions = [
  {
    id: 'dec_001',
    agent: 'SupportAgent',
    action: 'Issued refund of $45.00',
    order: '#10228',
    customer: 'Emily Walsh',
    model: 'claude-3-5-sonnet',
    cost: '$0.004',
    outcome: 'success',
    time: '2 min ago',
  },
  {
    id: 'dec_002',
    agent: 'LogisticsAgent',
    action: 'Drafted PO for Supplier XYZ - 200 units',
    order: 'N/A',
    customer: 'N/A',
    model: 'claude-3-5-sonnet',
    cost: '$0.006',
    outcome: 'pending_approval',
    time: '15 min ago',
  },
  {
    id: 'dec_003',
    agent: 'FinanceAgent',
    action: 'Rejected refund request - margin below 15%',
    order: '#10225',
    customer: 'David Park',
    model: 'claude-3-5-sonnet',
    cost: '$0.003',
    outcome: 'success',
    time: '32 min ago',
  },
  {
    id: 'dec_004',
    agent: 'SupportAgent',
    action: 'Classified ticket as URGENT',
    order: '#10224',
    customer: 'Sarah Kim',
    model: 'ollama:llama3:8b',
    cost: '$0.000',
    outcome: 'success',
    time: '1 hr ago',
  },
]

const outcomeBadge = (outcome: string) => {
  switch (outcome) {
    case 'success': return <Badge tone="success">Success</Badge>
    case 'pending_approval': return <Badge tone="attention">Pending Approval</Badge>
    case 'escalated': return <Badge tone="warning">Escalated</Badge>
    case 'failure': return <Badge tone="critical">Failed</Badge>
    default: return <Badge>{outcome}</Badge>
  }
}

const modelBadge = (model: string) => {
  if (model.includes('ollama')) return <Badge tone="success">Local</Badge>
  if (model.includes('claude')) return <Badge tone="info">Claude</Badge>
  return <Badge>GPT-4</Badge>
}

export default function AgentLogs() {
  const [selected, setSelected] = useState(0)

  const tabs = [
    { id: 'all', content: 'All Actions', panelID: 'all' },
    { id: 'support', content: 'Support Agent', panelID: 'support' },
    { id: 'logistics', content: 'Logistics Agent', panelID: 'logistics' },
    { id: 'finance', content: 'Finance Agent', panelID: 'finance' },
  ]

  const rows = agentDecisions.map(d => [
    d.time,
    d.agent,
    d.action,
    d.order,
    modelBadge(d.model),
    d.cost,
    outcomeBadge(d.outcome),
  ])

  return (
    <Page
      title="Agent Activity Log"
      subtitle="Every AI decision, fully auditable"
    >
      <Layout>
        {/* Stats row */}
        <Layout.Section>
          <InlineGrid columns={3} gap="400">
            <Card>
              <BlockStack gap="100">
                <Text variant="bodySm" tone="subdued" as="p">Total Actions Today</Text>
                <Text variant="headingXl" as="p">61</Text>
                <Text variant="bodySm" tone="success" as="p">↑ 60% above average</Text>
              </BlockStack>
            </Card>
            <Card>
              <BlockStack gap="100">
                <Text variant="bodySm" tone="subdued" as="p">Actions via Local AI (Free)</Text>
                <Text variant="headingXl" as="p">72%</Text>
                <Text variant="bodySm" tone="success" as="p">Saving ~$3.20 vs all-API</Text>
              </BlockStack>
            </Card>
            <Card>
              <BlockStack gap="100">
                <Text variant="bodySm" tone="subdued" as="p">Autonomous Resolution Rate</Text>
                <Text variant="headingXl" as="p">89%</Text>
                <Text variant="bodySm" tone="success" as="p">11% escalated to human</Text>
              </BlockStack>
            </Card>
          </InlineGrid>
        </Layout.Section>

        {/* Decision log */}
        <Layout.Section>
          <Card>
            <Tabs tabs={tabs} selected={selected} onSelect={setSelected} />
            <DataTable
              columnContentTypes={['text', 'text', 'text', 'text', 'text', 'numeric', 'text']}
              headings={['Time', 'Agent', 'Action Taken', 'Order', 'Model', 'Cost', 'Outcome']}
              rows={rows}
            />
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  )
}
