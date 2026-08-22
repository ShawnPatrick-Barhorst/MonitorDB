package main

import (
	"bufio"
	"encoding/json"
	"io"
	"os/exec"
	"strings"

	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type model struct {
	viewport      viewport.Model
	textarea      textarea.Model
	history       []string
	terminalWidth int

	cmd     *exec.Cmd
	stdin   io.WriteCloser
	scanner *bufio.Scanner

	isLoading bool
}

type promptPayload struct {
	Prompt            string  `json:"prompt"`
	SessionID         string  `json:"session_id"`
	SystemInstruction string  `json:"system_instruction,omitempty"`
	Temperature       float64 `json:"temperature,omitempty"`
	MaxOutputTokens   int     `json:"max_output_tokens,omitempty"`
	ThinkingLevel     string  `json:"thinking_level,omitempty"`
}

type responsePayload struct {
	Type        string `json:"type"`
	ContentType string `json:"content_type"`
	Content     string `json:"content"`
}

type responseMsg string

var (
	viewportStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(1, 2)
	textareaStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(1, 2)
)

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func renderHistory(width int, history []string) string {
	historyStyle := lipgloss.NewStyle().Width(width)

	lines := make([]string, 0, len(history))
	for _, msg := range history {
		lines = append(lines, msg)
	}

	return historyStyle.Render(strings.Join(lines, "\n"))
}

func sendPrompt(stdin io.Writer, scanner *bufio.Scanner, text string) tea.Cmd {
	return func() tea.Msg {
		data, _ := json.Marshal(promptPayload{Prompt: text, SessionID: "default"})
		_, _ = stdin.Write(append(data, '\n'))

		if scanner.Scan() {
			var resp responsePayload
			_ = json.Unmarshal(scanner.Bytes(), &resp)
			return responseMsg(resp.Content)
		}
		return responseMsg("[No response from engine]")
	}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {

	var (
		taCmd tea.Cmd
		vpCmd tea.Cmd
	)

	if !m.isLoading {
		m.textarea, taCmd = m.textarea.Update(msg)
	}
	m.viewport, vpCmd = m.viewport.Update(msg)

	switch msg := msg.(type) {

	case tea.WindowSizeMsg:
		vpFrameX, vpFrameY := viewportStyle.GetFrameSize() // x = left+right, y = top+bottom
		taFrameX, taFrameY := textareaStyle.GetFrameSize() // x = left+right, y = top+bottom

		// Inner widths (content area)

		m.viewport.Width = max(1, msg.Width-vpFrameX)
		m.textarea.SetWidth(max(1, msg.Width-taFrameX))

		// One row between viewport and textarea due to JoinVertical/newline
		joinGap := 1

		// Available inner height for viewport content
		available := msg.Height - vpFrameY - (taFrameY + m.textarea.Height()) - joinGap
		m.viewport.Height = max(1, available)

	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			input := strings.TrimSpace(m.textarea.Value())
			if input == "" {
				return m, nil
			}
			m.isLoading = true
			m.textarea.Blur()
			m.history = append(m.history, "You: "+input)
			m.viewport.SetContent(renderHistory(m.viewport.Width, m.history))
			m.viewport.GotoBottom()
			m.textarea.Reset()

			return m, sendPrompt(m.stdin, m.scanner, input)

		case "ctrl+c", "esc":
			if m.cmd != nil && m.cmd.Process != nil {
				_ = m.cmd.Process.Kill()
			}
			return m, tea.Quit
		}

	case responseMsg:
		m.isLoading = false
		m.textarea.Focus()
		m.history = append(m.history, "Gemini: "+string(msg))
		m.viewport.SetContent(renderHistory(m.viewport.Width, m.history))
		m.viewport.GotoBottom()
		return m, nil
	}

	return m, tea.Batch(taCmd, vpCmd)
}

func (m model) View() string {

	return lipgloss.JoinVertical(lipgloss.Top,
		viewportStyle.Render(m.viewport.View()),
		textareaStyle.Render(m.textarea.View()),
	)
}

func (m model) Init() tea.Cmd {
	return nil
}

func NewModel() model {
	cmd := exec.Command("uv", "run", "python", "-u", "-m", "monitordb", "--json")
	stdin, _ := cmd.StdinPipe()
	stdout, _ := cmd.StdoutPipe()
	_ = cmd.Start()

	ta := textarea.New()
	ta.Focus()
	ta.CharLimit = 512
	ta.SetWidth(50)
	ta.SetHeight(5)

	vp := viewport.New(50, 10)

	history := []string{}

	return model{
		viewport: vp,
		textarea: ta,
		history:  history,
		cmd:      cmd,
		stdin:    stdin,
		scanner:  bufio.NewScanner(stdout),
	}
}

func main() {
	p := tea.NewProgram(NewModel())

	_, err := p.Run()
	if err != nil {
		panic(err)
	}
}
