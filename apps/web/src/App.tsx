import { Routes, Route, Navigate } from 'react-router-dom'
import { Frame, Navigation, TopBar, Icon } from '@shopify/polaris'
import {
  HomeMinor,
  ProductsMinor,
  OrdersMinor,
  CustomersMajor,
  AutomationMajor,
  ChecklistMajor,
  SettingsMajor,
  NoteMinor,
} from '@shopify/polaris-icons'
import { useState, useCallback } from 'react'
import Dashboard from './pages/Dashboard'
import AgentLogs from './pages/AgentLogs'
import Approvals from './pages/Approvals'
import Workflows from './pages/Workflows'
import Settings from './pages/Settings'

export default function App() {
  const [mobileNavActive, setMobileNavActive] = useState(false)
  const toggleMobileNav = useCallback(() => setMobileNavActive(v => !v), [])

  const topBarMarkup = (
    <TopBar
      showNavigationToggle
      onNavigationToggle={toggleMobileNav}
    />
  )

  const navigationMarkup = (
    <Navigation location="/">
      <Navigation.Section
        title="NexusOS"
        items={[
          { label: 'Dashboard', icon: HomeMinor, url: '/dashboard', exactMatch: true },
          { label: 'Agent Activity', icon: AutomationMajor, url: '/agents' },
          { label: 'Approvals', icon: ChecklistMajor, url: '/approvals', badge: '2' },
          { label: 'Workflows', icon: NoteMinor, url: '/workflows' },
        ]}
      />
      <Navigation.Section
        title="Data"
        items={[
          { label: 'Orders', icon: OrdersMinor, url: '/orders' },
          { label: 'Customers', icon: CustomersMajor, url: '/customers' },
          { label: 'Products', icon: ProductsMinor, url: '/products' },
        ]}
      />
      <Navigation.Section
        title="System"
        items={[
          { label: 'Settings & MCP', icon: SettingsMajor, url: '/settings' },
        ]}
      />
    </Navigation>
  )

  return (
    <Frame
      topBar={topBarMarkup}
      navigation={navigationMarkup}
      showMobileNavigation={mobileNavActive}
      onNavigationDismiss={toggleMobileNav}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/agents" element={<AgentLogs />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Frame>
  )
}
