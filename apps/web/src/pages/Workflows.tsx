import {
  Page, Layout, Card, Button, Text, Badge,
  BlockStack, InlineStack, InlineGrid, Select, TextField, Divider, Box, Banner, Spinner,
} from '@shopify/polaris'
import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api'

interface WorkflowRule {
  id: string
  name: string
  description: string
  trigger: string
  conditions: Array<{ expression?: string }> | null
  actions: Array<{ command?: string }> | null
  active: boolean
  run_count: number
}

interface WorkflowResponse {
  setup_required?: boolean
  workflows?: WorkflowRule[]
}

export default function Workflows() {
  const [rules, setRules] = useState<WorkflowRule[]>([])
  const [showBuilder, setShowBuilder] = useState(false)
  const [draftName, setDraftName] = useState('')
  const [draftTrigger, setDraftTrigger] = useState('order.created')
  const [draftCondition, setDraftCondition] = useState('')
  const [draftAction, setDraftAction] = useState('')
  const [setupRequired, setSetupRequired] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadWorkflows = () => {
    setLoading(true)
    apiGet<WorkflowResponse>('/workflows')
      .then(data => {
        setSetupRequired(Boolean(data.setup_required))
        setRules(data.workflows || [])
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Workflow API failed'))
      .finally(() => setLoading(false))
  }

  useEffect(loadWorkflows, [])

  const toggleStatus = async (id: string) => {
    await apiPost<{ active: boolean }>(`/workflows/${id}/toggle`)
    loadWorkflows()
  }

  const saveWorkflow = async () => {
    const name = draftName.trim()
    const action = draftAction.trim()
    if (!name || !action) return

    await apiPost('/workflows', {
      name,
      trigger: draftTrigger,
      condition: draftCondition.trim() || 'always',
      action,
    })
    setDraftName('')
    setDraftTrigger('order.created')
    setDraftCondition('')
    setDraftAction('')
    setShowBuilder(false)
    loadWorkflows()
  }

  return (
    <Page
      title="Workflow Automator"
      subtitle="Database-backed automation rules"
      primaryAction={{ content: '+ New Workflow', onAction: () => setShowBuilder(true), disabled: setupRequired }}
    >
      <Layout>
        {error && <Layout.Section><Banner tone="critical"><Text as="p">{error}</Text></Banner></Layout.Section>}
        {setupRequired && <Layout.Section><Banner tone="warning"><Text as="p">Install a Shopify merchant before creating workflow rules.</Text></Banner></Layout.Section>}
        {loading && <Layout.Section><Box padding="500"><Spinner accessibilityLabel="Loading workflows" /></Box></Layout.Section>}

        {!loading && rules.length === 0 && !showBuilder && (
          <Layout.Section>
            <Card>
              <Text as="p" tone="subdued">No workflow rules are stored yet.</Text>
            </Card>
          </Layout.Section>
        )}

        {rules.map(rule => (
          <Layout.Section key={rule.id}>
            <Card>
              <BlockStack gap="300">
                <InlineStack align="space-between" blockAlign="center">
                  <InlineStack gap="200" blockAlign="center">
                    <Badge tone={rule.active ? 'success' : undefined}>
                      {rule.active ? 'Active' : 'Paused'}
                    </Badge>
                    <Text variant="headingMd" as="h2">{rule.name}</Text>
                  </InlineStack>
                  <InlineStack gap="200">
                    <Text variant="bodySm" tone="subdued" as="span">{rule.run_count} runs</Text>
                    <Button variant="plain" size="slim" onClick={() => toggleStatus(rule.id)}>
                      {rule.active ? 'Pause' : 'Activate'}
                    </Button>
                  </InlineStack>
                </InlineStack>

                <Divider />

                <InlineGrid columns={3} gap="400">
                  <Box>
                    <Text variant="bodySm" tone="subdued" as="p">TRIGGER</Text>
                    <Text variant="bodyMd" fontWeight="semibold" as="p">{rule.trigger}</Text>
                  </Box>
                  <Box>
                    <Text variant="bodySm" tone="subdued" as="p">CONDITION</Text>
                    <Text variant="bodySm" as="p" tone="subdued">{rule.conditions?.[0]?.expression || 'always'}</Text>
                  </Box>
                  <Box>
                    <Text variant="bodySm" tone="subdued" as="p">ACTION</Text>
                    <Text variant="bodySm" as="p">{rule.actions?.[0]?.command || 'No action configured'}</Text>
                  </Box>
                </InlineGrid>
              </BlockStack>
            </Card>
          </Layout.Section>
        ))}

        {showBuilder && (
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <Text as="h2" variant="headingMd">New Workflow</Text>
                <TextField label="Workflow Name" autoComplete="off" value={draftName} onChange={setDraftName} />
                <Select
                  label="Trigger Event"
                  options={[
                    { label: 'Order Created', value: 'order.created' },
                    { label: 'Inventory Below Reorder', value: 'inventory.low' },
                    { label: 'Refund Processed', value: 'refund.processed' },
                    { label: 'Support Ticket Opened', value: 'ticket.created' },
                    { label: 'Customer Churned', value: 'customer.churn_risk' },
                  ]}
                  value={draftTrigger}
                  onChange={setDraftTrigger}
                />
                <TextField label="Condition (optional)" autoComplete="off" value={draftCondition} onChange={setDraftCondition} placeholder="order.total > 500" />
                <TextField label="Action" autoComplete="off" value={draftAction} onChange={setDraftAction} placeholder="slack.notify(#ops)" />
                <InlineStack gap="200">
                  <Button variant="primary" onClick={saveWorkflow}>Save Workflow</Button>
                  <Button variant="plain" onClick={() => setShowBuilder(false)}>Cancel</Button>
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        )}
      </Layout>
    </Page>
  )
}
