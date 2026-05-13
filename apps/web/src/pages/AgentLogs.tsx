import {
  Page, Layout, Card, DataTable, Badge, Text,
  BlockStack, Tabs, InlineGrid, Banner, Spinner, Box,
} from '@shopify/polaris'
import { useEffect, useMemo, useState } from 'react'
import { apiGet, formatMoney } from '../api'

interface Decision {
  id: string
  agent: string
  task_type: string
  model: string
  cost_usd: number
  outcome: string
  created_at: string
}

interface DecisionResponse {
  setup_required?: boolean
  decisions?: Decision[]
}

const outcomeBadge = (outcome: string) => {
  switch (outcome) {
    case 'success': return <Badge tone="success">Success</Badge>
    case 'pending_approval': return <Badge tone="attention">Pending Approval</Badge>
    case 'escalated': return <Badge tone="warning">Escalated</Badge>
    case 'failure': return <Badge tone="critical">Failed</Badge>
    default: return <Badge>{outcome || 'Unknown'}</Badge>
  }
}

const modelBadge = (model: string) => {
  if (model.includes('ollama')) return <Badge tone="success">Local</Badge>
  if (model.includes('claude')) return <Badge tone="info">Claude</Badge>
  if (model.includes('gpt') || model.includes('o1')) return <Badge>OpenAI</Badge>
  return <Badge>{model || 'Unknown'}</Badge>
}

export default function AgentLogs() {
  const [selected, setSelected] = useState(0)
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [setupRequired, setSetupRequired] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiGet<DecisionResponse>('/ai/decisions')
      .then(data => {
        setSetupRequired(Boolean(data.setup_required))
        setDecisions(data.decisions || [])
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Decision API failed'))
      .finally(() => setLoading(false))
  }, [])

  const tabs = [
    { id: 'all', content: 'All Actions', panelID: 'all' },
    { id: 'support', content: 'Support Agent', panelID: 'support' },
    { id: 'logistics', content: 'Logistics Agent', panelID: 'logistics' },
    { id: 'finance', content: 'Finance Agent', panelID: 'finance' },
  ]

  const filtered = useMemo(() => {
    const agent = tabs[selected]?.content.replace(' Agent', '')
    if (selected === 0) return decisions
    return decisions.filter(d => d.agent.toLowerCase().includes(agent.toLowerCase()))
  }, [decisions, selected])

  const rows = filtered.map(d => [
    new Date(d.created_at).toLocaleString(),
    d.agent,
    d.task_type,
    modelBadge(d.model),
    formatMoney(d.cost_usd),
    outcomeBadge(d.outcome),
  ])

  const localActions = decisions.filter(d => d.model.includes('ollama')).length
  const successCount = decisions.filter(d => d.outcome === 'success').length

  return (
    <Page title="Agent Activity Log" subtitle="Every recorded AI decision from the database">
      <Layout>
        {error && <Layout.Section><Banner tone="critical"><Text as="p">{error}</Text></Banner></Layout.Section>}
        {setupRequired && <Layout.Section><Banner tone="warning"><Text as="p">No Shopify merchant is installed yet, so there is no decision ledger to display.</Text></Banner></Layout.Section>}
        {loading && <Layout.Section><Box padding="500"><Spinner accessibilityLabel="Loading decisions" /></Box></Layout.Section>}

        {!loading && (
          <>
            <Layout.Section>
              <InlineGrid columns={3} gap="400">
                <Card><BlockStack gap="100"><Text variant="bodySm" tone="subdued" as="p">Total Actions</Text><Text variant="headingXl" as="p">{decisions.length}</Text></BlockStack></Card>
                <Card><BlockStack gap="100"><Text variant="bodySm" tone="subdued" as="p">Actions via Local AI</Text><Text variant="headingXl" as="p">{localActions}</Text></BlockStack></Card>
                <Card><BlockStack gap="100"><Text variant="bodySm" tone="subdued" as="p">Successful Decisions</Text><Text variant="headingXl" as="p">{successCount}</Text></BlockStack></Card>
              </InlineGrid>
            </Layout.Section>

            <Layout.Section>
              <Card>
                <Tabs tabs={tabs} selected={selected} onSelect={setSelected} />
                {rows.length > 0 ? (
                  <DataTable
                    columnContentTypes={['text', 'text', 'text', 'text', 'numeric', 'text']}
                    headings={['Time', 'Agent', 'Task', 'Model', 'Cost', 'Outcome']}
                    rows={rows}
                  />
                ) : (
                  <Box padding="400"><Text as="p" tone="subdued">No AI decisions match this view yet.</Text></Box>
                )}
              </Card>
            </Layout.Section>
          </>
        )}
      </Layout>
    </Page>
  )
}
