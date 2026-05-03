import {
  Page, Layout, Card, Checkbox, Text, Badge,
  BlockStack, TextField, Button, InlineStack, Divider,
  Banner,
} from '@shopify/polaris'
import { useState } from 'react'

const shopifyApiVersion = '2026-04'

const mcpServers = [
  // PostgreSQL is connected first because agents need merchant data context.
  { id: 'postgres', name: 'PostgreSQL', description: 'Direct database access for agents', connected: true },
  // Filesystem access is useful for generated reports and local operational docs.
  { id: 'filesystem', name: 'File System', description: 'Local file read/write for agents', connected: true },
  // Slack starts disconnected until the merchant authorizes workspace access.
  { id: 'slack', name: 'Slack', description: 'Send messages, read channels', connected: false },
  // Google Drive starts disconnected until OAuth credentials are configured.
  { id: 'google-drive', name: 'Google Drive', description: 'Read/write docs and sheets', connected: false },
]

export default function Settings() {
  const [humanLoopEnabled, setHumanLoopEnabled] = useState(true)
  const [threshold, setThreshold] = useState('100')

  return (
    <Page title="Settings & MCP Connectors">
      <Layout>
        {/* MCP Connectors */}
        <Layout.AnnotatedSection
          title="MCP Server Connections"
          description="Connect NexusOS to external tools. Your AI agents can then access these tools without custom API code."
        >
          <Card>
            <BlockStack gap="400">
              {mcpServers.map(server => (
                <div key={server.id}>
                  <InlineStack align="space-between" blockAlign="center">
                    <InlineStack gap="300" blockAlign="center">
                      <BlockStack gap="050">
                        <Text variant="bodyMd" fontWeight="semibold" as="p">{server.name}</Text>
                        <Text variant="bodySm" tone="subdued" as="p">{server.description}</Text>
                      </BlockStack>
                    </InlineStack>
                    <InlineStack gap="200" blockAlign="center">
                      <Badge tone={server.connected ? 'success' : undefined}>
                        {server.connected ? 'Connected' : 'Not Connected'}
                      </Badge>
                      <Button size="slim" variant={server.connected ? 'plain' : 'secondary'}>
                        {server.connected ? 'Configure' : 'Connect'}
                      </Button>
                    </InlineStack>
                  </InlineStack>
                  <Divider />
                </div>
              ))}
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>

        {/* Human-in-the-Loop */}
        <Layout.AnnotatedSection
          title="Human-in-the-Loop Safety"
          description="Control which AI actions require your approval before execution."
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
                helpText="Any AI action costing more than this must be manually approved."
              />
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>

        {/* AI Model Keys */}
        <Layout.AnnotatedSection
          title="AI Model API Keys"
          description="Configure your LLM keys. Local Ollama runs without any key."
        >
          <Card>
            <BlockStack gap="400">
              <TextField label="Anthropic API Key (Claude)" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Used for standard tasks (drafting replies, analysis)" />
              <TextField label="OpenAI API Key (GPT-4o / o1)" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Used for complex reasoning tasks only" />
              <Banner tone="info">
                <Text as="p"><strong>Ollama (Llama3:8b)</strong> runs at http://localhost:11434 for local inference.</Text>
              </Banner>
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>

        {/* Shopify */}
        <Layout.AnnotatedSection
          title="Shopify Integration"
          description="Your Shopify store connection details."
        >
          <Card>
            <BlockStack gap="300">
              <InlineStack align="space-between">
                <Text as="p" variant="bodyMd">Shop Domain</Text>
                <Badge tone="success">Connected</Badge>
              </InlineStack>
              <Text variant="bodySm" tone="subdued" as="p">your-store.myshopify.com</Text>
              <Divider />
              <InlineStack align="space-between">
                <Text as="p" variant="bodyMd">Webhooks</Text>
                <Badge tone="success">12 Active</Badge>
              </InlineStack>
              <InlineStack align="space-between">
                <Text as="p" variant="bodyMd">GraphQL API Version</Text>
                <Text as="p" variant="bodySm" tone="subdued">{shopifyApiVersion}</Text>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.AnnotatedSection>
      </Layout>
    </Page>
  )
}
