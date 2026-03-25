import {
  Page, Layout, LegacyCard, Button, Text, Badge,
  BlockStack, InlineGrid, Banner, CalloutCard,
  InlineStack, Box, Divider,
} from '@shopify/polaris'
import { useState } from 'react'

interface PendingApproval {
  id: string
  agent: string
  action_type: string
  description: string
  estimated_cost: number
  created_at: string
  risk_level: 'low' | 'medium' | 'high'
  details: Record<string, string>
}

const pendingApprovals: PendingApproval[] = [
  {
    id: 'appr_001',
    agent: 'LogisticsAgent',
    action_type: 'purchase_order',
    description: 'Create Purchase Order: 200 units of SKU-XYZ-001 from SupplierCo at $8.50/unit',
    estimated_cost: 1700.00,
    created_at: '2026-03-11T22:30:00Z',
    risk_level: 'medium',
    details: {
      supplier: 'SupplierCo International',
      sku: 'XYZ-001',
      quantity: '200 units',
      unit_cost: '$8.50',
      total: '$1,700.00',
      reason: 'Stock at 45 units, reorder point is 50. Stockout predicted in 6 days.',
      lead_time: '14 days',
    },
  },
  {
    id: 'appr_002',
    agent: 'SupportAgent',
    action_type: 'refund',
    description: 'Issue refund of $235.00 for Order #10219 (customer claims item never arrived)',
    estimated_cost: 235.00,
    created_at: '2026-03-11T22:45:00Z',
    risk_level: 'medium',
    details: {
      customer: 'Robert Johnson',
      order: '#10219',
      amount: '$235.00',
      reason: 'Item not received. Carrier shows "delivered" but customer disputes.',
      margin_impact: 'Reduces order margin from 32% to 0%. Finance Agent flagged for review.',
      recommendation: 'Issue partial store credit of $117.50 instead of full refund.',
    },
  },
]

export default function Approvals() {
  const [approved, setApproved] = useState<string[]>([])
  const [rejected, setRejected] = useState<string[]>([])

  const pending = pendingApprovals.filter(a => !approved.includes(a.id) && !rejected.includes(a.id))

  return (
    <Page
      title="Human-in-the-Loop Approvals"
      subtitle="AI actions above $100 or with high risk require your review"
    >
      <Layout>
        {pending.length === 0 && (
          <Layout.Section>
            <Banner tone="success">
              <Text as="p">✅ All caught up! No pending approvals.</Text>
            </Banner>
          </Layout.Section>
        )}

        {pending.map(approval => (
          <Layout.Section key={approval.id}>
            <LegacyCard sectioned>
              <BlockStack gap="400">
                {/* Header */}
                <InlineStack align="space-between" blockAlign="center">
                  <InlineStack gap="200" blockAlign="center">
                    <Badge tone={approval.risk_level === 'high' ? 'critical' : 'attention'}>
                      {approval.risk_level.toUpperCase()} RISK
                    </Badge>
                    <Text variant="headingMd" as="h2">{approval.agent}</Text>
                    <Text variant="bodySm" tone="subdued" as="span">
                      {new Date(approval.created_at).toLocaleTimeString()}
                    </Text>
                  </InlineStack>
                  <Text variant="headingLg" fontWeight="bold" as="span">
                    ${approval.estimated_cost.toFixed(2)}
                  </Text>
                </InlineStack>

                <Text variant="bodyMd" as="p">{approval.description}</Text>

                <Divider />

                {/* Details */}
                <InlineGrid columns={3} gap="400">
                  {Object.entries(approval.details).map(([key, value]) => (
                    <Box key={key}>
                      <Text variant="bodySm" tone="subdued" as="p">{key.replace(/_/g, ' ').toUpperCase()}</Text>
                      <Text variant="bodySm" as="p">{value}</Text>
                    </Box>
                  ))}
                </InlineGrid>

                <Divider />

                {/* Actions */}
                <InlineStack gap="300">
                  <Button
                    variant="primary"
                    tone="success"
                    onClick={() => setApproved(prev => [...prev, approval.id])}
                  >
                    ✅ Approve — Execute Now
                  </Button>
                  <Button
                    variant="secondary"
                    tone="critical"
                    onClick={() => setRejected(prev => [...prev, approval.id])}
                  >
                    ❌ Reject
                  </Button>
                  <Button variant="plain">View Full AI Reasoning</Button>
                </InlineStack>
              </BlockStack>
            </LegacyCard>
          </Layout.Section>
        ))}

        {/* Resolved section */}
        {(approved.length > 0 || rejected.length > 0) && (
          <Layout.Section>
            <LegacyCard title="Resolved" sectioned>
              <BlockStack gap="200">
                {approved.map(id => (
                  <Text key={id} tone="success" as="p">✅ {id} — Approved and executed</Text>
                ))}
                {rejected.map(id => (
                  <Text key={id} tone="critical" as="p">❌ {id} — Rejected</Text>
                ))}
              </BlockStack>
            </LegacyCard>
          </Layout.Section>
        )}
      </Layout>
    </Page>
  )
}
