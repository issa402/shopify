import {
  Page, Layout, LegacyCard, SettingToggle, Text, Badge,
  BlockStack, TextField, Button, InlineStack, Divider,
  CalloutCard, Banner,
} from '@shopify/polaris'
import { useState } from 'react'

const mcpServers = [
  { id: 'postgres', name: 'PostgreSQL', description: 'Direct database access for agents', icon: '🗄️', connected: true },
  { id: 'filesystem', name: 'File System', description: 'Local file read/write for agents', icon: '📁', connected: true },
  { id: 'slack', name: 'Slack', description: 'Send messages, read channels', icon: '💬', connected: false },
  { id: 'google-drive', name: 'Google Drive', description: 'Read/write docs and sheets', icon: '📊', connected: false },
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
          <LegacyCard sectioned>
            <BlockStack gap="400">
              {mcpServers.map(server => (
                <div key={server.id}>
                  <InlineStack align="space-between" blockAlign="center">
                    <InlineStack gap="300" blockAlign="center">
                      <Text as="span" variant="headingMd">{server.icon}</Text>
                      <BlockStack gap="050">
                        <Text variant="bodyMd" fontWeight="semibold" as="p">{server.name}</Text>
                        <Text variant="bodySm" tone="subdued" as="p">{server.description}</Text>
                      </BlockStack>
                    </InlineStack>
                    <InlineStack gap="200" blockAlign="center">
                      <Badge tone={server.connected ? 'success' : 'subdued'}>
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
          </LegacyCard>
        </Layout.AnnotatedSection>

        {/* Human-in-the-Loop */}
        <Layout.AnnotatedSection
          title="Human-in-the-Loop Safety"
          description="Control which AI actions require your approval before execution."
        >
          <LegacyCard sectioned>
            <BlockStack gap="400">
              <SettingToggle
                action={{
                  content: humanLoopEnabled ? 'Enabled' : 'Disabled',
                  onAction: () => setHumanLoopEnabled(v => !v),
                }}
                enabled={humanLoopEnabled}
              >
                <Text as="p" variant="bodyMd">
                  Require approval for AI actions above:
                </Text>
              </SettingToggle>
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
          </LegacyCard>
        </Layout.AnnotatedSection>

        {/* AI Model Keys */}
        <Layout.AnnotatedSection
          title="AI Model API Keys"
          description="Configure your LLM keys. Local Ollama runs without any key."
        >
          <LegacyCard sectioned>
            <BlockStack gap="400">
              <TextField label="Anthropic API Key (Claude)" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Used for standard tasks (drafting replies, analysis)" />
              <TextField label="OpenAI API Key (GPT-4o / o1)" type="password" value="" onChange={() => {}} autoComplete="off" helpText="Used for complex reasoning tasks only" />
              <Banner tone="info">
                <Text as="p">🟢 <strong>Ollama (Llama3:8b)</strong> running at http://localhost:11434 — free local inference for 72% of tasks.</Text>
              </Banner>
            </BlockStack>
          </LegacyCard>
        </Layout.AnnotatedSection>

        {/* Shopify */}
        <Layout.AnnotatedSection
          title="Shopify Integration"
          description="Your Shopify store connection details."
        >
          <LegacyCard sectioned>
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
                <Text as="p" variant="bodySm" tone="subdued">2026-01</Text>
              </InlineStack>
            </BlockStack>
          </LegacyCard>
        </Layout.AnnotatedSection>
      </Layout>
    </Page>
  )
}
