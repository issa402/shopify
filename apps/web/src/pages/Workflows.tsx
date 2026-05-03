import {
  Page, Layout, Card, Button, Text, Badge,
  BlockStack, InlineStack, InlineGrid, Select, TextField, Divider, Box,
} from '@shopify/polaris'
import { useState } from 'react'

interface WorkflowRule {
  id: string
  name: string
  trigger: string
  condition: string
  action: string
  status: 'active' | 'paused'
  runs: number
}

const sampleRules: WorkflowRule[] = [
  {
    id: 'wf_001',
    name: 'VIP Order Alert',
    trigger: 'order.created',
    condition: 'order.total > 500 AND customer.ltv_segment == "vip"',
    action: 'slack.notify(#vip-orders) + support.assign_priority(high)',
    status: 'active',
    runs: 47,
  },
  {
    id: 'wf_002',
    name: 'Low Inventory Alert',
    trigger: 'inventory.below_reorder_point',
    condition: 'inventory.available < reorder_point',
    action: 'logistics_agent.draft_purchase_order() + slack.notify(#ops)',
    status: 'active',
    runs: 12,
  },
  {
    id: 'wf_003',
    name: 'Refund Win-Back',
    trigger: 'refund.processed',
    condition: 'customer.orders_count > 2',
    action: 'marketing.send_winback_email(discount=10%)',
    status: 'paused',
    runs: 88,
  },
]

export default function Workflows() {
  const [rules, setRules] = useState(sampleRules)
  const [showBuilder, setShowBuilder] = useState(false)
  // Form state makes the workflow builder functional instead of a static demo.
  const [draftName, setDraftName] = useState('')
  // The selected trigger maps to Shopify/webhook-style event names.
  const [draftTrigger, setDraftTrigger] = useState('order.created')
  // Conditions are optional because some automations should fire on every event.
  const [draftCondition, setDraftCondition] = useState('')
  // The action field captures the agent/tool call the workflow should perform.
  const [draftAction, setDraftAction] = useState('')

  const toggleStatus = (id: string) => {
    setRules(r => r.map(rule =>
      rule.id === id
        ? { ...rule, status: rule.status === 'active' ? 'paused' : 'active' }
        : rule
    ))
  }

  const saveWorkflow = () => {
    // Trimmed values prevent blank-looking workflows from being saved.
    const name = draftName.trim()
    // A workflow needs a name and action to be useful to a merchant.
    const action = draftAction.trim()

    if (!name || !action) {
      // Keeping the builder open makes the missing fields obvious without extra UI state.
      return
    }

    setRules(currentRules => [
      // New workflows appear first because the merchant just created them.
      {
        id: `wf_${Date.now()}`,
        name,
        trigger: draftTrigger,
        condition: draftCondition.trim() || 'always',
        action,
        status: 'active',
        runs: 0,
      },
      ...currentRules,
    ])
    // Resetting the draft makes the next workflow start clean.
    setDraftName('')
    setDraftTrigger('order.created')
    setDraftCondition('')
    setDraftAction('')
    setShowBuilder(false)
  }

  return (
    <Page
      title="Workflow Automator"
      subtitle="Build If-This-Then-That rules that connect your entire business"
      primaryAction={{ content: '+ New Workflow', onAction: () => setShowBuilder(true) }}
    >
      <Layout>
        {rules.map(rule => (
          <Layout.Section key={rule.id}>
            <Card>
              <BlockStack gap="300">
                <InlineStack align="space-between" blockAlign="center">
                  <InlineStack gap="200" blockAlign="center">
                    <Badge tone={rule.status === 'active' ? 'success' : undefined}>
                      {rule.status === 'active' ? '● Active' : '○ Paused'}
                    </Badge>
                    <Text variant="headingMd" as="h2">{rule.name}</Text>
                  </InlineStack>
                  <InlineStack gap="200">
                    <Text variant="bodySm" tone="subdued" as="span">{rule.runs} runs</Text>
                    <Button
                      variant="plain"
                      size="slim"
                      onClick={() => toggleStatus(rule.id)}
                    >
                      {rule.status === 'active' ? 'Pause' : 'Activate'}
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
                    <Text variant="bodySm" as="p"
                      tone="subdued">{rule.condition}
                    </Text>
                  </Box>
                  <Box>
                    <Text variant="bodySm" tone="subdued" as="p">ACTIONS</Text>
                    <Text variant="bodySm" as="p">{rule.action}</Text>
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
