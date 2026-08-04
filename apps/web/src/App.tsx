import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { Badge, BlockStack, Box, Button, InlineStack, Text } from '@shopify/polaris'
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./pages/Dashboard'))
// Lazy-loaded routes keep the first admin screen faster for merchants.
const AgentLogs = lazy(() => import('./pages/AgentLogs'))
// Approvals load only when needed because review workflows are not always active.
const Approvals = lazy(() => import('./pages/Approvals'))
// Workflow builder code is split away from the dashboard for a smaller first bundle.
const Workflows = lazy(() => import('./pages/Workflows'))
// Settings are split because connector forms are rarely the first merchant task.
const Settings = lazy(() => import('./pages/Settings'))

const navigationItems = [
  // Each item is route data for the custom shell, avoiding deprecated Polaris Frame/Navigation.
  { label: 'Dashboard', path: '/dashboard' },
  // Agent activity is kept one click away because auditability is core app value.
  { label: 'Agent Activity', path: '/agents' },
  // The badge value mirrors the seeded pending approvals shown in the approvals page.
  { label: 'Approvals', path: '/approvals', badge: '2' },
  // Workflows stay in primary nav because automation setup is a frequent merchant task.
  { label: 'Workflows', path: '/workflows' },
  // Settings includes MCP, model, and Shopify integration controls.
  { label: 'Settings', path: '/settings' },
]

export default function App() {
  // The current route drives active nav state without deprecated Polaris Navigation.
  const location = useLocation()
  // Programmatic navigation keeps buttons accessible while using React Router.
  const navigate = useNavigate()

  return (
    <Box background="bg-surface-secondary" minHeight="100vh">
      <Box background="bg-surface" borderBlockEndWidth="025" borderColor="border" padding="400">
        <InlineStack align="space-between" blockAlign="center" gap="400">
          <BlockStack gap="050">
            <InlineStack gap="200" blockAlign="center">
              <Text as="h1" variant="headingLg">NexusOS</Text>
              <Badge tone="success">Shopify API 2026-04</Badge>
            </InlineStack>
            <Text as="p" variant="bodySm" tone="subdued">
              Autonomous commerce controls for revenue, risk, agents, and approvals.
            </Text>
          </BlockStack>

          <InlineStack gap="200" blockAlign="center">
            {navigationItems.map(item => {
              // Prefix matching keeps nested routes highlighted if the app grows later.
              const isActive = location.pathname.startsWith(item.path)

              return (
                <Button
                  key={item.path}
                  pressed={isActive}
                  variant={isActive ? 'primary' : 'secondary'}
                  onClick={() => navigate(item.path)}
                >
                  {item.badge ? `${item.label} (${item.badge})` : item.label}
                </Button>
              )
            })}
          </InlineStack>
        </InlineStack>
      </Box>

      <Box paddingBlock="500">
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<AgentLogs />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </Box>
    </Box>
  )
}

function RouteFallback() {
  // The loading fallback is intentionally quiet so navigation feels native.
  return (
    <Box padding="500">
      <Text as="p" variant="bodyMd" tone="subdued">Loading...</Text>
    </Box>
  )
}
