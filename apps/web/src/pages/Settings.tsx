import {
  Page, Layout, Card, Checkbox, Text, Badge,
  BlockStack, TextField, InlineStack, Divider,
  Banner, Spinner, Box,
} from '@shopify/polaris'
import { useEffect, useState } from 'react'
import { apiGet } from '../api'

interface HealthResponse {
  status: string
  service: string
  version: string
  shopify_api_version: string
}

interface DashboardResponse {
  setup_required: boolean
  merchant: null | { id: string; shop_domain: string }
}

export default function Settings() {
  const [humanLoopEnabled, setHumanLoopEnabled] = useState(true)
  const [threshold, setThreshold] = useState('100')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [merchant, setMerchant] = useState<DashboardResponse['merchant']>(null)
  const [setupRequired, setSetupRequired] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch('/health').then(res => res.json()),
      apiGet<DashboardResponse>('/dashboard'),
    ])
      .then(([healthData, dashboard]) => {
        setHealth(healthData)
        setMerchant(dashboard.merchant)
        setSetupRequired(dashboard.setup_required)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Settings load failed'))
  }, [])

  return (
    <Page title="Settings & Connectors">
      <Layout>
        {error && <Layout.Section><Banner tone="critical"><Text as="p">{error}</Text></Banner></Layout.Section>}

        <Layout.AnnotatedSection
          title="Runtime Status"
          description="Live gateway and Shopify installation state."
        >
          <Card>
            {!health ? (
              <Box padding="400"><Spinner accessibilityLabel="Loading runtime status" /></Box>
            ) : (
              <BlockStack gap="300">
                <InlineStack align="space-between">
                  <Text as="p" variant="bodyMd">Gateway</Text>
                  <Badge tone={health.status === 'healthy' ? 'success' : 'critical'}>{health.status}</Badge>
                </InlineStack>
                <InlineStack align="space-between">
                  <Text as="p" variant="bodyMd">Service Version</Text>
                  <Text as="p" variant="bodySm" tone="subdued">{health.version}</Text>
                </InlineStack>
                <InlineStack align="space-between">
                  <Text as="p" variant="bodyMd">Shopify API Version</Text>
                  <Text as="p" variant="bodySm" tone="subdued">{health.shopify_api_version}</Text>
                </InlineStack>
              </BlockStack>
            )}
          </Card>
        </Layout.AnnotatedSection>

        <Layout.AnnotatedSection
          title="Shopify Integration"
          description="The merchant row created by Shopify OAuth."
        >
          <Card>
            <BlockStack gap="300">
              <InlineStack align="space-between">
                <Text as="p" variant="bodyMd">Shop Domain</Text>
                <Badge tone={merchant ? 'success' : 'attention'}>{merchant ? 'Installed' : 'Not Installed'}</Badge>
              </InlineStack>
              <Text variant="bodySm" tone="subdued" as="p">
                {merchant?.shop_domain || 'No merchant exists in Postgres yet.'}
              </Text>
              {setupRequired && (
                <Banner tone="warning">
                  <Text as="p">Run the Shopify OAuth flow before expecting live orders, customers, webhooks, or AI decisions.</Text>
                </Banner>
              )}
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>

        <Layout.AnnotatedSection
          title="Human-in-the-Loop Safety"
          description="Local UI setting for approval thresholds. Enforcement lives in agent tools and approval_queue."
        >
          <Card>
            <BlockStack gap="400">
              <Checkbox
                label="Require approval for AI actions above the threshold"
                checked={humanLoopEnabled}
                onChange={setHumanLoopEnabled}
              />
              <TextField
                label="Approval threshold (USD)"
                type="number"
                value={threshold}
                onChange={setThreshold}
                prefix="$"
                autoComplete="off"
                helpText="Agent tools currently queue large actions in Postgres for review."
              />
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>

        <Layout.AnnotatedSection
          title="AI Model Keys"
          description="Keys are read from environment variables, not from this browser form."
        >
          <Card>
            <BlockStack gap="400">
              <TextField label="ANTHROPIC_API_KEY" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Set this in .env or container environment." />
              <TextField label="OPENAI_API_KEY" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Set this in .env or container environment." />
              <Divider />
              <Text as="p" tone="subdued">Ollama is configured through OLLAMA_BASE_URL for local model calls.</Text>
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>
      </Layout>
    </Page>
  )
}
