// Package mcp implements the NexusOS MCP (Model Context Protocol) Host.
// NexusOS acts as an MCP Host, managing connections to multiple MCP servers
// (Slack, Google Drive, Postgres, etc.) so AI agents can access any tool
// without custom API wrappers.
package mcp

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
)

// Config represents the mcp-config.json structure.
type Config struct {
	Version    string                 `json:"version"`
	MCPServers map[string]ServerConfig `json:"mcpServers"`
	NexusOS    NexusOSConfig          `json:"nexusos"`
}

// ServerConfig defines an individual MCP server.
type ServerConfig struct {
	Command     string            `json:"command"`
	Args        []string          `json:"args"`
	Env         map[string]string `json:"env"`
	Description string            `json:"description"`
	Tools       []string          `json:"tools"`
}

// NexusOSConfig defines agent permissions per MCP server.
type NexusOSConfig struct {
	DefaultServers   []string            `json:"defaultServers"`
	OptionalServers  []string            `json:"optionalServers"`
	AgentPermissions map[string][]string `json:"agentPermissions"`
}

// Hub is the MCP Host — manages connections to all registered MCP servers.
type Hub struct {
	config      Config
	connections map[string]*ServerConnection
}

// ServerConnection represents a live connection to an MCP server.
type ServerConnection struct {
	Name   string
	Config ServerConfig
	Active bool
}

// ToolCall represents a request from an agent to a tool via MCP.
type ToolCall struct {
	Server string                 `json:"server"`
	Tool   string                 `json:"tool"`
	Args   map[string]interface{} `json:"args"`
}

// ToolResult is the response from an MCP tool.
type ToolResult struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data"`
	Error   string      `json:"error,omitempty"`
}

// NewHub creates and initializes the MCP Hub from a config file.
func NewHub(configPath string) (*Hub, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read MCP config: %w", err)
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse MCP config: %w", err)
	}

	hub := &Hub{
		config:      config,
		connections: make(map[string]*ServerConnection),
	}

	// Initialize default server connections
	for _, name := range config.NexusOS.DefaultServers {
		serverCfg, ok := config.MCPServers[name]
		if !ok {
			log.Printf("[mcp] Warning: server '%s' not found in config", name)
			continue
		}
		hub.connections[name] = &ServerConnection{
			Name:   name,
			Config: serverCfg,
			Active: true,
		}
		log.Printf("[mcp] Registered server: %s (%s)", name, serverCfg.Description)
	}

	log.Printf("[mcp] Hub initialized with %d server connections", len(hub.connections))
	return hub, nil
}

// Call dispatches a tool call to the specified MCP server.
// This is the core interface that AI agents use to access external tools.
func (h *Hub) Call(agentName, serverName, tool string, args map[string]interface{}) (*ToolResult, error) {
	// 1. Check agent permission
	if !h.agentCanAccess(agentName, serverName) {
		return nil, fmt.Errorf("[mcp] agent '%s' is not permitted to access server '%s'", agentName, serverName)
	}

	// 2. Check server connection
	conn, ok := h.connections[serverName]
	if !ok || !conn.Active {
		return nil, fmt.Errorf("[mcp] server '%s' is not connected", serverName)
	}

	// 3. Check tool is available
	if !h.serverHasTool(conn, tool) {
		return nil, fmt.Errorf("[mcp] tool '%s' not available on server '%s'", tool, serverName)
	}

	log.Printf("[mcp] %s → %s.%s(%v)", agentName, serverName, tool, args)

	// 4. Execute via stdio transport
	// In production: spawn/communicate with the MCP server process via JSON-RPC over stdio
	result, err := h.executeViaStdio(conn, tool, args)
	if err != nil {
		return &ToolResult{Success: false, Error: err.Error()}, nil
	}

	return result, nil
}

// ListAvailableTools returns all tools accessible to a given agent.
func (h *Hub) ListAvailableTools(agentName string) map[string][]string {
	allowedServers, ok := h.config.NexusOS.AgentPermissions[agentName]
	if !ok {
		allowedServers = h.config.NexusOS.DefaultServers
	}

	tools := make(map[string][]string)
	for _, serverName := range allowedServers {
		if conn, ok := h.connections[serverName]; ok {
			tools[serverName] = conn.Config.Tools
		}
	}
	return tools
}

// GetConnectedServers returns all currently active server connections.
func (h *Hub) GetConnectedServers() []string {
	var servers []string
	for name, conn := range h.connections {
		if conn.Active {
			servers = append(servers, name)
		}
	}
	return servers
}

// ─── Private helpers ──────────────────────────────────────────────────────────

func (h *Hub) agentCanAccess(agentName, serverName string) bool {
	permissions, ok := h.config.NexusOS.AgentPermissions[agentName]
	if !ok {
		// Default to allowing only default servers
		for _, s := range h.config.NexusOS.DefaultServers {
			if s == serverName {
				return true
			}
		}
		return false
	}
	for _, s := range permissions {
		if s == serverName {
			return true
		}
	}
	return false
}

func (h *Hub) serverHasTool(conn *ServerConnection, tool string) bool {
	for _, t := range conn.Config.Tools {
		if t == tool {
			return true
		}
	}
	return false
}

// executeViaStdio communicates with an MCP server via JSON-RPC 2.0 over stdio.
// This is the standard MCP transport mechanism.
func (h *Hub) executeViaStdio(_ *ServerConnection, tool string, args map[string]interface{}) (*ToolResult, error) {
	// In production: use exec.Command to spawn or reuse the MCP server process,
	// then send JSON-RPC 2.0 messages and read responses via stdin/stdout.
	// Reference: https://spec.modelcontextprotocol.io/specification/transport/stdio/

	// Stub response for development
	log.Printf("[mcp] [stub] Executing tool=%s args=%v", tool, args)
	return &ToolResult{
		Success: true,
		Data: map[string]interface{}{
			"tool":    tool,
			"args":    args,
			"result":  "stub_response",
			"note":    "Wire real MCP stdio transport in production",
		},
	}, nil
}
