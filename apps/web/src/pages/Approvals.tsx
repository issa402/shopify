import {
  Page, Layout, Card, Button, Text, Badge,
  BlockStack, InlineGrid, Banner,
  InlineStack, Box, Divider, Spinner,
} from '@shopify/polaris'
import { useEffect, useState } from 'react'
import { apiGet, apiPost, formatMoney } from '../api'

interface PendingApproval {
  id: string
  agent: string
  action_type: string
  action_payload: Record<string, unknown>
  estimated_cost: number
  created_at: string
  status: string
}

interface ApprovalResponse {
  setup_required?: boolean
  pending?: PendingApproval[]
}

export default function Approvals() {
  const [pending, setPending] = useState<PendingApproval[]>([])
  const [setupRequired, setSetupRequired] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadApprovals = () => {
    setLoading(true)
    apiGet<ApprovalResponse>('/approvals/pending')
      .then(data => {
        setSetupRequired(Boolean(data.setup_required))
        setPending(data.pending || [])
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Approvals API failed'))
      .finally(() => setLoading(false))
  }

  useEffect(loadApprovals, [])

  const decide = async (id: string, action: 'approve' | 'reject') => {
    await apiPost(`/approvals/${id}/${action}`)
    setPending(current => current.filter(item => item.id !== id))
  }

  return (
    <Page title="Human-in-the-Loop Approvals" subtitle="AI actions that require review before execution">
      <Layout>
        {error && <Layout.Section><Banner tone="critical"><Text as="p">{error}</Text></Banner></Layout.Section>}
        {setupRequired && <Layout.Section><Banner tone="warning"><Text as="p">No Shopify merchant is installed yet, so the approval queue is not available.</Text></Banner></Layout.Section>}
        {loading && <Layout.Section><Box padding="500"><Spinner accessibilityLabel="Loading approvals" /></Box></Layout.Section>}

        {!loading && pending.length === 0 && (
          <Layout.Section>
            <Banner tone="success">
              <Text as="p">No pending approvals are currently stored in the database.</Text>
            </Banner>
          </Layout.Section>
        )}

        {pending.map(approval => (
          <Layout.Section key={approval.id}>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between" blockAlign="center">
                  <InlineStack gap="200" blockAlign="center">
                    <Badge tone={approval.estimated_cost >= 100 ? 'attention' : undefined}>
                      {approval.action_type}
                    </Badge>
                    <Text variant="headingMd" as="h2">{approval.agent}</Text>
                    <Text variant="bodySm" tone="subdued" as="span">
                      {new Date(approval.created_at).toLocaleString()}
                    </Text>
                  </InlineStack>
                  <Text variant="headingLg" fontWeight="bold" as="span">
                    {formatMoney(approval.estimated_cost)}
                  </Text>
                </InlineStack>

                <InlineGrid columns={3} gap="400">
                  {Object.entries(approval.action_payload || {}).map(([key, value]) => (
                    <Box key={key}>
                      <Text variant="bodySm" tone="subdued" as="p">{key.replace(/_/g, ' ').toUpperCase()}</Text>
                      <Text variant="bodySm" as="p">{String(value)}</Text>
                    </Box>
                  ))}
                </InlineGrid>

                <Divider />

                <InlineStack gap="300">
                  <Button variant="primary" tone="success" onClick={() => decide(approval.id, 'approve')}>
                    Approve and execute
                  </Button>
                  <Button variant="secondary" tone="critical" onClick={() => decide(approval.id, 'reject')}>
                    Reject
                  </Button>
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        ))}
      </Layout>
    </Page>
  )
}
