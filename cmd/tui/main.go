package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"time"

	"charm.land/bubbles/v2/spinner"
	"charm.land/bubbles/v2/textarea"
	"charm.land/bubbles/v2/viewport"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/glamour"
)

const (
	targetContentWidth = 80
	minContentWidth    = 40
)

var (
	thinkingPhrases = []string{
		"Inspecting metrics...",
		"Analyzing database records...",
		"Synthesizing response...",
	}

	userBubble = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.ANSIColor(4)).
			Padding(0, 1)

	userLabel = lipgloss.NewStyle().
			Bold(true)

	viewportStyle = lipgloss.NewStyle().Padding(1, 2)
	textareaStyle = lipgloss.NewStyle().Border(lipgloss.NormalBorder()).BorderForeground(lipgloss.ANSIColor(12)).Padding(1, 2)

	thinkingStyle = lipgloss.NewStyle().
			Italic(true).
			Foreground(lipgloss.ANSIColor(8))

	BrailleWave = spinner.Spinner{
		Frames: []string{"⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"},
		FPS:    time.Second / 12,
	}
)

type model struct {
	viewport       viewport.Model
	textarea       textarea.Model
	history        []string
	terminalWidth  int
	terminalHeight int
	renderer       *glamour.TermRenderer
	renderer_style []byte

	cmd     *exec.Cmd
	stdin   io.WriteCloser
	scanner *bufio.Scanner

	spinner     spinner.Model
	loadingText string
	loadingStep int
	isLoading   bool
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

type (
	responseMsg  string
	cycleTextMsg struct{}
)

func cycleTextCmd() tea.Cmd {
	return tea.Tick(time.Second*2, func(t time.Time) tea.Msg {
		return cycleTextMsg{}
	})
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func (m *model) updateViewportHeight() {
	if m.terminalHeight == 0 {
		return
	}
	_, vpFrameY := viewportStyle.GetFrameSize()
	_, taFrameY := textareaStyle.GetFrameSize()

	joinGap := 1
	available := m.terminalHeight - vpFrameY - (taFrameY + m.textarea.Height()) - joinGap
	m.viewport.SetHeight(max(1, available))
}

func (m *model) updateDimensionsWidth() {
	if m.terminalWidth == 0 {
		return
	}

	vpFrameX, _ := viewportStyle.GetFrameSize()
	taFrameX, _ := textareaStyle.GetFrameSize()

	var containerWidth int
	if m.terminalWidth >= targetContentWidth {
		containerWidth = targetContentWidth
	} else {
		containerWidth = max(minContentWidth, m.terminalWidth)
	}

	targetVpWidth := max(1, containerWidth-vpFrameX)
	m.viewport.SetWidth(targetVpWidth)
	m.textarea.SetWidth(max(1, containerWidth-taFrameX))

	m.renderer, _ = glamour.NewTermRenderer(
		glamour.WithStylesFromJSONBytes(m.renderer_style),
		glamour.WithWordWrap(max(10, targetVpWidth-4)),
	)

	m.viewport.SetContent(renderHistory(targetVpWidth, m.history, m.renderer, m.isLoading, m.spinner.View(), m.loadingText))
}

func renderHistory(width int, history []string, renderer *glamour.TermRenderer, isLoading bool, spView string, spText string) string {
	maxBubbleWidth := max(30, int(float64(width)*0.75))
	lines := make([]string, 0, len(history)+1)

	for _, msg := range history {
		if strings.HasPrefix(msg, "You: ") {
			text := strings.TrimPrefix(msg, "You: ")
			bubbleText := userLabel.Render("You:") + "\n" + text
			userText := userBubble.Width(maxBubbleWidth).Render(bubbleText)

			rightAlignedStyle := lipgloss.NewStyle().Width(width).Align(lipgloss.Right)
			lines = append(lines, rightAlignedStyle.Render(userText))
		} else {
			out, err := renderer.Render(msg)
			if err != nil {
				out = msg
			}
			lines = append(lines, strings.TrimSpace(out))
		}
	}

	if isLoading {
		indicator := fmt.Sprintf("%s %s", spView, thinkingStyle.Render(spText))
		lines = append(lines, indicator)
	}

	return strings.Join(lines, "\n\n")
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
		spCmd tea.Cmd
	)

	if !m.isLoading {
		prevTaHeight := m.textarea.Height()
		m.textarea, taCmd = m.textarea.Update(msg)
		if m.textarea.Height() != prevTaHeight {
			m.updateViewportHeight()
		}
	}
	m.viewport, vpCmd = m.viewport.Update(msg)

	switch msg := msg.(type) {
	case spinner.TickMsg:
		if m.isLoading {
			m.spinner, spCmd = m.spinner.Update(msg)
			m.viewport.SetContent(renderHistory(m.viewport.Width(), m.history, m.renderer, m.isLoading, m.spinner.View(), m.loadingText))
			return m, spCmd
		}

	case cycleTextMsg:
		if m.isLoading {
			m.loadingStep = (m.loadingStep + 1) % len(thinkingPhrases)
			m.loadingText = thinkingPhrases[m.loadingStep]
			m.viewport.SetContent(renderHistory(m.viewport.Width(), m.history, m.renderer, m.isLoading, m.spinner.View(), m.loadingText))
			return m, cycleTextCmd()
		}

	case tea.WindowSizeMsg:
		m.terminalHeight = msg.Height
		m.terminalWidth = msg.Width
		m.updateDimensionsWidth()
		m.updateViewportHeight()
		m.viewport.GotoBottom()

	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			input := strings.TrimSpace(m.textarea.Value())
			if input == "" || m.isLoading {
				return m, nil
			}

			m.isLoading = true
			m.loadingStep = 0
			m.loadingText = thinkingPhrases[0]
			m.textarea.Blur()
			m.history = append(m.history, "You: "+input)
			m.viewport.SetContent(renderHistory(m.viewport.Width(), m.history, m.renderer, m.isLoading, m.spinner.View(), m.loadingText))
			m.viewport.GotoBottom()
			m.textarea.Reset()
			m.updateViewportHeight()

			return m, tea.Batch(
				sendPrompt(m.stdin, m.scanner, input),
				m.spinner.Tick,
				cycleTextCmd(),
			)

		case "ctrl+c", "esc":
			if m.cmd != nil && m.cmd.Process != nil {
				_ = m.cmd.Process.Kill()
			}
			return m, tea.Quit
		}

	case responseMsg:
		m.isLoading = false
		m.textarea.Focus()
		m.history = append(m.history, string(msg))
		m.viewport.SetContent(renderHistory(m.viewport.Width(), m.history, m.renderer, m.isLoading, m.spinner.View(), m.loadingText))
		m.viewport.GotoBottom()
		return m, nil
	}

	return m, tea.Batch(taCmd, vpCmd)
}

func (m model) View() tea.View {
	content := lipgloss.JoinVertical(lipgloss.Top,
		viewportStyle.Render(m.viewport.View()),
		textareaStyle.Render(m.textarea.View()),
	)

	centered := lipgloss.PlaceHorizontal(
		m.terminalWidth,
		lipgloss.Center,
		content,
	)

	v := tea.NewView(centered)
	v.AltScreen = true
	return v
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
	ta.DynamicHeight = true
	ta.MinHeight = 1
	ta.MaxHeight = 8
	ta.MaxContentHeight = 15
	ta.Focus()

	vp := viewport.New(viewport.WithWidth(50), viewport.WithHeight(10))

	ansiGlamourStyle, err := os.ReadFile("cmd/tui/ansiGlamourStyle.json")
	if err != nil {
		panic(fmt.Sprintf("Glamour style sheet not found."))
	}

	r, _ := glamour.NewTermRenderer(
		glamour.WithStylesFromJSONBytes(ansiGlamourStyle),
		glamour.WithWordWrap(80),
	)

	s := spinner.New()
	s.Spinner = BrailleWave
	s.Style = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.ANSIColor(14))

	return model{
		viewport:       vp,
		textarea:       ta,
		history:        []string{},
		cmd:            cmd,
		stdin:          stdin,
		scanner:        bufio.NewScanner(stdout),
		renderer:       r,
		renderer_style: ansiGlamourStyle,
		spinner:        s,
		loadingText:    thinkingPhrases[0],
	}
}

func main() {

	p := tea.NewProgram(NewModel())
	if _, err := p.Run(); err != nil {
		panic(err)
	}
}
